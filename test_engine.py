from combined_engine import search_combined

query = input("Search Findly: ")

results = search_combined(query)

print("\nCombined Results:\n")

for result in results:

    print("\nName:", result[0])
    print("Type:", result[1])
    print("Size:", round(result[2], 2), "MB")
    print("Location:", result[3])
    print("Match:", round(result[4], 4))

print("\nTotal results:", len(results))