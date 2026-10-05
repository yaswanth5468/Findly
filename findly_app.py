import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

from file_watcher import start_watcher
from natural_language_engine import search_findly
from scanner import scan_folder
from document_index import add_folder_to_index
from voice_assistant import VoiceAssistant


selected_folders = []
pending_folders = set()
watchers = []
voice_assistant = VoiceAssistant()
automatic_refresh_running = False


# ============================================================
# FOLDER MANAGEMENT
# ============================================================

def add_folder():

    folder = filedialog.askdirectory()

    if folder:

        folder = os.path.abspath(folder)

        if folder in selected_folders or folder in pending_folders:
            messagebox.showinfo(
                "Folder already added",
                "This folder is already included or currently being scanned."
            )
            return

        if not os.path.isdir(folder):
            messagebox.showerror(
                "Folder not found",
                "The selected folder is no longer available on this PC."
            )
            return

        if not messagebox.askyesno(
            "Allow Findly to access this folder?",
            "Findly will scan this folder and its subfolders, read file "
            "metadata and supported document contents for search, locally "
            "analyze photos for visual/person search, and monitor changes "
            "while the app is open. Person detection may download its model "
            "once; your files stay on this PC. Continue?"
        ):
            set_status("Folder access was not granted.")
            return

        try:
            with os.scandir(folder):
                pass
        except PermissionError as error:
            messagebox.showerror(
                "Folder access denied",
                f"Findly cannot read this folder:\n{folder}\n\n{error}"
            )
            return
        except OSError as error:
            messagebox.showerror(
                "Folder unavailable",
                f"Findly could not access this folder:\n{folder}\n\n{error}"
            )
            return

        pending_folders.add(folder)
        set_status(f"Scanning and indexing: {folder}", "#1d4ed8")
        search_button.config(state="disabled")
        folder_button.config(state="disabled")
        refresh_button.config(state="disabled")

        def index_folder():
            try:
                add_folder_to_index(folder)
                scan_summary = scan_folder(folder)
                from image_indexer import index_image_folder

                new_images = index_image_folder(folder)
                observer = start_watcher(folder)
            except Exception as error:
                def report_failure(error=error):
                    pending_folders.discard(folder)
                    search_button.config(state="normal")
                    folder_button.config(state="normal")
                    refresh_button.config(state="normal")
                    set_status("Folder scan failed.", "#b22222")
                    messagebox.showerror(
                        "Folder indexing failed",
                        f"Findly could not finish accessing the folder:\n"
                        f"{folder}\n\n{error}"
                    )

                root.after(0, report_failure)
                return

            def report_success():
                pending_folders.discard(folder)
                selected_folders.append(folder)
                watchers.append(observer)
                search_button.config(state="normal")
                folder_button.config(state="normal")
                refresh_button.config(state="normal")
                scanned = scan_summary["scanned"]
                skipped = scan_summary["skipped"]
                status = (
                    f"Scan complete: {scanned} files indexed; "
                    f"{new_images} new photos indexed."
                )
                if skipped:
                    status += f" {skipped} files could not be read."
                set_status(
                    status,
                    "#9a6700" if skipped else "#006400"
                )
                print("Added folder:", folder)
                print("File scan summary:", scan_summary)
                print("Real-time monitoring started.")
                print("Selected folders:", selected_folders)

            root.after(0, report_success)

        threading.Thread(
            target=index_folder,
            daemon=True
        ).start()


def refresh_index():

    if not selected_folders:

        print(
            "Please add a folder first."
        )

        return

    inaccessible = []

    for folder in selected_folders:
        if not os.path.isdir(folder):
            inaccessible.append(folder)
            continue

        try:
            with os.scandir(folder):
                pass
            add_folder_to_index(folder)
            scan_folder(folder)
            from image_indexer import index_image_folder

            index_image_folder(folder)
        except OSError as error:
            inaccessible.append(f"{folder} ({error})")
        except Exception as error:
            inaccessible.append(f"{folder} (indexing failed: {error})")

    if inaccessible:
        messagebox.showwarning(
            "Some folders could not be refreshed",
            "These folders are missing or inaccessible:\n\n"
            + "\n".join(inaccessible)
        )
        set_status("Index refreshed with inaccessible folders.", "#b22222")
    else:
        set_status("Index refreshed successfully.", "#006400")
        print("Document and file indexes refreshed.")


# ============================================================
# RESULT MANAGEMENT
# ============================================================

def clear_results():

    for widget in result_frame.winfo_children():

        widget.destroy()


def set_status(message, color="black"):

    if "status_label" in globals():

        status_label.config(
            text=message,
            fg=color
        )


def get_result_path(result):

    if not isinstance(result, (tuple, list)):
        return None

    if len(result) == 2:
        path = result[0]
    elif len(result) == 4:
        path = result[1]
    elif len(result) == 5 and is_document_result(result):
        path = result[1]
    elif len(result) == 5:
        path = result[3]
    elif len(result) >= 7:
        path = result[3]
    else:
        return None

    return path if isinstance(path, str) else None


