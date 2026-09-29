from text_engine import search_text_files

folder = input("Folder to search: ")
query = input("What are you looking for? ")

results = search_text_files(query, folder)

print("\nResults:\n")

for result in results:
    print("Location:", result[0])
    print("Match:", result[1])
    print("-" * 50)

print("\nTotal results:", len(results))