import os
import sqlite3
from datetime import datetime
from PIL import Image


def scan_folder(folder):

    connection = sqlite3.connect("findly.db")
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            path TEXT UNIQUE,
            extension TEXT,
            size REAL,
            created TEXT,
            modified TEXT,
            taken TEXT
        )
        """
    )

    for root, folders, files in os.walk(folder):

        folders[:] = [
            folder
            for folder in folders
            if folder != ".venv"
        ]

        for file in files:

            path = os.path.join(root, file)

            try:
                extension = os.path.splitext(file)[1].lower()

                size = os.path.getsize(path) / (
                    1024 * 1024
                )

                created = datetime.fromtimestamp(
                    os.path.getctime(path)
                )

                modified = datetime.fromtimestamp(
                    os.path.getmtime(path)
                )

                taken = None

                if extension in [
                    ".jpg",
                    ".jpeg",
                    ".tif",
                    ".tiff"
                ]:

                    try:
                        image = Image.open(path)
                        exif = image.getexif()

                        taken = (
                            exif.get(36867)
                            or exif.get(36868)
                            or exif.get(306)
                        )

                    except:
                        pass

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO files
                    (
                        name,
                        path,
                        extension,
                        size,
                        created,
                        modified,
                        taken
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        file,
                        path,
                        extension,
                        size,
                        str(created),
                        str(modified),
                        taken
                    )
                )

            except:
                pass

    connection.commit()
    connection.close()