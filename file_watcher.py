import os
import time
import threading

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from document_index import add_folder_to_index

from image_indexer import (
    update_image,
    remove_image
)


DOCUMENT_EXTENSIONS = {
    ".txt",
    ".pdf",
    ".docx"
}

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
    ".tif",
    ".tiff"
}


class FindlyFileWatcher(FileSystemEventHandler):

    def __init__(self, folder):

        self.folder = folder

        self.document_timer = None

        self.lock = threading.Lock()

    def get_extension(self, path):

        return os.path.splitext(
            path
        )[1].lower()

    def schedule_document_refresh(self):

        with self.lock:

            if self.document_timer is not None:
                self.document_timer.cancel()

            self.document_timer = threading.Timer(
                2,
                self.refresh_documents
            )

            self.document_timer.start()

    def refresh_documents(self):

        print("\nDocument changes settled.")

        print(
            "Updating document index..."
        )

        add_folder_to_index(
            self.folder
        )

        print(
            "Document index updated."
        )

    def handle_created(self, path):

        extension = self.get_extension(
            path
        )

        if extension in DOCUMENT_EXTENSIONS:

            print(
                "\nNew document detected:",
                path
            )

            self.schedule_document_refresh()

        elif extension in IMAGE_EXTENSIONS:

            print(
                "\nNew image detected:",
                path
            )

            update_image(
                path
            )

    def handle_modified(self, path):

        extension = self.get_extension(
            path
        )

        if extension in DOCUMENT_EXTENSIONS:

            print(
                "\nDocument modified:",
                path
            )

            self.schedule_document_refresh()

        elif extension in IMAGE_EXTENSIONS:

            print(
                "\nImage modified:",
                path
            )

            update_image(
                path
            )

    def handle_deleted(self, path):

        extension = self.get_extension(
            path
        )

        if extension in DOCUMENT_EXTENSIONS:

            print(
                "\nDocument deleted:",
                path
            )

            self.schedule_document_refresh()

        elif extension in IMAGE_EXTENSIONS:

            print(
                "\nImage deleted:",
                path
            )

            remove_image(
                path
            )

    def handle_moved(self, old_path, new_path):

        old_extension = self.get_extension(
            old_path
        )

        new_extension = self.get_extension(
            new_path
        )

        if old_extension in IMAGE_EXTENSIONS:

            remove_image(
                old_path
            )

        if new_extension in IMAGE_EXTENSIONS:

            update_image(
                new_path
            )

        if (
            old_extension in DOCUMENT_EXTENSIONS
            or
            new_extension in DOCUMENT_EXTENSIONS
        ):

            self.schedule_document_refresh()

    def on_created(self, event):

        if not event.is_directory:

            self.handle_created(
                event.src_path
            )

    def on_modified(self, event):

        if not event.is_directory:

            self.handle_modified(
                event.src_path
            )

    def on_deleted(self, event):

        if not event.is_directory:

            self.handle_deleted(
                event.src_path
            )

    def on_moved(self, event):

        if not event.is_directory:

            self.handle_moved(
                event.src_path,
                event.dest_path
            )


def start_watcher(folder):

    event_handler = FindlyFileWatcher(
        folder
    )

    observer = Observer()

    observer.schedule(
        event_handler,
        folder,
        recursive=True
    )

    observer.start()

    print(
        "Watching folder:",
        folder
    )

    return observer