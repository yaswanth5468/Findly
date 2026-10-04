from flask import Flask, render_template, request, jsonify

from natural_language_engine import search_findly


app = Flask(__name__)


# Temporary folder for testing
SEARCH_FOLDER = r"C:\Users\admin\Desktop\test findly"


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/search", methods=["POST"])
def search():

    data = request.get_json()

    query = data.get("query", "").strip()

    if not query:
        return jsonify({
            "success": False,
            "results": [],
            "message": "Please enter a search query."
        })

    print("\nWeb search:", query)

    try:

        results = search_findly(
            query,
            [SEARCH_FOLDER]
        )

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
            "count": len(formatted_results)
        })

    except Exception as error:

        print("Search error:", error)

        return jsonify({
            "success": False,
            "results": [],
            "message": str(error)
        })


if __name__ == "__main__":
    app.run(debug=True)