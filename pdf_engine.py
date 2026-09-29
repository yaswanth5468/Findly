import os
from pypdf import PdfReader

def search_pdf_files(query, folder):
    results = []

    query = query.lower()

    for root, folders, files in os.walk(folder):

        folders[:] = [
            folder
            for folder in folders
            if folder != ".venv"
        ]

        for file in files:

            if not file.lower().endswith(".pdf"):
                continue

            path = os.path.join(root, file)

            try:
                reader = PdfReader(path)

                for page_number, page in enumerate(reader.pages, 1):

                    text = page.extract_text()

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

                        snippet = text[start:end].replace(
                            "\n",
                            " "
                        )

                        results.append(
                            (
                                path,
                                page_number,
                                snippet
                            )
                        )

                        break

            except:
                pass

    return results