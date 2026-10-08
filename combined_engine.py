import os
import sqlite3

from datetime import datetime

from image_engine import load_image_index, search_images

from query_parser import parse_query


def search_combined(query, folders=None):

    details = parse_query(query)

    visual_query = details["visual_query"]

    file_type = details["file_type"]

    year = details["year"]

    month = details["month"]

    day = details["day"]

    if visual_query in {"person", "people", "man", "woman"}:
        from person_detector import search_person_images

        image_results = search_person_images(folders)
    elif visual_query:
        image_results = search_images(visual_query, folders)
    elif file_type == "photo":
        image_results = [
            (entry[0], 0.0)
            for entry in load_image_index()
            if isinstance(entry, (tuple, list)) and len(entry) >= 2
        ]
    else:
        return []

    needs_taken_date = any(
        details[key] is not None
        for key in ("date_start", "year", "month", "day")
    ) or bool(details["weekdays"])
    taken_dates = (
        get_photo_taken_dates(
            [
                path
                for path, _score in image_results
                if isinstance(path, str) and os.path.isfile(path)
            ]
        )
        if needs_taken_date
        else {}
    )

    results = []

    for path, score in image_results:

        if not os.path.exists(path):

            continue

        if folders and not any(
            is_inside_folder(path, folder)
            for folder in folders
        ):
            continue

        extension = os.path.splitext(
            path
        )[1].lower()

        # -------------------------
        # File type filter
        # -------------------------

        if file_type == "photo":

            if extension not in [

                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".tif",
                ".tiff",
                ".webp",

            ]:

                continue

        # -------------------------
        # File size
        # -------------------------

        try:
            stat = os.stat(path)
            size = stat.st_size / (1024 * 1024)
            file_dates = {
                datetime.fromtimestamp(stat.st_ctime).date(),
                datetime.fromtimestamp(stat.st_mtime).date(),
            }
        except OSError:
            continue

        # -------------------------
        # Date filter
        # -------------------------

        taken = taken_dates.get(os.path.normcase(os.path.abspath(path)))
        if taken:
            file_dates.add(taken)

        has_date_filter = (
            details["date_start"] is not None
            or year is not None
            or month is not None
            or day is not None
            or bool(details["weekdays"])
        )
        if details["date_start"] is not None:
            file_dates = {
                file_date
                for file_date in file_dates
                if details["date_start"] <= file_date < details["date_end"]
            }

        if year or month or day:
            file_dates = {
                file_date
                for file_date in file_dates
                if (year is None or file_date.year == year)
                and (month is None or file_date.month == month)
                and (day is None or file_date.day == day)
            }

        if details["weekdays"]:
            file_dates = {
                file_date
                for file_date in file_dates
                if file_date.weekday() in details["weekdays"]
            }

        if has_date_filter and not file_dates:
            continue

        # -------------------------
        # Size filter
        # -------------------------

        minimum_size = details["size_min"]
        maximum_size = details["size_max"]
        if minimum_size is not None:
            if details["size_condition"] == ">":
                if size <= minimum_size:
                    continue
            elif size < minimum_size:
                continue
        if maximum_size is not None:
            if (
                size >= maximum_size
                and details["size_condition"] == "<"
            ):
                continue
            if size > maximum_size and details["size_condition"] != "<":
                continue

        # -------------------------
        # Add result
        # -------------------------

        results.append(

            (

                os.path.basename(path),

                extension,

                size,

                path,

                score

            )

        )

    # -------------------------
    # Sort by AI similarity
    # -------------------------

    if details["size_order"]:
        results.sort(
            key=lambda result: result[2],
            reverse=details["size_order"] == "desc",
        )
    else:
        results.sort(
            key=lambda result: result[4],
            reverse=True,
        )

    return results


def is_inside_folder(path, folder):
    try:
        return os.path.commonpath(
            [
                os.path.normcase(os.path.abspath(path)),
                os.path.normcase(os.path.abspath(folder)),
            ]
        ) == os.path.normcase(os.path.abspath(folder))
    except ValueError:
        return False


def get_photo_taken_dates(paths):
    paths_by_key = {
        os.path.normcase(os.path.abspath(path)): os.path.normpath(path).replace(
            "\\", "/"
        )
        for path in paths
    }
    if not paths_by_key:
        return {}

    taken_dates = {}
    try:
        connection = sqlite3.connect("findly.db")
        try:
            paths = list(paths_by_key.values())
            for start in range(0, len(paths), 500):
                placeholders = ",".join("?" for _ in paths[start:start + 500])
                rows = connection.execute(
                    f"""
                    SELECT REPLACE(path, char(92), '/'), taken
                    FROM files
                    WHERE taken IS NOT NULL
                    AND REPLACE(path, char(92), '/') IN ({placeholders})
                    """,
                    paths[start:start + 500],
                )
                for saved_path, value in rows:
                    parsed = parse_taken_date(value)
                    if parsed is not None:
                        taken_dates[
                            os.path.normcase(os.path.abspath(saved_path))
                        ] = parsed
        finally:
            connection.close()
    except sqlite3.Error:
        print("Could not load photo capture dates from the file index.")
    return taken_dates


def parse_taken_date(value):
    if not value:
        return None
    value = str(value)
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        for date_format in ("%Y:%m:%d %H:%M:%S", "%Y:%m:%d"):
            try:
                return datetime.strptime(value, date_format).date()
            except ValueError:
                continue
        return None