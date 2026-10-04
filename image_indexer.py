from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import os
import torch


MODEL_NAME = "openai/clip-vit-base-patch32"

INDEX_PATH = "clip_images_new.pt"

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp"
}


print("Loading CLIP model...")

model = CLIPModel.from_pretrained(
    MODEL_NAME
)

processor = CLIPProcessor.from_pretrained(
    MODEL_NAME
)

print("CLIP model loaded.")


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

        return torch.load(
            INDEX_PATH,
            weights_only=False
        )

    except Exception as e:

        print(
            "Could not load image index:",
            e
        )

        return []


def save_image_index(image_data):

    torch.save(
        image_data,
        INDEX_PATH
    )


def is_supported_image(path):

    extension = os.path.splitext(
        path
    )[1].lower()

    return extension in SUPPORTED_EXTENSIONS


def index_image_folder(folder):

    image_data = load_image_index()

    existing_paths = {
        os.path.abspath(path)
        for path, embedding in image_data
    }

    new_count = 0

    for root, folders, files in os.walk(folder):

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

            if absolute_path in existing_paths:
                continue

            print(
                "Analyzing new image:",
                path
            )

            embedding = get_image_embedding(
                path
            )

            if embedding is not None:

                image_data.append(
                    (
                        path,
                        embedding
                    )
                )

                existing_paths.add(
                    absolute_path
                )

                new_count += 1

    save_image_index(
        image_data
    )

    print(
        "New images indexed:",
        new_count
    )

    print(
        "Total images in index:",
        len(image_data)
    )


def update_image(path):

    if not os.path.exists(path):
        return

    if not is_supported_image(path):
        return

    image_data = load_image_index()

    absolute_path = os.path.abspath(
        path
    )

    image_data = [
        (
            saved_path,
            embedding
        )
        for saved_path, embedding in image_data
        if os.path.abspath(saved_path) != absolute_path
    ]

    print(
        "Updating image:",
        path
    )

    embedding = get_image_embedding(
        path
    )

    if embedding is not None:

        image_data.append(
            (
                path,
                embedding
            )
        )

    save_image_index(
        image_data
    )


def remove_image(path):

    image_data = load_image_index()

    absolute_path = os.path.abspath(
        path
    )

    new_data = [
        (
            saved_path,
            embedding
        )
        for saved_path, embedding in image_data
        if os.path.abspath(saved_path) != absolute_path
    ]

    if len(new_data) != len(image_data):

        print(
            "Removed image from index:",
            path
        )

        save_image_index(
            new_data
        )


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