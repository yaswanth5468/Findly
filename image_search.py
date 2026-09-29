from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import os
import torch

model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

folder = input("Enter photo folder path: ")
query = input("What are you looking for? ")

results = []

for root, folders, files in os.walk(folder):

    for file in files:

        if file.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):

            path = os.path.join(root, file)

            print("Checking:", file)

            try:
                img = Image.open(path).convert("RGB")

                inputs = processor(
                    text=[query],
                    images=img,
                    return_tensors="pt",
                    padding=True
                )

                outputs = model(**inputs)

                score = outputs.logits_per_image[0][0].item()

                results.append((path, score))

            except Exception as e:
                print("Skipped:", file)

results.sort(key=lambda x: x[1], reverse=True)

print("\nBest matches:\n")

for path, score in results[:10]:

    print(round(score, 2), "-", path)