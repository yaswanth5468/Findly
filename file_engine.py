import sqlite3
import re
from datetime import datetime, timedelta


def search_files(text, folders=None):

    conn = sqlite3.connect("findly.db")
    cursor = conn.cursor()

    text = text.lower()

    types = []

    if "photo" in text or "image" in text:
        types = [
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".tif",
            ".tiff"
        ]

    elif "video" in text:
        types = [
            ".mp4",
            ".mkv",
            ".avi",
            ".mov"
        ]

    elif "document" in text or "pdf" in text:
        types = [
            ".pdf",
            ".docx",
            ".doc",
            ".txt"
        ]

    elif "python" in text:
        types = [
            ".py"
        ]

    months = {
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

    weekdays = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6
    }

    conditions = []
    values = []

    if types:

        placeholders = ",".join(
            ["?"] * len(types)
        )

        conditions.append(
            "extension IN (" + placeholders + ")"
        )

        values.extend(types)

    if "today" in text:

        today = datetime.now().date()

        conditions.append(
            """
            (
                date(created) = ?
                OR date(modified) = ?
                OR date(substr(taken,1,10)) = ?
            )
            """
        )

        values.extend([
            today.isoformat(),
            today.isoformat(),
            today.isoformat()
        ])

    elif "yesterday" in text:

        yesterday = (
            datetime.now().date()
            - timedelta(days=1)
        )

        conditions.append(
            """
            (
                date(created) = ?
                OR date(modified) = ?
                OR date(substr(taken,1,10)) = ?
            )
            """
        )

        values.extend([
            yesterday.isoformat(),
            yesterday.isoformat(),
            yesterday.isoformat()
        ])

    elif "last week" in text:

        today = datetime.now().date()

        start = (
            today
            - timedelta(days=today.weekday() + 7)
        )

        end = start + timedelta(days=7)

        conditions.append(
            """
            (
                date(created) >= ?
                AND date(created) < ?
            )
            OR
            (
                date(modified) >= ?
                AND date(modified) < ?
            )
            OR
            (
                date(substr(taken,1,10)) >= ?
                AND date(substr(taken,1,10)) < ?
            )
            """
        )

        values.extend([
            start.isoformat(),
            end.isoformat(),
            start.isoformat(),
            end.isoformat(),
            start.isoformat(),
            end.isoformat()
        ])

    elif "last month" in text:

        today = datetime.now().date()

        first_this_month = today.replace(day=1)

        last_month = (
            first_this_month
            - timedelta(days=1)
        )

        start = last_month.replace(day=1)

        end = first_this_month

        conditions.append(
            """
            (
                date(created) >= ?
                AND date(created) < ?
            )
            OR
            (
                date(modified) >= ?
                AND date(modified) < ?
            )
            OR
            (
                date(substr(taken,1,10)) >= ?
                AND date(substr(taken,1,10)) < ?
            )
            """
        )

        values.extend([
            start.isoformat(),
            end.isoformat(),
            start.isoformat(),
            end.isoformat(),
            start.isoformat(),
            end.isoformat()
        ])

    elif "this year" in text:

        year = datetime.now().year

        start = f"{year}-01-01"
        end = f"{year + 1}-01-01"

        conditions.append(
            """
            (
                date(created) >= ?
                AND date(created) < ?
            )
            OR
            (
                date(modified) >= ?
                AND date(modified) < ?
            )
            OR
            (
                date(substr(taken,1,10)) >= ?
                AND date(substr(taken,1,10)) < ?
            )
            """
        )

        values.extend([
            start,
            end,
            start,
            end,
            start,
            end
        ])

    month_number = None

    for month_name in months:

        if month_name in text:

            month_number = months[month_name]

            break

    year_match = re.search(
        r"\b(20\d{2})\b",
        text
    )

    if month_number and year_match:

        year = int(
            year_match.group(1)
        )

        start = datetime(
            year,
            month_number,
            1
        )

        if month_number == 12:

            end = datetime(
                year + 1,
                1,
                1
            )

        else:

            end = datetime(
                year,
                month_number + 1,
                1
            )

        conditions.append(
            """
            (
                date(created) >= ?
                AND date(created) < ?
            )
            OR
            (
                date(modified) >= ?
                AND date(modified) < ?
            )
            OR
            (
                date(substr(taken,1,10)) >= ?
                AND date(substr(taken,1,10)) < ?
            )
            """
        )

        values.extend([
            start.strftime("%Y-%m-%d"),
            end.strftime("%Y-%m-%d"),
            start.strftime("%Y-%m-%d"),
            end.strftime("%Y-%m-%d"),
            start.strftime("%Y-%m-%d"),
            end.strftime("%Y-%m-%d")
        ])

    elif year_match and not month_number:

        year = int(
            year_match.group(1)
        )

        start = f"{year}-01-01"
        end = f"{year + 1}-01-01"

        conditions.append(
            """
            (
                date(created) >= ?
                AND date(created) < ?
            )
            OR
            (
                date(modified) >= ?
                AND date(modified) < ?
            )
            OR
            (
                date(substr(taken,1,10)) >= ?
                AND date(substr(taken,1,10)) < ?
            )
            """
        )

        values.extend([
            start,
            end,
            start,
            end,
            start,
            end
        ])

    every_match = re.search(
        r"(every|all)\s+"
        r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
        text
    )

    if every_match:

        day_name = every_match.group(2)

        day_number = weekdays[day_name]

        sqlite_day = (
            day_number + 1
        ) % 7

        conditions.append(
            """
            (
                CAST(strftime('%w', created) AS INTEGER) = ?
                OR
                CAST(strftime('%w', modified) AS INTEGER) = ?
                OR
                CAST(strftime('%w', substr(taken,1,10)) AS INTEGER) = ?
            )
            """
        )

        values.extend([
            sqlite_day,
            sqlite_day,
            sqlite_day
        ])

    for day_name, day_number in weekdays.items():

        if (
            "this " + day_name in text
            or
            "last " + day_name in text
        ):

            today = datetime.now().date()

            if "this " + day_name in text:

                difference = (
                    day_number
                    - today.weekday()
                ) % 7

                target = today + timedelta(
                    days=difference
                )

            else:

                difference = (
                    today.weekday()
                    - day_number
                ) % 7

                if difference == 0:
                    difference = 7

                target = today - timedelta(
                    days=difference
                )

            conditions.append(
                """
                (
                    date(created) = ?
                    OR date(modified) = ?
                    OR date(substr(taken,1,10)) = ?
                )
                """
            )

            values.extend([
                target.isoformat(),
                target.isoformat(),
                target.isoformat()
            ])

            break

    def convert_size(value, unit):

        value = float(value)

        if unit == "gb":
            return value * 1024

        if unit == "mb":
            return value

        if unit == "kb":
            return value / 1024

        return value

    range_match = re.search(
        r"(?:between|from)\s+"
        r"(\d+(?:\.\d+)?)\s*"
        r"(gb|mb|kb)\s+"
        r"(?:and|to)\s+"
        r"(\d+(?:\.\d+)?)\s*"
        r"(gb|mb|kb)",
        text
    )

    if range_match:

        min_size = convert_size(
            range_match.group(1),
            range_match.group(2)
        )

        max_size = convert_size(
            range_match.group(3),
            range_match.group(4)
        )

        conditions.append(
            "size >= ? AND size <= ?"
        )

        values.extend([
            min_size,
            max_size
        ])

    greater_match = re.search(
        r"(bigger|larger|greater|more)\s+"
        r"than\s+"
        r"(\d+(?:\.\d+)?)\s*"
        r"(gb|mb|kb)",
        text
    )

    if greater_match:

        size = convert_size(
            greater_match.group(2),
            greater_match.group(3)
        )

        conditions.append(
            "size > ?"
        )

        values.append(size)

    over_match = re.search(
        r"\bover\s+"
        r"(\d+(?:\.\d+)?)\s*"
        r"(gb|mb|kb)",
        text
    )

    if over_match:

        size = convert_size(
            over_match.group(1),
            over_match.group(2)
        )

        conditions.append(
            "size > ?"
        )

        values.append(size)

    smaller_match = re.search(
        r"(smaller|less)\s+"
        r"than\s+"
        r"(\d+(?:\.\d+)?)\s*"
        r"(gb|mb|kb)",
        text
    )

    if smaller_match:

        size = convert_size(
            smaller_match.group(2),
            smaller_match.group(3)
        )

        conditions.append(
            "size < ?"
        )

        values.append(size)

    under_match = re.search(
        r"\bunder\s+"
        r"(\d+(?:\.\d+)?)\s*"
        r"(gb|mb|kb)",
        text
    )

    if under_match:

        size = convert_size(
            under_match.group(1),
            under_match.group(2)
        )

        conditions.append(
            "size < ?"
        )

        values.append(size)

    at_least_match = re.search(
        r"at\s+least\s+"
        r"(\d+(?:\.\d+)?)\s*"
        r"(gb|mb|kb)",
        text
    )

    if at_least_match:

        size = convert_size(
            at_least_match.group(1),
            at_least_match.group(2)
        )

        conditions.append(
            "size >= ?"
        )

        values.append(size)

    at_most_match = re.search(
        r"at\s+most\s+"
        r"(\d+(?:\.\d+)?)\s*"
        r"(gb|mb|kb)",
        text
    )

    if at_most_match:

        size = convert_size(
            at_most_match.group(1),
            at_most_match.group(2)
        )

        conditions.append(
            "size <= ?"
        )

        values.append(size)

    if (
        "large" in text
        and not greater_match
        and not over_match
    ):

        conditions.append(
            "size > ?"
        )

        values.append(100)

    if (
        "small" in text
        and not smaller_match
        and not under_match
    ):

        conditions.append(
            "size < ?"
        )

        values.append(10)

    order = ""

    if (
        "biggest" in text
        or "largest" in text
    ):

        order = " ORDER BY size DESC"

    elif "smallest" in text:

        order = " ORDER BY size ASC"

    query = """
    SELECT
        name,
        extension,
        size,
        path,
        created,
        modified,
        taken
    FROM files
    """

    if conditions:

        query += " WHERE "

        query += " AND ".join(
            "(" + condition + ")"
            for condition in conditions
        )

    if folders:

        folder_conditions = []

        for folder in folders:

            folder_conditions.append(
                "path LIKE ?"
            )

            values.append(
                folder.rstrip("\\/")
                + "\\%"
            )

        folder_condition = (
            "("
            + " OR ".join(folder_conditions)
            + ")"
        )

        if conditions:

            query += " AND " + folder_condition

        else:

            query += " WHERE " + folder_condition

    query += order

    cursor.execute(
        query,
        values
    )

    results = cursor.fetchall()

    conn.close()

    return results


def search_files_in_folders(query, folders):

    return search_files(
        query,
        folders
    )