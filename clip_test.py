from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import torch

model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

path = r"D:\my photos\051A6452.JPG"

img = Image.open(path).convert("RGB")

query = input("What are you looking for? ")

inputs = processor(
    text=[query],
    images=img,
    return_tensors="pt",
    padding=True
)

outputs = model(**inputs)

score = outputs.logits_per_image[0][0]

print("\nMatch score:", round(score.item(), 2))