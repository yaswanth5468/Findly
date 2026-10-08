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
        "date_start": None,
        "date_end": None,
        "weekdays": [],

        "size_condition": None,
        "size_value": None,
        "size_min": None,
        "size_max": None,
        "size_order": None

    }

    # -------------------------
    # File type
    # -------------------------

    if re.search(r"\b(photos?|pictures?|images?)\b", query):

        result["file_type"] = "photo"

    elif re.search(r"\bvideos?\b", query):

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

    if re.search(r"\btoday\b", query):

        result["year"] = today.year
        result["month"] = today.month
        result["day"] = today.day
        result["date_start"] = today.date()
        result["date_end"] = today.date() + relativedelta(days=1)

    elif re.search(r"\byesterday\b", query):

        yesterday = today - relativedelta(
            days=1
        )

        result["year"] = yesterday.year
        result["month"] = yesterday.month
        result["day"] = yesterday.day
        result["date_start"] = yesterday.date()
        result["date_end"] = yesterday.date() + relativedelta(days=1)

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

    elif "this week" in query:
        start = today.date() - relativedelta(days=today.weekday())
        result["date_start"] = start
        result["date_end"] = start + relativedelta(days=7)

    elif "last week" in query:
        start = today.date() - relativedelta(days=today.weekday() + 7)
        result["date_start"] = start
        result["date_end"] = start + relativedelta(days=7)

    elif "last 7 days" in query or "past 7 days" in query:
        result["date_start"] = today.date() - relativedelta(days=6)
        result["date_end"] = today.date() + relativedelta(days=1)

    weekday_names = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }
    every_weekday = re.search(
        r"\b(?:every|all)\s+(monday|tuesday|wednesday|thursday|"
        r"friday|saturday|sunday)\b",
        query,
    )
    if every_weekday:
        result["weekdays"] = [weekday_names[every_weekday.group(1)]]
    else:
        for name, weekday in weekday_names.items():
            if re.search(r"\b(?:this|last)\s+" + name + r"\b", query):
                result["weekdays"] = [weekday]
                break

    # -------------------------
    # File size
    # -------------------------

    size_range = re.search(
        r"\b(?:between|from)\s+"
        r"(\d+(?:\.\d+)?)\s*(mb|gb|kb)\s+"
        r"(?:and|to)\s+"
        r"(\d+(?:\.\d+)?)\s*(mb|gb|kb)\b",
        query,
    )

    def to_megabytes(value, unit):
        value = float(value)
        if unit == "gb":
            return value * 1024
        if unit == "kb":
            return value / 1024
        return value

    if size_range:
        first = to_megabytes(size_range.group(1), size_range.group(2))
        second = to_megabytes(size_range.group(3), size_range.group(4))
        result["size_min"] = min(first, second)
        result["size_max"] = max(first, second)

    size = re.search(

        r"(bigger than|larger than|over|above|greater than|more than|"
        r"smaller than|less than|under|below|at least|at most)\s*"
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

        if condition == "at least":
            result["size_condition"] = ">="
        elif condition == "at most":
            result["size_condition"] = "<="
        elif condition in [

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
        if result["size_condition"] == ">":
            result["size_min"] = value
        elif result["size_condition"] == ">=":
            result["size_min"] = value
        elif result["size_condition"] in {"<", "<="}:
            result["size_max"] = value

    if re.search(r"\b(?:largest|biggest)\b", query):
        result["size_order"] = "desc"
    elif re.search(r"\bsmallest\b", query):
        result["size_order"] = "asc"

    if "large" in query and result["size_min"] is None:
        result["size_condition"] = ">"
        result["size_min"] = 100
    elif "small" in query and result["size_max"] is None:
        result["size_condition"] = "<"
        result["size_max"] = 10

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