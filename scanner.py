import os
import sqlite3
from datetime import datetime
from PIL import Image


def refresh_file(path):

    if not os.path.isfile(path):
        remove_file(path)
        return False

    path = os.path.normpath(path).replace("\\", "/")
    file_name = os.path.basename(path)
    extension = os.path.splitext(file_name)[1].lower()
    size = os.path.getsize(path) / (1024 * 1024)
    created = datetime.fromtimestamp(os.path.getctime(path))
    modified = datetime.fromtimestamp(os.path.getmtime(path))
    taken = None

    if extension in {".jpg", ".jpeg", ".tif", ".tiff"}:
        try:
            with Image.open(path) as image:
                exif = image.getexif()
                taken = (
                    exif.get(36867)
                    or exif.get(36868)
                    or exif.get(306)
                )
        except (OSError, ValueError):
            pass

    connection = sqlite3.connect("findly.db")
    try:
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
        cursor.execute(
            """
            INSERT OR REPLACE INTO files
            (name, path, extension, size, created, modified, taken)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                file_name,
                path,
                extension,
                size,
                str(created),
                str(modified),
                taken
            )
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return True


def remove_file(path):

    normalized_path = os.path.normpath(path).replace("\\", "/")
    connection = sqlite3.connect("findly.db")
    try:
        connection.execute(
            "DELETE FROM files WHERE REPLACE(path, char(92), '/') = ?",
            (normalized_path,)
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def scan_folder(folder):

    connection = sqlite3.connect("findly.db")
    cursor = connection.cursor()
    scanned = 0
    skipped = 0
    errors = []
    scanned_paths = set()

    def record_error(error):
        nonlocal skipped
        skipped += 1
        if len(errors) < 5:
            errors.append(str(error))

    def on_walk_error(error):
        record_error(error)

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

    try:
        for root, folders, files in os.walk(
            folder,
            onerror=on_walk_error
        ):

            folders[:] = [
                folder
                for folder in folders
                if folder != ".venv"
            ]

            for file in files:

                path = os.path.join(root, file)
                path = os.path.normpath(path).replace("\\", "/")

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
                            with Image.open(path) as image:
                                exif = image.getexif()
                                taken = (
                                    exif.get(36867)
                                    or exif.get(36868)
                                    or exif.get(306)
                                )
                        except (OSError, ValueError):
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
                    scanned_paths.add(os.path.normcase(path))
                    scanned += 1

                except OSError as error:
                    record_error(f"{path}: {error}")

        if skipped == 0:
            stale_ids = []
            for row_id, indexed_path in cursor.execute(
                "SELECT id, path FROM files"
            ):
                try:
                    indexed_path = os.path.normcase(
                        os.path.abspath(indexed_path)
                    )
                    normalized_folder = os.path.normcase(
                        os.path.abspath(folder)
                    )
                    if (
                        os.path.commonpath(
                            [indexed_path, normalized_folder]
                        )
                        == normalized_folder
                        and os.path.normcase(
                            os.path.normpath(indexed_path).replace("\\", "/")
                        ) not in scanned_paths
                    ):
                        stale_ids.append((row_id,))
                except (TypeError, ValueError):
                    continue

            if stale_ids:
                cursor.executemany(
                    "DELETE FROM files WHERE id = ?",
                    stale_ids
                )

        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    summary = {
        "scanned": scanned,
        "skipped": skipped,
        "errors": errors
    }

    print(
        f"File scan complete for {folder}: "
        f"{scanned} indexed, {skipped} skipped."
    )
    for error in errors:
        print("File scan warning:", error)

    return summary