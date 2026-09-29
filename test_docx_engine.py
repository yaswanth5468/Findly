from docx_engine import search_docx_files

folder = input("Folder to search: ")
query = input("What are you looking for? ")

results = search_docx_files(query, folder)

print("\nResults:\n")

for result in results:

    print("Location:", result[0])
    print("Paragraph:", result[1])
    print("Match:", result[2])
    print("-" * 50)

print("\nTotal results:", len(results))