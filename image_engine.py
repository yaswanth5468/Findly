from transformers import CLIPProcessor, CLIPModel
import torch
import os


model = CLIPModel.from_pretrained(
    "openai/clip-vit-base-patch32"
)

processor = CLIPProcessor.from_pretrained(
    "openai/clip-vit-base-patch32"
)


image_data = torch.load(
    "clip_images_new.pt",
    weights_only=False
)


def search_images(query, folders=None):

    inputs = processor(
        text=[query],
        return_tensors="pt",
        padding=True
    )

    with torch.no_grad():

        text_output = model.text_model(
            **inputs
        )

        text_embedding = text_output.pooler_output

        text_embedding = model.text_projection(
            text_embedding
        )

        text_embedding = (
            text_embedding
            / text_embedding.norm(
                dim=-1,
                keepdim=True
            )
        )

    results = []

    for path, image_embedding in image_data:

        if folders:

            allowed = False

            for folder in folders:

                folder = os.path.abspath(
                    folder
                )

                image_path = os.path.abspath(
                    path
                )

                if (
                    image_path == folder
                    or image_path.startswith(
                        folder + os.sep
                    )
                ):

                    allowed = True
                    break

            if not allowed:
                continue

        if not os.path.exists(path):
            continue

        image_embedding = torch.tensor(
            image_embedding
        )

        score = torch.dot(
            text_embedding[0],
            image_embedding
        ).item()

        results.append(
            (
                path,
                score
            )
        )

    results.sort(
        key=lambda x: x[1],
        reverse=True
    )

    return results