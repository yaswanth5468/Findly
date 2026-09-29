import tkinter as tk
from PIL import Image, ImageTk
from transformers import CLIPProcessor, CLIPModel
import torch
import os

model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

image_data = torch.load(
    "clip_images_new.pt",
    weights_only=False
)


def search_photos():

    query = search_box.get()

    if query == "":
        return

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

    results.sort(
        key=lambda x: x[1],
        reverse=True
    )

    for widget in results_frame.winfo_children():
        widget.destroy()

    photos.clear()

    title_label.config(
        text="Results for: " + query
    )

    count = 0

    threshold = 0.20

    for path, score in results:

        if count >= 6:
            break

        if score < threshold:
            continue

        if not os.path.exists(path):
            continue

        try:

            img = Image.open(path).convert("RGB")

            img.thumbnail((250, 200))

            photo = ImageTk.PhotoImage(img)

            box = tk.Frame(results_frame)

            box.pack(
                side="left",
                padx=10,
                pady=10
            )

            button = tk.Button(
                box,
                image=photo,
                command=lambda p=path: os.startfile(p)
            )

            button.pack()

            score_label = tk.Label(
                box,
                text="Match score: " + str(round(score, 4))
            )

            score_label.pack()

            photos.append(photo)

            count += 1

        except Exception as e:

            print("Skipped:", path)

    if count == 0:

        no_result = tk.Label(
            results_frame,
            text="No strong matches found.",
            font=("Arial", 16)
        )

        no_result.pack(pady=30)


root = tk.Tk()

root.title("Findly - AI Photo Search")

root.geometry("1100x700")


title = tk.Label(
    root,
    text="Findly",
    font=("Arial", 28)
)

title.pack(pady=15)


search_frame = tk.Frame(root)

search_frame.pack()


search_box = tk.Entry(
    search_frame,
    width=60,
    font=("Arial", 14)
)

search_box.pack(
    side="left",
    padx=5
)


search_button = tk.Button(
    search_frame,
    text="SEARCH",
    font=("Arial", 12),
    command=search_photos
)

search_button.pack(
    side="left",
    padx=5
)
search_box.bind(
    "<Return>",
    lambda event: search_photos()
)

title_label = tk.Label(
    root,
    text="Search for your photos",
    font=("Arial", 14)
)

title_label.pack(pady=15)


results_frame = tk.Frame(root)

results_frame.pack(pady=20)


photos = []


root.mainloop()