def is_document_result(result):

    return (
        isinstance(result, (tuple, list))
        and len(result) == 5
        and str(result[0]).upper() in {"PDF", "DOCX", "TXT"}
        and isinstance(result[1], str)
        and os.path.splitext(result[1])[1].lower()
        in {".pdf", ".docx", ".txt"}
    )


def open_file(path):

    if not os.path.isfile(path):
        messagebox.showwarning(
            "File no longer available",
            f"This file is not present on this PC:\n{path}\n\n"
            "Refresh the index to update search results."
        )
        return

    try:

        os.startfile(path)

    except OSError as error:
        messagebox.showerror(
            "Could not open file",
            f"Windows could not open this file:\n{path}\n\n{error}"
        )


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

    for path, score in results:

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

        set_status("Please type a search query.", "#b22222")
        return

    clear_results()
    result_count_label.config(text="")

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
        set_status("Please add a folder first.", "#b22222")
        return

    def run_search():

        print(
            "\nSearching:",
            query
        )

        root.after(
            0,
            lambda: set_status("Searching...")
        )

        accessible_folders = []
        unavailable_folders = []

        for folder in selected_folders:
            if not os.path.isdir(folder):
                unavailable_folders.append(folder)
                continue

            try:
                with os.scandir(folder):
                    pass
                accessible_folders.append(folder)
            except OSError:
                unavailable_folders.append(folder)

        if accessible_folders:
            try:
                indexed_results = search_findly(
                    query,
                    accessible_folders
                )
            except Exception as error:
                def report_search_error(error=error):
                    set_status("Search failed.", "#b22222")
                    messagebox.showerror(
                        "Search failed",
                        f"Findly could not complete the search.\n\n{error}"
                    )

                root.after(
                    0,
                    report_search_error
                )
                return
        else:
            indexed_results = []

        results = []
        missing_file_count = 0

        for result in indexed_results:
            path = get_result_path(result)
            if path is None or os.path.isfile(path):
                results.append(result)
            else:
                missing_file_count += 1

        def update_ui():

            if not results:

                search_type_label.config(
                    text="Search type: No results"
                )

                tk.Label(
                    result_frame,
                    text=(
                        "No matching files are currently available."
                        if missing_file_count
                        else "No matching files found"
                    ),
                    font=("Arial", 12)
                ).pack(
                    pady=20
                )

            else:

                first_result = results[0]

                if is_document_result(first_result):

                    show_document_results(results)

                elif (
                    isinstance(first_result, tuple)
                    and len(first_result) == 5
                ):

                    show_combined_results(
                        results
                    )

                elif (
                    isinstance(first_result, tuple)
                    and len(first_result) == 2
                ):

                    show_image_results(
                        results
                    )

                elif (
                    isinstance(first_result, tuple)
                    and len(first_result) == 4
                ):

                    show_document_results(
                        results
                    )

                else:

                    show_file_results(
                        results
                    )

            result_count_label.config(
                text="Results found: "
                + str(len(results))
            )

            if (
                results
                and not missing_file_count
                and not unavailable_folders
            ):
                set_status("Search complete. All listed files are present.", "#006400")
                if voice_assistant.is_speaking_supported():
                    voice_assistant.speak_results_summary(query, results)
            elif results:
                notices = []
                if missing_file_count:
                    notices.append(
                        f"{missing_file_count} indexed file(s) are no longer "
                        "on this PC"
                    )
                if unavailable_folders:
                    notices.append(
                        f"{len(unavailable_folders)} selected folder(s) are "
                        "missing or inaccessible"
                    )
                set_status(
                    "; ".join(notices) + ". Refresh the index.",
                    "#9a6700"
                )
                if voice_assistant.is_speaking_supported():
                    voice_assistant.speak_results_summary(query, results)
            else:
                if missing_file_count:
                    set_status(
                        f"{missing_file_count} indexed file(s) are no longer "
                        "on this PC. Refresh the index.",
                        "#9a6700"
                    )
                elif unavailable_folders:
                    set_status(
                        "Selected folders are missing or inaccessible.",
                        "#b22222"
                    )
                else:
                    set_status("No results found.", "#b22222")

        root.after(
            0,
            update_ui
        )

    threading.Thread(
        target=run_search,
        daemon=True
    ).start()


def voice_search():

    if not voice_assistant.is_listening_supported():

        set_status("Voice input is unavailable on this device.", "#b22222")
        return

    query = voice_assistant.listen_for_query()

    if not query:

        set_status("Could not hear the query. Please try again.", "#b22222")
        return

    search_entry.delete(
        0,
        tk.END
    )
    search_entry.insert(
        0,
        query
    )
    set_status(f"Voice query: {query}")
    search()


# ============================================================
# MAIN WINDOW
# ============================================================

root = tk.Tk()

root.title(
    "Findly"
)

root.geometry(
    "900x760"
)

root.minsize(
    800,
    600
)

root.configure(
    bg="#f3f6fb"
)

try:
    import tkinter.ttk as ttk
except ImportError:
    ttk = None

