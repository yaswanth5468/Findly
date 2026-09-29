import os
import sqlite3
from datetime import datetime
from PIL import Image

folder = input("Enter folder path: ")
search = input("What are you looking for? ").lower()

types = {
    "photos": [".jpg", ".jpeg", ".png", ".gif", ".tif", ".tiff"],
    "videos": [".mp4", ".mkv", ".avi", ".mov"],
    "documents": [".pdf", ".docx", ".doc", ".txt"],
    "python": [".py"]
}

if "photo" in search:
    search = "photos"
elif "video" in search:
    search = "videos"
elif "document" in search or "pdf" in search:
    search = "documents"
elif "python" in search:
    search = "python"

database = sqlite3.connect("findly.db")
cursor = database.cursor()

print("\nSearching...\n")

if search in types:

    extensions = types[search]
    placeholders = ",".join("?" * len(extensions))

    cursor.execute(
        f"""
        SELECT name, path, extension, size, created, modified, taken
        FROM files
        WHERE extension IN ({placeholders})
        """,
        extensions
    )

else:

    cursor.execute(
        """
        SELECT name, path, extension, size, created, modified, taken
        FROM files
        WHERE LOWER(name) LIKE ?
        """,
        ("%" + search + "%",)
    )

results = cursor.fetchall()

if len(results) == 0:
    print("No files found.")

else:

    for i, result in enumerate(results):

        name, path, extension, size, created, modified, taken = result

        print(i + 1, ".", name)
        print("   Type:", extension)
        print("   Size:", round(size, 2), "MB")
        print("   Location:", path)
        print("   Created:", created)
        print("   Modified:", modified)

        if taken:
            print("   Taken:", taken)

        print()

    choice = input("Enter file number to open, or press Enter to exit: ")

    if choice.isdigit():

        number = int(choice)

        if number >= 1 and number <= len(results):

            selected_file = results[number - 1][1]

            print("\nOpening:", selected_file)

            os.startfile(selected_file)

        else:
            print("Invalid file number.")

database.close()