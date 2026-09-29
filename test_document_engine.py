from document_engine import search_documents

folder = input("Folder to search: ")
query = input("What are you looking for? ")

results = search_documents(
    query,
    folder
)

print("\nDocument Results:\n")

for result in results:

    print("Type:", result[0])
    print("Location:", result[1])

    if result[2]:
        print("Page/Paragraph:", result[2])

    print("Match:", result[3])
    print("Score:", result[4])

    print("-" * 50)

print("\nTotal results:", len(results))