import os
from docx import Document

def search_docx_files(query, folder):
    results = []

    query = query.lower()

    for root, folders, files in os.walk(folder):

        folders[:] = [
            folder
            for folder in folders
            if folder != ".venv"
        ]

        for file in files:

            if not file.lower().endswith(".docx"):
                continue

            path = os.path.join(root, file)

            try:
                document = Document(path)

                for paragraph_number, paragraph in enumerate(
                    document.paragraphs,
                    1
                ):

                    text = paragraph.text

                    if not text:
                        continue

                    lower_text = text.lower()

                    if query in lower_text:

                        position = lower_text.find(query)

                        start = max(
                            0,
                            position - 80
                        )

                        end = min(
                            len(text),
                            position + len(query) + 120
                        )

                        snippet = text[start:end]

                        results.append(
                            (
                                path,
                                paragraph_number,
                                snippet
                            )
                        )

                        break

            except:
                pass

    return results