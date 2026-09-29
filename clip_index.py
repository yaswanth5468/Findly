from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import os
import torch

model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

folder = input("Enter photo folder path: ")

image_data = []

for root, folders, files in os.walk(folder):

    for file in files:

        if file.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):

            path = os.path.join(root, file)

            print("Analyzing:", file)

            try:
                img = Image.open(path).convert("RGB")

                inputs = processor(
                    images=img,
                    return_tensors="pt"
                )

                with torch.no_grad():
                    vision_output = model.vision_model(**inputs)

                    embedding = vision_output.pooler_output

                    embedding = model.visual_projection(embedding)

                    embedding = embedding / embedding.norm(
                        dim=-1,
                        keepdim=True
                    )

                image_data.append(
                    (path, embedding[0].tolist())
                )

            except Exception as e:

                print("Skipped:", file, e)

torch.save(image_data, "clip_images.pt")

print("\nImage indexing completed!")
print("Images indexed:", len(image_data))