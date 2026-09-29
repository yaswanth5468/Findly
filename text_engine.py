import os

def search_text_files(query, folder):
    results = []

    query = query.lower()

    for root, folders, files in os.walk(folder):

        folders[:] = [
            folder
            for folder in folders
            if folder != ".venv"
        ]

        for file in files:

            if not file.lower().endswith(".txt"):
                continue

            path = os.path.join(root, file)

            try:
                with open(
                    path,
                    "r",
                    encoding="utf-8",
                    errors="ignore"
                ) as f:
                    content = f.read()

                lower_content = content.lower()

                if query in lower_content:

                    position = lower_content.find(query)

                    start = max(0, position - 80)
                    end = min(
                        len(content),
                        position + len(query) + 120
                    )

                    snippet = content[start:end].replace(
                        "\n",
                        " "
                    )

                    results.append(
                        (path, snippet)
                    )

            except:
                pass

    return results