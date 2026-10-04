import os
import tkinter as tk
from tkinter import filedialog

from file_watcher import start_watcher
from natural_language_engine import search_findly
from scanner import scan_folder
from document_index import add_folder_to_index


selected_folders = []
watchers = []


# ============================================================
# FOLDER MANAGEMENT
# ============================================================

def add_folder():

    folder = filedialog.askdirectory()

    if folder:

        if folder not in selected_folders:

            selected_folders.append(folder)

            # Initial indexing
            add_folder_to_index(folder)

            scan_folder(folder)

            # Start real-time watcher
            observer = start_watcher(
                folder
            )

            watchers.append(
                observer
            )

            print(
                "Added folder:",
                folder
            )

            print(
                "Folder scanned successfully."
            )

            print(
                "Real-time monitoring started."
            )

            print(
                "Selected folders:",
                selected_folders
            )

        else:

            print(
                "Folder already added."
            )


def refresh_index():

    if not selected_folders:

        print(
            "Please add a folder first."
        )

        return

    for folder in selected_folders:

        add_folder_to_index(
            folder
        )

    print(
        "Document index refreshed."
    )


# ============================================================
# RESULT MANAGEMENT
# ============================================================

def clear_results():

    for widget in result_frame.winfo_children():

        widget.destroy()


def open_file(path):

    try:

        os.startfile(path)

    except:

        pass


# ============================================================
# IMAGE RESULTS
# ============================================================

def show_image_results(results):

    search_type_label.config(
        text="Search type: AI Photo Search"
    )

    if not results:

        tk.Label(
            result_frame,
            text="No strong matches found",
            font=("Arial", 12)
        ).pack(
            pady=20
        )

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

        name = os.path.basename(
            path
        )

        tk.Label(
            frame,
            text=name,
            font=("Arial", 11, "bold")
        ).pack(
            anchor="w"
        )

        tk.Label(
            frame,
            text="Match: "
            + str(
                round(score, 4)
            )
        ).pack(
            anchor="w"
        )

        tk.Button(
            frame,
            text="OPEN",
            command=lambda p=path: open_file(p)
        ).pack(
            anchor="e"
        )


# ============================================================
# COMBINED RESULTS
# ============================================================

def show_combined_results(results):

    search_type_label.config(
        text="Search type: Combined AI + File Search"
    )

    if not results:

        tk.Label(
            result_frame,
            text="No matching files found",
            font=("Arial", 12)
        ).pack(
            pady=20
        )

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
        ).pack(
            anchor="w"
        )

        tk.Label(
            frame,
            text="Type: "
            + extension
        ).pack(
            anchor="w"
        )

        tk.Label(
            frame,
            text="Size: "
            + str(
                round(size, 2)
            )
            + " MB"
        ).pack(
            anchor="w"
        )

        tk.Label(
            frame,
            text="Match: "
            + str(
                round(score, 4)
            )
        ).pack(
            anchor="w"
        )

        tk.Label(
            frame,
            text=path,
            wraplength=700
        ).pack(
            anchor="w"
        )

        tk.Button(
            frame,
            text="OPEN",
            command=lambda p=path: open_file(p)
        ).pack(
            anchor="e"
        )


# ============================================================
# NORMAL FILE RESULTS
# ============================================================

def show_file_results(results):

    search_type_label.config(
        text="Search type: File Search"
    )

    if not results:

        tk.Label(
            result_frame,
            text="No files found",
            font=("Arial", 12)
        ).pack(
            pady=20
        )

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
        ).pack(
            anchor="w"
        )

        tk.Label(
            frame,
            text="Type: "
            + extension
        ).pack(
            anchor="w"
        )

        tk.Label(
            frame,
            text="Size: "
            + str(
                round(size, 2)
            )
            + " MB"
        ).pack(
            anchor="w"
        )

        tk.Label(
            frame,
            text="Location: "
            + path,
            wraplength=700
        ).pack(
            anchor="w"
        )

        tk.Label(
            frame,
            text="Created: "
            + str(created)
        ).pack(
            anchor="w"
        )

        tk.Label(
            frame,
            text="Modified: "
            + str(modified)
        ).pack(
            anchor="w"
        )

        if taken:

            tk.Label(
                frame,
                text="Taken: "
                + str(taken)
            ).pack(
                anchor="w"
            )

        tk.Button(
            frame,
            text="OPEN",
            command=lambda p=path: open_file(p)
        ).pack(
            anchor="e"
        )


# ============================================================
# DOCUMENT RESULTS
# ============================================================

def show_document_results(results):

    search_type_label.config(
        text="Search type: Document Content Search"
    )

    if not results:

        tk.Label(
            result_frame,
            text="No matching documents found",
            font=("Arial", 12)
        ).pack(
            pady=20
        )

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
        ).pack(
            anchor="w"
        )

        tk.Label(
            frame,
            text="Type: "
            + file_type
        ).pack(
            anchor="w"
        )

        if location:

            if file_type == "PDF":

                location_text = (
                    "Page: "
                    + str(location)
                )

            else:

                location_text = (
                    "Paragraph: "
                    + str(location)
                )

            tk.Label(
                frame,
                text=location_text
            ).pack(
                anchor="w"
            )

        tk.Label(
            frame,
            text="Match:",
            font=("Arial", 10, "bold")
        ).pack(
            anchor="w",
            pady=(8, 0)
        )

        tk.Label(
            frame,
            text=snippet,
            wraplength=750,
            justify="left"
        ).pack(
            anchor="w"
        )

        tk.Button(
            frame,
            text="OPEN",
            command=lambda p=path: open_file(p)
        ).pack(
            anchor="e"
        )


