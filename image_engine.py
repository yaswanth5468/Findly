
from transformers import CLIPProcessor, CLIPModel

import torch
import os


# ============================================================
# MODEL
# ============================================================

MODEL_NAME = "openai/clip-vit-base-patch32"
MIN_IMAGE_SIMILARITY = 0.20


print(
    "Loading CLIP model..."
)


model = CLIPModel.from_pretrained(
    MODEL_NAME
)


processor = CLIPProcessor.from_pretrained(
    MODEL_NAME
)


print(
    "CLIP model loaded."
)


# ============================================================
# IMAGE INDEX
# ============================================================

INDEX_PATH = "clip_images_new.pt"


# ============================================================
# LOAD IMAGE INDEX
# ============================================================

def load_image_index():

    if not os.path.exists(
        INDEX_PATH
    ):

        print(
            "Image index does not exist."
        )

        return []

    try:

        image_data = torch.load(
            INDEX_PATH,
            weights_only=False
        )

        print(
            "Image index loaded:",
            len(image_data),
            "images"
        )

        return image_data

    except Exception as error:

        print(
            "Could not load image index:",
            error
        )

        return []


# ============================================================
# CHECK WHETHER IMAGE BELONGS TO SELECTED FOLDER
# ============================================================

def is_inside_folder(image_path, folder):

    try:
        image_path = os.path.normcase(
            os.path.abspath(image_path)
        )

        folder = os.path.normcase(
            os.path.abspath(folder)
        )

        return os.path.commonpath(
            [image_path, folder]
        ) == folder

    except ValueError:
        return False

def search_images(
    query,
    folders=None
):

    print(
        "\nImage search query:",
        query
    )


    # --------------------------------------------------------
    # IMPORTANT:
    # Reload the latest index every search
    # --------------------------------------------------------

    image_data = load_image_index()


    if not image_data:

        print(
            "No images are currently indexed."
        )

        return []


    # --------------------------------------------------------
    # Create text embedding
    # --------------------------------------------------------

    inputs = processor(
        text=[query],
        return_tensors="pt",
        padding=True
    )


    with torch.no_grad():

        text_output = model.text_model(
            **inputs
        )

        text_embedding = (
            text_output.pooler_output
        )

        text_embedding = (
            model.text_projection(
                text_embedding
            )
        )

        text_embedding = (
            text_embedding
            /
            text_embedding.norm(
                dim=-1,
                keepdim=True
            )
        )


    # --------------------------------------------------------
    # Search every indexed image
    # --------------------------------------------------------

    results = []
    candidate_count = 0


    for path, image_embedding in image_data:

        # ----------------------------------------------------
        # Ignore deleted files
        # ----------------------------------------------------

        if not os.path.exists(
            path
        ):

            continue


        # ----------------------------------------------------
        # Restrict search to selected folders
        # ----------------------------------------------------

        if folders:

            allowed = False

            for folder in folders:

                if is_inside_folder(
                    path,
                    folder
                ):

                    allowed = True

                    break


            if not allowed:

                continue

        candidate_count += 1


        # ----------------------------------------------------
        # Convert stored embedding
        # ----------------------------------------------------

        image_embedding = torch.tensor(
            image_embedding
        )


        # ----------------------------------------------------
        # Calculate similarity
        # ----------------------------------------------------

        score = torch.dot(
            text_embedding[0],
            image_embedding
        ).item()


        if score >= MIN_IMAGE_SIMILARITY:
            results.append(
                (
                    path,
                    score
                )
            )


    # --------------------------------------------------------
    # Highest similarity first
    # --------------------------------------------------------

    results.sort(
        key=lambda x: x[1],
        reverse=True
    )


    print(
        "Indexed images checked:",
        candidate_count
    )

    print(
        "Images matching similarity threshold:",
        len(results)
    )

    return results