if ttk is not None:
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass

    style.configure(
        "Findly.TFrame",
        background="#f3f6fb"
    )
    style.configure(
        "Findly.TLabel",
        background="#f3f6fb",
        foreground="#1d2433",
        font=("Segoe UI", 10)
    )
    style.configure(
        "Findly.TEntry",
        fieldbackground="#ffffff",
        borderwidth=1,
        padding=8
    )
    style.configure(
        "Findly.TButton",
        background="#dfe9ff",
        foreground="#1d2433",
        borderwidth=0,
        padding=(12, 9),
        font=("Segoe UI", 10, "bold")
    )
    style.map(
        "Findly.TButton",
        background=[
            ("active", "#cfe0ff"),
            ("pressed", "#bfd7ff")
        ]
    )


# ============================================================
# TITLE
# ============================================================

main_container = tk.Frame(
    root,
    bg="#f3f6fb",
    padx=20,
    pady=20
)

main_container.pack(
    fill="both",
    expand=True
)

title = tk.Label(
    main_container,
    text="Findly",
    font=("Segoe UI", 28, "bold"),
    fg="#1d4ed8",
    bg="#f3f6fb"
)

title.pack(
    pady=(0, 12)
)


# ============================================================
# SEARCH BAR
# ============================================================

search_frame = tk.Frame(
    main_container,
    bg="#f3f6fb"
)

search_frame.pack(
    fill="x",
    pady=(0, 12)
)

search_entry = tk.Entry(
    search_frame,
    font=("Segoe UI", 12),
    bd=1,
    relief="solid",
    width=1
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
    font=("Segoe UI", 10, "bold"),
    bg="#dfe9ff",
    fg="#1d2433",
    bd=0,
    padx=16,
    pady=10,
    activebackground="#cfe0ff",
    command=search
)

search_button.pack(
    side="right"
)

voice_button = tk.Button(
    search_frame,
    text="🎤 VOICE",
    font=("Segoe UI", 10, "bold"),
    bg="#dfe9ff",
    fg="#1d2433",
    bd=0,
    padx=16,
    pady=10,
    activebackground="#cfe0ff",
    command=voice_search
)

voice_button.pack(
    side="right",
    padx=(0, 10)
)


# ============================================================
# ADD FOLDER BUTTON
# ============================================================

folder_button = tk.Button(
    search_frame,
    text="ADD FOLDER",
    font=("Segoe UI", 10, "bold"),
    bg="#e8f7ed",
    fg="#1d3f2a",
    bd=0,
    padx=14,
    pady=10,
    activebackground="#d4efe0",
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
    font=("Segoe UI", 10, "bold"),
    bg="#fff1d6",
    fg="#5a3c00",
    bd=0,
    padx=14,
    pady=10,
    activebackground="#ffe6ae",
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
    main_container,
    text="",
    font=("Segoe UI", 10, "bold"),
    fg="#2f3b52",
    bg="#f3f6fb"
)

search_type_label.pack(
    pady=(0, 6)
)


# ============================================================
# RESULT COUNT
# ============================================================

result_count_label = tk.Label(
    main_container,
    text="",
    font=("Segoe UI", 10),
    fg="#445067",
    bg="#f3f6fb"
)

result_count_label.pack(
    pady=(0, 6)
)

status_label = tk.Label(
    main_container,
    text="Ready",
    font=("Segoe UI", 10),
    fg="#222222",
    bg="#f3f6fb"
)

status_label.pack(
    pady=(0, 10)
)


# ============================================================
# RESULT CONTAINER
# ============================================================

result_container = tk.Frame(
    main_container,
    bg="#f3f6fb",
    bd=0
)

result_container.pack(
    fill="both",
    expand=True
)


# ============================================================
# RESULT CANVAS
# ============================================================

result_canvas = tk.Canvas(
    result_container,
    bg="#f3f6fb",
    highlightthickness=0
)


# ============================================================
# SCROLLBAR
# ============================================================

result_scrollbar = tk.Scrollbar(
    result_container,
    orient="vertical",
    command=result_canvas.yview,
    troughcolor="#f3f6fb"
)


# ============================================================
# RESULT FRAME
# ============================================================

result_frame = tk.Frame(
    result_canvas,
    bg="#f3f6fb"
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

    global automatic_refresh_running

    if selected_folders and not automatic_refresh_running:
        automatic_refresh_running = True
        folders_to_refresh = tuple(selected_folders)

        def refresh_indexes():
            inaccessible = []

            for folder in folders_to_refresh:
                if not os.path.isdir(folder):
                    inaccessible.append(folder)
                    continue

                try:
                    with os.scandir(folder):
                        pass
                    add_folder_to_index(folder)
                    scan_folder(folder)
                except Exception as error:
                    inaccessible.append(f"{folder} ({error})")

            def finish_refresh():
                global automatic_refresh_running
                automatic_refresh_running = False

                if inaccessible:
                    set_status(
                        "Automatic refresh skipped missing or inaccessible "
                        "folders.",
                        "#9a6700"
                    )
                    print(
                        "Folders skipped during automatic refresh:",
                        inaccessible
                    )
                else:
                    set_status("Indexes refreshed.", "#006400")
                    print("Automatic file and document refresh completed.")

            root.after(0, finish_refresh)

        threading.Thread(
            target=refresh_indexes,
            daemon=True
        ).start()

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
