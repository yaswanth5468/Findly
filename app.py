import json
import os

from flask import Flask, render_template, request, jsonify

from natural_language_engine import search_findly


app = Flask(__name__)


FOLDER_CONFIG_PATH = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
    "Findly",
    "approved_folders.json",
)


def default_search_folders():
    home = os.path.expanduser("~")
    candidates = []

    for folder in [
        os.path.join(home, "Desktop"),
        os.path.join(home, "Documents"),
        os.path.join(home, "Downloads"),
        os.path.join(home, "Pictures"),
        os.path.join(home, "Videos"),
        os.path.join(home, "OneDrive"),
        home,
    ]:
        if folder and os.path.isdir(folder):
            candidates.append(os.path.normpath(folder))

    unique = []
    seen = set()
    for folder in candidates:
        key = os.path.normcase(os.path.abspath(folder))
        if key not in seen:
            seen.add(key)
            unique.append(folder)
    return unique


def resolve_search_folders():
    folders = []

    try:
        if os.path.exists(FOLDER_CONFIG_PATH):
            with open(FOLDER_CONFIG_PATH, "r", encoding="utf-8") as config_file:
                saved = json.load(config_file)
            if isinstance(saved, list):
                folders = [
                    os.path.normpath(folder)
                    for folder in saved
                    if isinstance(folder, str) and folder.strip()
                ]
    except (OSError, ValueError, TypeError):
        folders = []

    if not folders:
        folders = default_search_folders()

    accessible = []
    unavailable = []
    for folder in folders:
        if not os.path.isdir(folder):
            unavailable.append(folder)
            continue
        try:
            with os.scandir(folder):
                pass
            accessible.append(folder)
        except OSError:
            unavailable.append(folder)

    return accessible, unavailable


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/search", methods=["POST"])
def search():

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "results": [],
            "message": "Request must contain a JSON object."
        }), 400

    query = data.get("query", "")
    if not isinstance(query, str):
        query = ""
    query = query.strip()

    if not query:
        return jsonify({
            "success": False,
            "results": [],
            "message": "Please enter a search query."
        }), 400

    print("\nWeb search:", query)

    try:
        accessible_folders, unavailable_folders = resolve_search_folders()

        if not accessible_folders:
            return jsonify({
                "success": True,
                "results": [],
                "count": 0,
                "message": (
                    "No accessible folders were found. Findly will use your common "
                    "desktop folders automatically when they exist."
                ),
                "unavailable_folders": unavailable_folders,
                "folders_used": [],
            })

        results = search_findly(query, accessible_folders)

        formatted_results = []
        for result in results:
            if isinstance(result, tuple):
                formatted_results.append({
                    "data": [str(value) for value in result]
                })
            else:
                formatted_results.append({
                    "data": [str(result)]
                })

        return jsonify({
            "success": True,
            "results": formatted_results,
            "count": len(formatted_results),
            "unavailable_folders": unavailable_folders,
            "folders_used": accessible_folders,
        })

    except Exception as error:

        print("Search error:", error)

        return jsonify({
            "success": False,
            "results": [],
            "message": str(error)
        }), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", debug=False)