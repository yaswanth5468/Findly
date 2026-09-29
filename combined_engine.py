import os
from datetime import datetime

from image_engine import search_images
from query_parser import parse_query


def get_file_date(path):

    try:
        created = datetime.fromtimestamp(
            os.path.getctime(path)
        )

        modified = datetime.fromtimestamp(
            os.path.getmtime(path)
        )

        return created, modified

    except Exception:

        return None, None


def search_combined(query):

    details = parse_query(query)

    visual_query = details["visual_query"]
    file_type = details["file_type"]
    year = details["year"]
    size_condition = details["size_condition"]
    size_value = details["size_value"]

    if not visual_query:

        return []

    image_results = search_images(visual_query)

    results = []

    for path, score in image_results:

        if not os.path.exists(path):
            continue

        extension = os.path.splitext(path)[1].lower()

        if file_type == "photo":

            if extension not in [
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".tif",
                ".tiff"
            ]:

                continue

        size = os.path.getsize(path) / (1024 * 1024)

        if year:

            created, modified = get_file_date(path)

            found_year = False

            if created and created.year == year:

                found_year = True

            if modified and modified.year == year:

                found_year = True

            if not found_year:

                continue

        if size_condition == ">":

            if size <= size_value:

                continue

        elif size_condition == "<":

            if size >= size_value:

                continue

        results.append(
            (
                os.path.basename(path),
                extension,
                size,
                path,
                score
            )
        )

    results.sort(
        key=lambda x: x[4],
        reverse=True
    )

    return results