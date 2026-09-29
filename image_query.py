from transformers import CLIPProcessor, CLIPModel
import torch

model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

image_data = torch.load("clip_images.pt", weights_only=False)

query = input("What are you looking for? ")

inputs = processor(
    text=[query],
    return_tensors="pt",
    padding=True
)

with torch.no_grad():
    text_output = model.text_model(**inputs)

    text_embedding = text_output.pooler_output

    text_embedding = model.text_projection(text_embedding)

    text_embedding = text_embedding / text_embedding.norm(
        dim=-1,
        keepdim=True
    )

results = []

for path, image_embedding in image_data:

    image_embedding = torch.tensor(image_embedding)

    score = torch.dot(
        text_embedding[0],
        image_embedding
    ).item()

    results.append((path, score))

results.sort(key=lambda x: x[1], reverse=True)

print("\nBest matches:\n")

for path, score in results[:10]:

    print(round(score, 4), "-", path)