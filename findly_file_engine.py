import sqlite3


def search_files(query):

    connection = sqlite3.connect("findly.db")

    cursor = connection.cursor()

    words = query.lower().split()

    conditions = []
    values = []

    for word in words:

        if word in ["pdf"]:
            conditions.append("extension = ?")
            values.append(".pdf")

        elif word in ["python", "py"]:
            conditions.append("extension = ?")
            values.append(".py")

        elif word in ["jpg", "jpeg"]:
            conditions.append("extension = ?")
            values.append("." + word)

        elif word in ["png"]:
            conditions.append("extension = ?")
            values.append(".png")

        elif word in ["mp4", "video", "videos"]:
            conditions.append("extension IN (?, ?, ?, ?)")
            values.extend([".mp4", ".mkv", ".avi", ".mov"])

    if len(conditions) == 0:

        cursor.execute(
            "SELECT name, path, extension, size, modified FROM files"
        )

    else:

        sql = """
        SELECT name, path, extension, size, modified
        FROM files
        WHERE
        """ + " AND ".join(conditions)

        cursor.execute(sql, values)

    results = cursor.fetchall()

    connection.close()

    return results