from text_engine import search_text_files
from pdf_engine import search_pdf_files
from docx_engine import search_docx_files


def search_documents(query, folder):

    words = query.lower().split()

    file_type = None

    if "pdf" in words:
        file_type = "PDF"

    elif "word" in words or "docx" in words:
        file_type = "DOCX"

    elif "txt" in words or "text" in words:
        file_type = "TXT"

    filtered_words = []

    for word in words:

        if word in [
            "document",
            "documents",
            "file",
            "files",
            "find",
            "my",
            "the",
            "about",
            "containing",
            "pdf",
            "word",
            "docx",
            "txt",
            "text"
        ]:
            continue

        filtered_words.append(word)

    if not filtered_words:
        return []

    all_results = {}

    for word in filtered_words:

        current_results = []

        if file_type is None or file_type == "TXT":

            txt_results = search_text_files(
                word,
                folder
            )

            for result in txt_results:

                current_results.append(
                    (
                        "TXT",
                        result[0],
                        None,
                        result[1]
                    )
                )

        if file_type is None or file_type == "PDF":

            pdf_results = search_pdf_files(
                word,
                folder
            )

            for result in pdf_results:

                current_results.append(
                    (
                        "PDF",
                        result[0],
                        result[1],
                        result[2]
                    )
                )

        if file_type is None or file_type == "DOCX":

            docx_results = search_docx_files(
                word,
                folder
            )

            for result in docx_results:

                current_results.append(
                    (
                        "DOCX",
                        result[0],
                        result[1],
                        result[2]
                    )
                )

        current_paths = set()

        for result in current_results:
            current_paths.add(result[1])

        if not all_results:

            for result in current_results:
                all_results[result[1]] = {
                    "result": result,
                    "score": 1
                }

        else:

            for path in list(all_results.keys()):

                if path in current_paths:
                    all_results[path]["score"] += 1

                else:
                    del all_results[path]

    results = []

    for data in all_results.values():

        result = data["result"]
        score = data["score"]

        results.append(
            (
                result[0],
                result[1],
                result[2],
                result[3],
                score
            )
        )

    results.sort(
        key=lambda x: x[4],
        reverse=True
    )

    return results