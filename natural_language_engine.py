import os
import re

from query_parser import parse_query

from image_engine import search_images

from file_engine import search_files_in_folders

from smart_document_engine import search_smart_documents


def normalize_folders(folders):

    if not folders:
        return []

    if isinstance(folders, str):
        folders = [folders]

    normalized = []

    for folder in folders:
        if not folder:
            continue
        cleaned = os.path.normpath(str(folder)).replace("\\", "/")
        cleaned = "/".join(part for part in cleaned.split("/") if part)
        if cleaned not in normalized:
            normalized.append(cleaned)

    return normalized


def deduplicate_results(results):

    unique = []
    seen = set()

    if results is None:
        return unique

    for result in results:

        if isinstance(result, (tuple, list)) and result:
            if len(result) >= 7 and isinstance(result[3], str):
                result_path = result[3]
            elif (
                len(result) == 5
                and str(result[0]).upper() in {"PDF", "DOCX", "TXT"}
                and isinstance(result[1], str)
            ):
                result_path = result[1]
            elif len(result) == 5 and isinstance(result[3], str):
                result_path = result[3]
            elif len(result) in {2, 4} and isinstance(result[1 if len(result) == 4 else 0], str):
                result_path = result[1 if len(result) == 4 else 0]
            else:
                result_path = None

            key = (
                os.path.normcase(os.path.normpath(result_path))
                if result_path
                else tuple(result)
            )

            if key not in seen:
                seen.add(key)
                unique.append(tuple(result))
            continue

        if isinstance(result, str):
            if result in seen:
                continue
            seen.add(result)
            unique.append(result)

    return unique


DOCUMENT_EXTENSIONS = {
    ".txt",
    ".pdf",
    ".doc",
    ".docx"
}

DOCUMENT_CATEGORY_WORDS = {
    "document", "documents", "doc", "docs", "file", "files",
    "text", "texts", "pdf", "pdfs", "word", "docx", "txt",
    "excel", "spreadsheet", "spreadsheets", "xls", "xlsx",
    "xlsm", "xlsb", "csv", "presentation", "presentations",
    "ppt", "pptx", "rtf", "odt", "ods", "odp"
}

DOCUMENT_QUERY_FILLER_WORDS = DOCUMENT_CATEGORY_WORDS | {
    "a", "about", "all", "and", "containing", "every", "find",
    "for", "get", "list", "my", "of", "please", "show", "the",
    "with", "from", "in", "on", "last", "this", "week", "month",
    "year", "today", "yesterday", "january", "february", "march",
    "april", "may", "june", "july", "august", "september",
    "october", "november", "december", "monday", "tuesday",
    "wednesday", "thursday", "friday", "saturday", "sunday",
    "under", "over", "above", "below", "bigger", "larger",
    "smaller", "than", "more", "less", "least", "most", "between",
    "to", "gb", "mb", "kb"
}

PERSON_QUERY_WORDS = {
    "person", "people", "man", "men", "woman", "women",
    "child", "children", "boy", "girl"
}


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
    ".tif",
    ".tiff"
}


def is_document_query(query):

    words = set(re.findall(r"[a-z0-9]+", query.lower()))
    return bool(words & DOCUMENT_CATEGORY_WORDS)


def is_document_browse_query(query):

    words = re.findall(r"[a-z0-9]+", query.lower())
    meaningful_words = [
        word
        for word in words
        if word not in DOCUMENT_QUERY_FILLER_WORDS
        and not re.fullmatch(r"(?:19|20)\d{2}", word)
        and not re.fullmatch(r"\d+(?:\.\d+)?", word)
    ]
    return not meaningful_words


def is_image_query(query):

    words = [
        "photo",
        "photos",
        "picture",
        "pictures",
        "image",
        "images"
    ]

    query = query.lower()

    for word in words:

        if word in query:
            return True

    return False


def has_visual_query(query):

    details = parse_query(query)

    return bool(
        details["visual_query"]
    )


def is_person_query(query):

    return bool(
        set(re.findall(r"[a-z0-9]+", query.lower()))
        & PERSON_QUERY_WORDS
    )


def search_findly(query, folders=None):

    if query is None:
        return []

    query = str(query).strip()

    if not query:
        return []

    folders = normalize_folders(folders)

    print("\n==============================")
    print("Findly Natural Language Search")
    print("==============================")

    print(
        "Query:",
        query
    )

    details = parse_query(query)

    print(
        "Parsed:",
        details
    )

    # --------------------------------
    # DOCUMENT SEARCH
    # --------------------------------

    if is_document_query(query):

        print(
            "Search mode: DOCUMENT"
        )

        if is_document_browse_query(query):
            return search_files_in_folders(query, folders)

        results = []

        for folder in folders:

            document_results = (
                search_smart_documents(
                    query,
                    folder
                )
            )

            results.extend(
                document_results
            )

        return deduplicate_results(results)

    # --------------------------------
    # IMAGE SEARCH
    # --------------------------------

    if is_person_query(query):

        print(
            "Search mode: PERSON DETECTION"
        )

        from person_detector import search_person_images

        return deduplicate_results(
            search_person_images(folders)
        )

    if (
        is_image_query(query)
        or
        has_visual_query(query)
    ):

        print(
            "Search mode: IMAGE"
        )

        # If the query contains
        # date/size filters, use the
        # existing combined engine.

        if (
            details["year"] is not None
            or
            details["month"] is not None
            or
            details["day"] is not None
            or
            details["size_condition"] is not None
        ):

            from combined_engine import search_combined

            return deduplicate_results(
                search_combined(
                    query,
                    folders
                )
            )

        return deduplicate_results(
            search_images(query, folders)
        )

    # --------------------------------
    # NORMAL FILE SEARCH
    # --------------------------------

    print(
        "Search mode: FILE"
    )

    if not folders:
        return []

    return deduplicate_results(
        search_files_in_folders(
            query,
            folders
        )
    )


if __name__ == "__main__":

    print(
        "Findly Natural Language Engine"
    )

    query = input(
        "\nEnter search query: "
    )

    results = search_findly(
        query
    )

    print(
        "\nResults:"
    )

    for result in results:

        print(
            result
        )