import re


def parse_query(query):

    query = query.lower()

    result = {
        "visual_query": "",
        "file_type": None,
        "year": None,
        "size_condition": None,
        "size_value": None
    }

    if "photo" in query or "picture" in query or "image" in query:
        result["file_type"] = "photo"

    elif "video" in query:
        result["file_type"] = "video"

    visual_words = [
        "person",
        "people",
        "man",
        "woman",
        "car",
        "dog",
        "cat",
        "food",
        "family",
        "college",
        "laptop"
    ]

    for word in visual_words:

        if word in query:

            result["visual_query"] = word

            break

    year = re.search(
        r"\b(19|20)\d{2}\b",
        query
    )

    if year:

        result["year"] = int(year.group())

    size = re.search(
        r"(bigger than|larger than|over|above|greater than|more than|"
        r"smaller than|less than|under|below)\s*"
        r"(\d+(?:\.\d+)?)\s*(mb|gb|kb)",
        query
    )

    if size:

        condition = size.group(1)

        value = float(size.group(2))

        unit = size.group(3)

        if unit == "gb":
            value = value * 1024

        elif unit == "kb":
            value = value / 1024

        if condition in [
            "bigger than",
            "larger than",
            "over",
            "above",
            "greater than",
            "more than"
        ]:

            result["size_condition"] = ">"

        else:

            result["size_condition"] = "<"

        result["size_value"] = value

    return result