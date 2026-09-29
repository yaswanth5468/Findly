from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input, decode_predictions
from tensorflow.keras.preprocessing import image
import os
import sqlite3
import numpy as np

model = MobileNetV2(weights="imagenet")

folder = input("Enter photo folder path: ")

conn = sqlite3.connect("findly.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS image_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT,
    tags TEXT
)
""")

for root, folders, files in os.walk(folder):

    for file in files:

        if file.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):

            path = os.path.join(root, file)

            print("\nAnalyzing:", file)

            try:

                img = image.load_img(path, target_size=(224, 224))

                x = image.img_to_array(img)

                x = np.expand_dims(x, axis=0)

                x = preprocess_input(x)

                result = model.predict(x, verbose=0)

                predictions = decode_predictions(result, top=5)[0]

                tags = []

                for item in predictions:
                    tags.append(item[1])

                tag_text = ", ".join(tags)

                cursor.execute(
                    "INSERT INTO image_tags (path, tags) VALUES (?, ?)",
                    (path, tag_text)
                )

                conn.commit()

                print("Found:", tag_text)

            except Exception as e:

                print("Skipped:", e)

conn.close()

print("\nImage indexing completed!")