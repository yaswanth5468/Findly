import tkinter as tk
from PIL import Image, ImageTk
import torch
import os

image_data = torch.load("clip_images.pt", weights_only=False)

root = tk.Tk()
root.title("Findly - AI Photo Search")
root.geometry("900x650")

query_label = tk.Label(root, text="Search your photos")
query_label.pack(pady=10)

query_entry = tk.Entry(root, width=50)
query_entry.pack()

result_frame = tk.Frame(root)
result_frame.pack(pady=20)

photos = []

for path, score in image_data[:20]:

    try:
        img = Image.open(path)
        img.thumbnail((150, 150))

        photo = ImageTk.PhotoImage(img)

        label = tk.Label(result_frame, image=photo)
        label.image = photo
        label.pack(side="left", padx=5)

        photos.append(photo)

    except Exception as e:
        print("Skipped:", path)

root.mainloop()