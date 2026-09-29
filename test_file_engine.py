from findly_file_engine import search_files

query = input("Search files: ")

results = search_files(query)

print("\nResults:\n")

for result in results[:10]:

    print(result)