# ============================================================
# MAIN SEARCH
# ============================================================

def search():

    query = search_entry.get().strip()

    if not query:

        return

    clear_results()

    result_count_label.config(
        text=""
    )

    if not selected_folders:

        tk.Label(
            result_frame,
            text="Please add a folder first.",
            font=("Arial", 12)
        ).pack(
            pady=20
        )

        result_count_label.config(
            text="Results found: 0"
        )

        return

    print(
        "\nSearching:",
        query
    )

    # ========================================================
    # NATURAL LANGUAGE SEARCH
    # ========================================================

    results = search_findly(
        query,
        selected_folders
    )

    # ========================================================
    # DISPLAY RESULTS
    # ========================================================

    if not results:

        search_type_label.config(
            text="Search type: No results"
        )

        tk.Label(
            result_frame,
            text="No matching files found",
            font=("Arial", 12)
        ).pack(
            pady=20
        )

    else:

        first_result = results[0]

        # ----------------------------------------------------
        # Combined result
        # Format:
        # name, extension, size, path, score
        # ----------------------------------------------------

        if (
            isinstance(first_result, tuple)
            and len(first_result) == 5
        ):

            show_combined_results(
                results
            )

        # ----------------------------------------------------
        # Image result
        # Format:
        # path, score
        # ----------------------------------------------------

        elif (
            isinstance(first_result, tuple)
            and len(first_result) == 2
        ):

            show_image_results(
                results
            )

        # ----------------------------------------------------
        # Document result
        # Format:
        # type, path, location, snippet
        # ----------------------------------------------------

        elif (
            isinstance(first_result, tuple)
            and len(first_result) == 4
        ):

            show_document_results(
                results
            )

        # ----------------------------------------------------
        # Normal file result
        # ----------------------------------------------------

        else:

            show_file_results(
                results
            )

    result_count_label.config(
        text="Results found: "
        + str(len(results))
    )


# ============================================================
# MAIN WINDOW
# ============================================================

root = tk.Tk()

root.title(
    "Findly"
)

root.geometry(
    "850x700"
)


# ============================================================
# TITLE
# ============================================================

title = tk.Label(
    root,
    text="Findly",
    font=("Arial", 24, "bold")
)

title.pack(
    pady=15
)


# ============================================================
# SEARCH BAR
# ============================================================

search_frame = tk.Frame(
    root
)

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


# ============================================================
# ADD FOLDER BUTTON
# ============================================================

folder_button = tk.Button(
    search_frame,
    text="ADD FOLDER",
    font=("Arial", 12),
    command=add_folder
)

folder_button.pack(
    side="right"
)


# ============================================================
# REFRESH BUTTON
# ============================================================

refresh_button = tk.Button(
    search_frame,
    text="REFRESH INDEX",
    font=("Arial", 12),
    command=refresh_index
)

refresh_button.pack(
    side="right",
    padx=(10, 0)
)


# ============================================================
# ENTER KEY
# ============================================================

search_entry.bind(
    "<Return>",
    lambda event: search()
)


# ============================================================
# SEARCH TYPE
# ============================================================

search_type_label = tk.Label(
    root,
    text="",
    font=("Arial", 11)
)

search_type_label.pack(
    pady=10
)


# ============================================================
# RESULT COUNT
# ============================================================

result_count_label = tk.Label(
    root,
    text="",
    font=("Arial", 10)
)

result_count_label.pack(
    pady=2
)


# ============================================================
# RESULT CONTAINER
# ============================================================

result_container = tk.Frame(
    root
)

result_container.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)


# ============================================================
# RESULT CANVAS
# ============================================================

result_canvas = tk.Canvas(
    result_container
)


# ============================================================
# SCROLLBAR
# ============================================================

result_scrollbar = tk.Scrollbar(
    result_container,
    orient="vertical",
    command=result_canvas.yview
)


# ============================================================
# RESULT FRAME
# ============================================================

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


# ============================================================
# AUTOMATIC INDEX REFRESH
# ============================================================

def automatic_index_refresh():

    if selected_folders:

        print(
            "\nAutomatic index refresh started."
        )

        for folder in selected_folders:

            add_folder_to_index(
                folder
            )

        print(
            "Automatic index refresh completed."
        )

    root.after(
        60000,
        automatic_index_refresh
    )


root.after(
    60000,
    automatic_index_refresh
)


# ============================================================
# CLEAN SHUTDOWN
# ============================================================

def close_findly():

    print(
        "\nClosing Findly..."
    )

    for observer in watchers:

        observer.stop()

    for observer in watchers:

        observer.join()

    print(
        "All watchers stopped."
    )

    root.destroy()


root.protocol(
    "WM_DELETE_WINDOW",
    close_findly
)


# ============================================================
# START FINDLY
# ============================================================

root.mainloop()
