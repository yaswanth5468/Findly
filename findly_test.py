query = input("What are you looking for? ")

words = query.lower()

ai_words = [
    "photo with",
    "photos with",
    "picture with",
    "pictures with",
    "photo of",
    "photos of",
    "picture of",
    "pictures of",
    "image of",
    "images of",
    "person",
    "people",
    "food",
    "car",
    "dog",
    "cat",
    "family",
    "college"
]

is_ai_search = False

for word in ai_words:

    if word in words:
        is_ai_search = True
        break


if is_ai_search:

    print("\nAI PHOTO SEARCH selected")
    print("Query:", query)

else:

    print("\nNORMAL FILE SEARCH selected")
    print("Query:", query)