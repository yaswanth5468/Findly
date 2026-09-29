from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input, decode_predictions
from tensorflow.keras.preprocessing import image
import numpy as np

model = MobileNetV2(weights="imagenet")

path = input("Enter image path: ")

img = image.load_img(path, target_size=(224, 224))

x = image.img_to_array(img)

x = np.expand_dims(x, axis=0)

x = preprocess_input(x)

result = model.predict(x)

predictions = decode_predictions(result, top=5)[0]

print("\nWhat I found:\n")

for item in predictions:
    name = item[1]
    probability = item[2] * 100

    print(name, "-", round(probability, 2), "%")