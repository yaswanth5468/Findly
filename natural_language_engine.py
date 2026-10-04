import os

from query_parser import parse_query

from image_engine import search_images

from file_engine import search_files_in_folders

from smart_document_engine import search_smart_documents


DOCUMENT_EXTENSIONS = {
    ".txt",
    ".pdf",
    ".docx"
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

    words = [
        "document",
        "documents",
        "pdf",
        "pdfs",
        "word",
        "docx",
        "text",
        "txt"
    ]

    query = query.lower()

    for word in words:

        if word in query:
            return True

    return False


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


def search_findly(query, folders=None):

    query = query.strip()

    if not query:

        return []

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

        results = []

        if folders:

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

        return results

    # --------------------------------
    # IMAGE SEARCH
    # --------------------------------

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

            return search_combined(
                query,
                folders
            )

        return search_images(
            details["visual_query"]
            if details["visual_query"]
            else query,
            folders
        )

    # --------------------------------
    # NORMAL FILE SEARCH
    # --------------------------------

    print(
        "Search mode: FILE"
    )

    return search_files_in_folders(
        query,
        folders
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