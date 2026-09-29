import os
import tkinter as tk
from tkinter import filedialog

from image_engine import search_images
from file_engine import search_files
from combined_engine import search_combined
from document_engine import search_documents


selected_folders = []


def add_folder():
    folder = filedialog.askdirectory()

    if folder:
        selected_folders.append(folder)
        print("Added folder:", folder)


ai_words = [
    "person",
    "people",
    "man",
    "woman",
    "car",
    "dog",
    "cat",
    "food",
    "family",
    "college",
    "laptop"
]


def is_combined_search(query):
    query = query.lower()

    has_visual = False

    for word in ai_words:
        if word in query:
            has_visual = True
            break

    has_photo = (
        "photo" in query
        or "picture" in query
        or "image" in query
    )

    has_filter = (
        "bigger" in query
        or "larger" in query
        or "smaller" in query
        or "over" in query
        or "under" in query
        or "from" in query
        or "2025" in query
        or "2026" in query
    )

    return has_visual and has_photo and has_filter


def is_ai_search(query):
    query = query.lower()

    if (
        "photo" in query
        or "picture" in query
        or "image" in query
    ):
        return True

    for word in ai_words:
        if word in query:
            return True

    return False


def is_document_search(query):
    query = query.lower()

    document_words = [
        "document",
        "documents",
        "pdf",
        "word",
        "docx",
        "text file",
        "txt"
    ]

    for word in document_words:
        if word in query:
            return True

    return False


def clear_results():
    for widget in result_frame.winfo_children():
        widget.destroy()


def open_file(path):
    try:
        os.startfile(path)
    except:
        pass


def show_image_results(results):
    search_type_label.config(
        text="Search type: AI Photo Search"
    )

    if not results:
        tk.Label(
            result_frame,
            text="No strong matches found",
            font=("Arial", 12)
        ).pack(pady=20)

        return

    for path, score in results[:6]:

        frame = tk.Frame(
            result_frame,
            bd=1,
            relief="solid",
            padx=10,
            pady=10
        )

        frame.pack(
            fill="x",
            padx=10,
            pady=5
        )

        name = os.path.basename(path)

        tk.Label(
            frame,
            text=name,
            font=("Arial", 11, "bold")
        ).pack(anchor="w")

        tk.Label(
            frame,
            text="Match: " + str(round(score, 4))
        ).pack(anchor="w")

        tk.Button(
            frame,
            text="OPEN",
            command=lambda p=path: open_file(p)
        ).pack(anchor="e")


def show_combined_results(results):
    search_type_label.config(
        text="Search type: Combined AI + File Search"
    )

    if not results:
        tk.Label(
            result_frame,
            text="No matching files found",
            font=("Arial", 12)
        ).pack(pady=20)

        return

    for result in results:

        name = result[0]
        extension = result[1]
        size = result[2]
        path = result[3]
        score = result[4]

        frame = tk.Frame(
            result_frame,
            bd=1,
            relief="solid",
            padx=10,
            pady=10
        )

        frame.pack(
            fill="x",
            padx=10,
            pady=5
        )

        tk.Label(
            frame,
            text=name,
            font=("Arial", 11, "bold")
        ).pack(anchor="w")

        tk.Label(
            frame,
            text="Type: " + extension
        ).pack(anchor="w")

        tk.Label(
            frame,
            text="Size: " + str(round(size, 2)) + " MB"
        ).pack(anchor="w")

        tk.Label(
            frame,
            text="Match: " + str(round(score, 4))
        ).pack(anchor="w")

        tk.Label(
            frame,
            text=path,
            wraplength=700
        ).pack(anchor="w")

        tk.Button(
            frame,
            text="OPEN",
            command=lambda p=path: open_file(p)
        ).pack(anchor="e")


def show_file_results(results):
    search_type_label.config(
        text="Search type: File Search"
    )

    if not results:
        tk.Label(
            result_frame,
            text="No files found",
            font=("Arial", 12)
        ).pack(pady=20)

        return

    for result in results:

        name = result[0]
        extension = result[1]
        size = result[2]
        path = result[3]
        created = result[4]
        modified = result[5]
        taken = result[6]

        frame = tk.Frame(
            result_frame,
            bd=1,
            relief="solid",
            padx=10,
            pady=10
        )

        frame.pack(
            fill="x",
            padx=10,
            pady=5
        )

        tk.Label(
            frame,
            text=name,
            font=("Arial", 11, "bold")
        ).pack(anchor="w")

        tk.Label(
            frame,
            text="Type: " + extension
        ).pack(anchor="w")

        tk.Label(
            frame,
            text="Size: " + str(round(size, 2)) + " MB"
        ).pack(anchor="w")

        tk.Label(
            frame,
            text="Location: " + path,
            wraplength=700
        ).pack(anchor="w")

        tk.Label(
            frame,
            text="Created: " + str(created)
        ).pack(anchor="w")

        tk.Label(
            frame,
            text="Modified: " + str(modified)
        ).pack(anchor="w")

        if taken:
            tk.Label(
                frame,
                text="Taken: " + str(taken)
            ).pack(anchor="w")

        tk.Button(
            frame,
            text="OPEN",
            command=lambda p=path: open_file(p)
        ).pack(anchor="e")


