import re

from datetime import datetime

from dateutil.relativedelta import relativedelta


MONTHS = {

    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12

}


def parse_query(query):

    query = query.lower()

    result = {

        "visual_query": "",
        "file_type": None,

        "year": None,
        "month": None,
        "day": None,

        "size_condition": None,
        "size_value": None

    }

    # -------------------------
    # File type
    # -------------------------

    if (
        "photo" in query
        or "picture" in query
        or "image" in query
    ):

        result["file_type"] = "photo"

    elif "video" in query:

        result["file_type"] = "video"

    # -------------------------
    # Visual query
    # -------------------------

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

    # -------------------------
    # Current date
    # -------------------------

    today = datetime.now()

    # -------------------------
    # Year
    # -------------------------

    year = re.search(
        r"\b(19|20)\d{2}\b",
        query
    )

    if year:

        result["year"] = int(
            year.group()
        )

    # -------------------------
    # Month
    # -------------------------

    for month_name, month_number in MONTHS.items():

        if re.search(
            r"\b" + month_name + r"\b",
            query
        ):

            result["month"] = month_number

            break

    # -------------------------
    # Relative dates
    # -------------------------

    if "today" in query:

        result["year"] = today.year
        result["month"] = today.month
        result["day"] = today.day

    elif "yesterday" in query:

        yesterday = today - relativedelta(
            days=1
        )

        result["year"] = yesterday.year
        result["month"] = yesterday.month
        result["day"] = yesterday.day

    elif "this year" in query:

        result["year"] = today.year

    elif "last year" in query:

        result["year"] = today.year - 1

    elif "this month" in query:

        result["year"] = today.year
        result["month"] = today.month

    elif "last month" in query:

        previous_month = today - relativedelta(
            months=1
        )

        result["year"] = previous_month.year
        result["month"] = previous_month.month

    # -------------------------
    # File size
    # -------------------------

    size = re.search(

        r"(bigger than|larger than|over|above|greater than|more than|"
        r"smaller than|less than|under|below)\s*"
        r"(\d+(?:\.\d+)?)\s*"
        r"(mb|gb|kb)",

        query

    )

    if size:

        condition = size.group(1)

        value = float(
            size.group(2)
        )

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


if __name__ == "__main__":

    query = input(
        "Enter query: "
    )

    result = parse_query(
        query
    )

    print("\nParsed query:")

    for key, value in result.items():

        print(
            key,
            ":",
            value
        )