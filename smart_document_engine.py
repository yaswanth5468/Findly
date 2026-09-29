import os

from document_engine import search_documents
from semantic_search import search_documents as semantic_search


def search_smart_documents(
    query,
    folder
):

    keyword_results = search_documents(
        query,
        folder
    )

    semantic_results = semantic_search(
        query
    )

    filtered_semantic = []

    for path, score in semantic_results:

        if score < 0.15:

            continue

        path = os.path.abspath(path)

        folder_path = os.path.abspath(
            folder
        )

        if (
            path == folder_path
            or path.startswith(
                folder_path + os.sep
            )
        ):

            filtered_semantic.append(
                (
                    path,
                    score
                )
            )

    results = {}

    for result in keyword_results:

        file_type = result[0]
        path = result[1]
        location = result[2]
        snippet = result[3]
        keyword_score = result[4]

        results[path] = {
            "type": file_type,
            "path": path,
            "location": location,
            "snippet": snippet,
            "keyword_score": keyword_score,
            "semantic_score": 0
        }

    for path, semantic_score in filtered_semantic:

        if path in results:

            results[path]["semantic_score"] = (
                semantic_score
            )

        else:

            extension = os.path.splitext(
                path
            )[1].lower()

            if extension == ".pdf":

                file_type = "PDF"

            elif extension == ".docx":

                file_type = "DOCX"

            else:

                file_type = "TXT"

            results[path] = {
                "type": file_type,
                "path": path,
                "location": None,
                "snippet": "",
                "keyword_score": 0,
                "semantic_score": semantic_score
            }

    final_results = []

    for data in results.values():

        combined_score = (
            data["keyword_score"] * 0.5
            + data["semantic_score"] * 2
        )

        final_results.append(
            (
                data["type"],
                data["path"],
                data["location"],
                data["snippet"],
                combined_score
            )
        )

    final_results.sort(
        key=lambda x: x[4],
        reverse=True
    )

    return final_results