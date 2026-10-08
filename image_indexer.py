from PIL import Image
import os
import tempfile
import threading
import torch

from image_engine import INDEX_PATH, model, processor

_IMAGE_INDEX_LOCK = threading.RLock()

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
    ".tif",
    ".tiff"
}


def get_image_embedding(path):

    try:

        image = Image.open(path).convert("RGB")

        inputs = processor(
            images=image,
            return_tensors="pt"
        )

        with torch.no_grad():

            vision_output = model.vision_model(
                **inputs
            )

            embedding = vision_output.pooler_output

            embedding = model.visual_projection(
                embedding
            )

            embedding = embedding / embedding.norm(
                dim=-1,
                keepdim=True
            )

        return embedding[0].tolist()

    except Exception as e:

        print(
            "Failed to process:",
            path,
            e
        )

        return None


def load_image_index():

    if not os.path.exists(INDEX_PATH):

        return []

    try:
        image_data = torch.load(
            INDEX_PATH,
            weights_only=False
        )
        if not isinstance(image_data, list):
            raise ValueError("Image index must contain a list.")
        if any(
            not isinstance(entry, (tuple, list))
            or len(entry) < 2
            or not isinstance(entry[0], str)
            for entry in image_data
        ):
            raise ValueError("Image index contains an invalid entry.")
        return image_data

    except Exception as e:

        print(
            "Could not load image index:",
            e
        )

        return None


def save_image_index(image_data):
    directory = os.path.dirname(os.path.abspath(INDEX_PATH))
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=directory,
            suffix=".pt",
            delete=False,
        ) as index_file:
            temporary_path = index_file.name
        torch.save(image_data, temporary_path)
        os.replace(temporary_path, INDEX_PATH)
    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.remove(temporary_path)


def is_supported_image(path):

    extension = os.path.splitext(
        path
    )[1].lower()

    return extension in SUPPORTED_EXTENSIONS


def index_image_folder(folder):
    with _IMAGE_INDEX_LOCK:
        return _index_image_folder(folder)


def _index_image_folder(folder):

    image_data = load_image_index()
    if image_data is None:
        raise RuntimeError(
            "The saved photo index could not be loaded. Findly left it "
            "unchanged; restore or remove the damaged index before "
            "rebuilding."
        )
    image_paths = []
    walk_errors = []

    existing_entries = {}
    for entry in image_data:
        if isinstance(entry, (tuple, list)) and len(entry) >= 2:
            existing_entries[
                os.path.normcase(os.path.abspath(entry[0]))
            ] = entry

    new_count = 0
    person_scanned = 0
    people_detected = 0

    def on_walk_error(error):
        walk_errors.append(error)

    for root, folders, files in os.walk(folder, onerror=on_walk_error):

        folders[:] = [
            folder_name
            for folder_name in folders
            if folder_name != ".venv"
        ]

        for file in files:

            path = os.path.join(
                root,
                file
            )

            if not is_supported_image(path):
                continue

            absolute_path = os.path.abspath(
                path
            )
            image_paths.append((path, absolute_path))

    if image_paths:
        from person_detector import (
            PERSON_DETECTION_THRESHOLD,
            index_person_image,
            initialize_person_detector,
        )

        initialize_person_detector()

    current_paths = {
        os.path.normcase(os.path.abspath(absolute_path))
        for _path, absolute_path in image_paths
    }
    updated_entries = []

    for path, absolute_path in image_paths:

        normalized_path = os.path.normcase(absolute_path)
        old_entry = existing_entries.get(normalized_path)
        try:
            stat = os.stat(path)
        except OSError as error:
            print("Could not inspect image:", path, error)
            if old_entry is not None:
                updated_entries.append(old_entry)
            continue

        changed = (
            old_entry is None
            or len(old_entry) < 4
            or old_entry[2] != stat.st_mtime_ns
            or old_entry[3] != stat.st_size
        )

        if changed:
            print(
                "Analyzing image:",
                path
            )

            embedding = get_image_embedding(path)
            if embedding is not None:
                updated_entries.append(
                    (path, embedding, stat.st_mtime_ns, stat.st_size)
                )
                if old_entry is None:
                    new_count += 1
            elif old_entry is not None:
                updated_entries.append(old_entry)
        else:
            updated_entries.append(old_entry)

        try:
            person_confidence = index_person_image(path, force=changed)
            if person_confidence is not None:
                person_scanned += 1
                if person_confidence >= PERSON_DETECTION_THRESHOLD:
                    people_detected += 1
                    print(
                        "Person detected:",
                        path,
                        round(person_confidence, 3)
                    )
        except (OSError, ValueError) as error:
            print(
                "Could not analyze image for people:",
                path,
                error
            )

    if not walk_errors:
        folder_path = os.path.normcase(os.path.abspath(folder))
        for existing_path, entry in existing_entries.items():
            try:
                inside_folder = (
                    os.path.commonpath([existing_path, folder_path])
                    == folder_path
                )
            except ValueError:
                updated_entries.append(entry)
                continue

            if not inside_folder:
                updated_entries.append(entry)

        image_data = updated_entries

        from person_detector import prune_person_images

        prune_person_images(folder, current_paths)
    else:
        print(
            "Image index cleanup skipped because some folders could not "
            "be scanned:",
            walk_errors
        )
        updated_paths = {
            os.path.normcase(os.path.abspath(entry[0]))
            for entry in updated_entries
        }
        image_data = updated_entries + [
            entry
            for path, entry in existing_entries.items()
            if path not in updated_paths
        ]

    save_image_index(image_data)

    print(
        "New images indexed:",
        new_count
    )

    print(
        "Total images in index:",
        len(image_data)
    )
    print(
        "Photos checked for people:",
        person_scanned,
        "| photos with person detections:",
        people_detected
    )

    return new_count