def show_document_results(results):
    search_type_label.config(
        text="Search type: Document Content Search"
    )

    if not results:
        tk.Label(
            result_frame,
            text="No matching documents found",
            font=("Arial", 12)
        ).pack(pady=20)

        return

    for result in results:

        file_type = result[0]
        path = result[1]
        location = result[2]
        snippet = result[3]

        frame = tk.Frame(
            result_frame,
            bd=1,
            relief="solid",
            padx=10,
            pady=10
        )

        frame.pack(
            fill="x",
            padx=10,
            pady=5
        )

        tk.Label(
            frame,
            text=os.path.basename(path),
            font=("Arial", 11, "bold")
        ).pack(anchor="w")

        tk.Label(
            frame,
            text="Type: " + file_type
        ).pack(anchor="w")

        if location:
            if file_type == "PDF":
                location_text = "Page: " + str(location)
            else:
                location_text = "Paragraph: " + str(location)

            tk.Label(
                frame,
                text=location_text
            ).pack(anchor="w")

        tk.Label(
            frame,
            text="Match:",
            font=("Arial", 10, "bold")
        ).pack(anchor="w", pady=(8, 0))

        tk.Label(
            frame,
            text=snippet,
            wraplength=750,
            justify="left"
        ).pack(anchor="w")

        tk.Button(
            frame,
            text="OPEN",
            command=lambda p=path: open_file(p)
        ).pack(anchor="e")


def search():
    query = search_entry.get().strip()

    if not query:
        return

    clear_results()

    result_count_label.config(
        text=""
    )

    if is_combined_search(query):

        results = search_combined(query)

        show_combined_results(results)

    elif is_document_search(query):

        folder = os.path.expanduser("~")

        results = search_documents(
            query,
            folder
        )

        show_document_results(results)

    elif is_ai_search(query):

        results = search_images(query)

        show_image_results(results)

    else:

        results = search_files(query)

        show_file_results(results)

    result_count_label.config(
        text="Results found: " + str(len(results))
    )


root = tk.Tk()

root.title("Findly")

root.geometry("850x700")


title = tk.Label(
    root,
    text="Findly",
    font=("Arial", 24, "bold")
)

title.pack(pady=15)


search_frame = tk.Frame(root)

search_frame.pack(
    fill="x",
    padx=20
)


search_entry = tk.Entry(
    search_frame,
    font=("Arial", 14)
)

search_entry.pack(
    side="left",
    fill="x",
    expand=True,
    padx=(0, 10)
)


search_button = tk.Button(
    search_frame,
    text="SEARCH",
    font=("Arial", 12),
    command=search
)

search_button.pack(
    side="right"
)


folder_button = tk.Button(
    search_frame,
    text="ADD FOLDER",
    font=("Arial", 12),
    command=add_folder
)

folder_button.pack(
    side="right"
)


search_entry.bind(
    "<Return>",
    lambda event: search()
)


search_type_label = tk.Label(
    root,
    text="",
    font=("Arial", 11)
)

search_type_label.pack(
    pady=10
)


result_count_label = tk.Label(
    root,
    text="",
    font=("Arial", 10)
)

result_count_label.pack(
    pady=2
)


result_container = tk.Frame(root)

result_container.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)


result_canvas = tk.Canvas(
    result_container
)


result_scrollbar = tk.Scrollbar(
    result_container,
    orient="vertical",
    command=result_canvas.yview
)


result_frame = tk.Frame(
    result_canvas
)


result_frame.bind(
    "<Configure>",
    lambda e: result_canvas.configure(
        scrollregion=result_canvas.bbox("all")
    )
)


result_canvas.create_window(
    (0, 0),
    window=result_frame,
    anchor="nw"
)


result_canvas.configure(
    yscrollcommand=result_scrollbar.set
)


result_canvas.pack(
    side="left",
    fill="both",
    expand=True
)


result_scrollbar.pack(
    side="right",
    fill="y"
)


root.mainloop()