def update_image(path):
    with _IMAGE_INDEX_LOCK:
        return _update_image(path)


def _update_image(path):
    if not os.path.exists(path):
        return

    if not is_supported_image(path):
        return

    image_data = load_image_index()
    if image_data is None:
        print("Image update skipped because the saved index is unreadable.")
        return

    absolute_path = os.path.abspath(
        path
    )

    image_data = [
        entry
        for entry in image_data
        if (
            isinstance(entry, (tuple, list))
            and len(entry) >= 2
            and os.path.abspath(entry[0]) != absolute_path
        )
    ]

    print(
        "Updating image:",
        path
    )

    try:
        stat = os.stat(path)
    except OSError as error:
        print("Could not inspect changed image:", path, error)
        return

    embedding = get_image_embedding(path)

    if embedding is not None:

        image_data.append(
            (
                path,
                embedding,
                stat.st_mtime_ns,
                stat.st_size,
            )
        )

    save_image_index(
        image_data
    )

    from person_detector import index_person_image

    try:
        index_person_image(path, force=True)
    except OSError as error:
        print(
            "Could not refresh person detection for image:",
            path,
            error
        )


def remove_image(path):
    with _IMAGE_INDEX_LOCK:
        return _remove_image(path)


def _remove_image(path):

    image_data = load_image_index()
    if image_data is None:
        print("Image removal skipped because the saved index is unreadable.")
        return

    absolute_path = os.path.abspath(
        path
    )

    new_data = [
        entry
        for entry in image_data
        if (
            not isinstance(entry, (tuple, list))
            or len(entry) < 2
            or os.path.abspath(entry[0]) != absolute_path
        )
    ]

    if len(new_data) != len(image_data):

        print(
            "Removed image from index:",
            path
        )

        save_image_index(
            new_data
        )

    from person_detector import remove_person_image

    remove_person_image(path)


if __name__ == "__main__":

    folder = input(
        "Enter image folder: "
    )

    if os.path.isdir(folder):

        index_image_folder(
            folder
        )

    else:

        print(
            "Invalid folder."
        )