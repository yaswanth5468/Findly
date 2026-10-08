import json
import sqlite3
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import file_engine
import image_engine
import natural_language_engine
import person_detector
import query_parser
import scanner
import torch
import app as web_app


class SearchSmokeTests(unittest.TestCase):

    def test_web_search_uses_only_saved_approved_folders(self):
        with tempfile.TemporaryDirectory() as folder:
            config_path = os.path.join(folder, "approved.json")
            with open(config_path, "w", encoding="utf-8") as config_file:
                json.dump([folder], config_file)

            with (
                patch.object(web_app, "FOLDER_CONFIG_PATH", config_path),
                patch.object(
                    web_app,
                    "search_findly",
                    return_value=[("clip.mp4", ".mp4")],
                ) as search,
            ):
                response = web_app.app.test_client().post(
                    "/search",
                    json={"query": "videos"},
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["count"], 1)
        search.assert_called_once_with("videos", [folder])

    def test_web_search_rejects_non_json_request(self):
        response = web_app.app.test_client().post(
            "/search",
            data="not json",
            content_type="text/plain",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.get_json()["success"])

    def test_scanner_indexes_files_and_reports_count(self):
        connection = sqlite3.connect(":memory:")

        with tempfile.TemporaryDirectory() as folder:
            file_path = os.path.join(folder, "notes.txt")
            with open(file_path, "w", encoding="utf-8") as file:
                file.write("Findly scan test")

            with patch("scanner.sqlite3.connect", return_value=connection):
                summary = scanner.scan_folder(folder)

        self.assertEqual(summary["scanned"], 1)
        self.assertEqual(summary["skipped"], 0)

    def test_scanner_removes_stale_entries_only_inside_successfully_scanned_folder(self):
        with tempfile.TemporaryDirectory() as folder, tempfile.TemporaryDirectory() as database_folder:
            database_path = os.path.join(database_folder, "test.db")
            connect = sqlite3.connect
            present_path = os.path.join(folder, "present.txt")
            stale_path = os.path.join(folder, "deleted.txt")
            outside_path = os.path.join(
                os.path.dirname(folder),
                "outside-keep.txt"
            )
            with open(present_path, "w", encoding="utf-8") as file:
                file.write("current")

            connection = connect(database_path)
            connection.execute(
                """
                CREATE TABLE files (
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
            connection.executemany(
                "INSERT INTO files (name, path) VALUES (?, ?)",
                [
                    ("deleted.txt", stale_path.replace("\\", "/")),
                    ("outside-keep.txt", outside_path.replace("\\", "/")),
                ],
            )
            connection.commit()
            connection.close()

            with patch(
                "scanner.sqlite3.connect",
                side_effect=lambda _path: connect(database_path)
            ):
                scanner.scan_folder(folder)

            connection = connect(database_path)
            paths = {
                row[0]
                for row in connection.execute("SELECT path FROM files")
            }
            connection.close()

        self.assertIn(present_path.replace("\\", "/"), paths)
        self.assertNotIn(stale_path.replace("\\", "/"), paths)
        self.assertIn(outside_path.replace("\\", "/"), paths)

    def test_refresh_file_updates_modified_timestamp(self):
        with tempfile.TemporaryDirectory() as folder:
            database_path = os.path.join(folder, "test.db")
            file_path = os.path.join(folder, "notes.txt")
            connect = sqlite3.connect
            with open(file_path, "w", encoding="utf-8") as file:
                file.write("before")

            with patch(
                "scanner.sqlite3.connect",
                side_effect=lambda _path: connect(database_path)
            ):
                scanner.refresh_file(file_path)
                connection = connect(database_path)
                before = connection.execute(
                    "SELECT modified FROM files WHERE name = ?",
                    ("notes.txt",)
                ).fetchone()[0]
                connection.close()

                with open(file_path, "a", encoding="utf-8") as file:
                    file.write(" updated")
                os.utime(file_path, (1_800_000_000, 1_800_000_000))
                scanner.refresh_file(file_path)
                connection = connect(database_path)
                after = connection.execute(
                    "SELECT modified FROM files WHERE name = ?",
                    ("notes.txt",)
                ).fetchone()[0]
                connection.close()

            self.assertNotEqual(before, after)

    def test_remove_file_deletes_its_index_record(self):
        with tempfile.TemporaryDirectory() as folder:
            database_path = os.path.join(folder, "test.db")
            file_path = os.path.join(folder, "notes.txt")
            connect = sqlite3.connect

            with patch(
                "scanner.sqlite3.connect",
                side_effect=lambda _path: connect(database_path)
            ):
                connection = connect(database_path)
                connection.execute(
                    """
                    CREATE TABLE files (
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
                connection.execute(
                    "INSERT INTO files (name, path) VALUES (?, ?)",
                    ("notes.txt", file_path.replace("\\", "/"))
                )
                connection.commit()
                connection.close()

                scanner.remove_file(file_path)

            connection = connect(database_path)
            count = connection.execute(
                "SELECT COUNT(*) FROM files WHERE name = ?",
                ("notes.txt",)
            ).fetchone()[0]
            connection.close()
            self.assertEqual(count, 0)

    def test_search_files_deduplicates_same_path_results(self):
        connection = sqlite3.connect(":memory:")
        connection.execute(
            """
            CREATE TABLE files (
                name TEXT,
                path TEXT,
                extension TEXT,
                size REAL,
                created TEXT,
                modified TEXT,
                taken TEXT
            )
            """
        )

        connection.executemany(
            """
            INSERT INTO files (name, path, extension, size, created, modified, taken)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "photo1.jpg",
                    r"C:\project\photos\photo1.jpg",
                    ".jpg",
                    1.2,
                    "2024-01-01 00:00:00",
                    "2024-01-02 00:00:00",
                    None,
                ),
                (
                    "photo1.jpg",
                    r"C:\project\photos\photo1.jpg",
                    ".jpg",
                    1.2,
                    "2024-01-01 00:00:00",
                    "2024-01-02 00:00:00",
                    None,
                ),
            ],
        )

        with patch("file_engine.sqlite3.connect", return_value=connection):
            results = file_engine.search_files(
                "photo",
                [r"C:\project\photos"]
            )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][1], ".jpg")

    def test_documents_search_lists_spreadsheets_and_text_documents(self):
        connection = sqlite3.connect(":memory:")
        connection.execute(
            """
            CREATE TABLE files (
                name TEXT,
                path TEXT,
                extension TEXT,
                size REAL,
                created TEXT,
                modified TEXT,
                taken TEXT
            )
            """
        )
        connection.executemany(
            """
            INSERT INTO files (name, path, extension, size, created, modified, taken)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("notes.txt", "C:/docs/notes.txt", ".txt", 0.1, "", "", None),
                ("report.pdf", "C:/docs/report.pdf", ".pdf", 0.2, "", "", None),
                ("budget.xlsx", "C:/docs/budget.xlsx", ".xlsx", 0.3, "", "", None),
                ("archive.exe", "C:/docs/archive.exe", ".exe", 0.4, "", "", None),
            ],
        )

        with patch("file_engine.sqlite3.connect", return_value=connection):
            results = file_engine.search_files(
                "all documents",
                [r"C:\docs"]
            )

        self.assertEqual(
            {result[1] for result in results},
            {".txt", ".pdf", ".xlsx"}
        )

    def test_search_findly_rejects_empty_query(self):
        self.assertEqual(natural_language_engine.search_findly("   "), [])

    def test_documents_category_query_lists_all_indexed_document_types(self):
        with patch(
            "natural_language_engine.search_files_in_folders",
            return_value=[("budget.xlsx", ".xlsx", 0.3, "C:/docs/budget.xlsx", "", "", None)],
        ) as search_files:
            results = natural_language_engine.search_findly(
                "show all documents",
                [r"C:\docs"]
            )

        search_files.assert_called_once()
        self.assertEqual(results[0][1], ".xlsx")

    def test_resume_query_uses_document_search(self):
        with patch(
            "natural_language_engine.search_smart_documents",
            return_value=[
                ("PDF", r"C:/docs/resume.pdf", 1, "This is my resume.", 0.9)
            ],
        ) as search_documents:
            results = natural_language_engine.search_findly(
                "find my resume",
                [r"C:\docs"]
            )

        search_documents.assert_called_once_with("find my resume", r"C:\docs")
        self.assertEqual(results[0][1], r"C:/docs/resume.pdf")

    def test_search_findly_deduplicates_document_results(self):
        with patch(
            "natural_language_engine.search_smart_documents",
            return_value=[
                ("PDF", r"C:\docs\report.pdf", 1, "This is a report."),
                ("PDF", r"C:\docs\report.pdf", 1, "This is a report."),
            ],
        ):
            results = natural_language_engine.search_findly(
                "document report",
                [r"C:\docs"]
            )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][1], r"C:\docs\report.pdf")

    def test_person_search_returns_every_detected_photo_in_folder(self):
        with tempfile.TemporaryDirectory() as folder:
            indexed_paths = []
            for index in range(8):
                path = os.path.join(folder, f"person-{index}.jpg")
                with open(path, "wb") as image_file:
                    image_file.write(b"test image placeholder")
                indexed_paths.append(path)

            with (
                patch.object(
                    person_detector,
                    "PERSON_INDEX_PATH",
                    os.path.join(folder, "person-index.json")
                ),
                patch(
                    "person_detector.detect_person_confidence",
                    return_value=0.8
                )
            ):
                for path in indexed_paths:
                    person_detector.index_person_image(path)

                results = person_detector.search_person_images([folder])

        self.assertEqual(len(results), 8)
        self.assertEqual(
            {result[0] for result in results},
            set(indexed_paths)
        )

    def test_person_index_refresh_removes_deleted_photos_in_folder(self):
        with tempfile.TemporaryDirectory() as folder:
            keep_path = os.path.join(folder, "keep.jpg")
            deleted_path = os.path.join(folder, "deleted.jpg")
            for path in (keep_path, deleted_path):
                with open(path, "wb") as image_file:
                    image_file.write(b"test image placeholder")

            index_path = os.path.join(folder, "person-index.json")
            with (
                patch.object(person_detector, "PERSON_INDEX_PATH", index_path),
                patch(
                    "person_detector.detect_person_confidence",
                    return_value=0.8
                ),
            ):
                person_detector.index_person_image(keep_path)
                person_detector.index_person_image(deleted_path)
                os.remove(deleted_path)
                person_detector.prune_person_images(
                    folder,
                    {os.path.normcase(os.path.abspath(keep_path))}
                )
                results = person_detector.search_person_images([folder])

        self.assertEqual(results, [(keep_path, 0.8)])

    def test_person_query_uses_detector_instead_of_similarity_search(self):
        matches = [
            (f"C:/photos/person-{index}.jpg", 0.8)
            for index in range(8)
        ]
        with patch(
            "person_detector.search_person_images",
            return_value=matches
        ) as search_people:
            results = natural_language_engine.search_findly(
                "show me a photo of a person",
                ["C:/photos"]
            )

        search_people.assert_called_once()
        self.assertEqual(results, matches)

    def test_video_query_uses_file_metadata_search(self):
        with (
            patch(
                "natural_language_engine.search_files_in_folders",
                return_value=[
                    ("clip.mp4", ".mp4", 2.0, "C:/videos/clip.mp4", "", "", None)
                ],
            ) as search_files,
            patch("natural_language_engine.search_images") as search_images,
        ):
            results = natural_language_engine.search_findly(
                "show family videos from 2025",
                ["C:/videos"],
            )

        search_files.assert_called_once()
        search_images.assert_not_called()
        self.assertEqual(results[0][1], ".mp4")

    def test_person_search_combines_year_and_size_filters(self):
        with tempfile.TemporaryDirectory() as folder:
            matching_path = os.path.join(folder, "person-large.jpg")
            old_path = os.path.join(folder, "person-old.jpg")
            for path in (matching_path, old_path):
                with open(path, "wb") as image_file:
                    image_file.write(b"x" * (2 * 1024 * 1024))

            os.utime(matching_path, (1_735_689_600, 1_735_689_600))
            os.utime(old_path, (1_672_531_200, 1_672_531_200))

            with patch(
                "person_detector.search_person_images",
                return_value=[(matching_path, 0.9), (old_path, 0.95)]
            ):
                results = natural_language_engine.search_findly(
                    "show person photos from 2025 bigger than 1 MB",
                    [folder]
                )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][3], matching_path)
        self.assertEqual(results[0][4], 0.9)

    def test_combined_photo_search_supports_date_and_size_ranges(self):
        import combined_engine

        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "photo.jpg")
            with open(path, "wb") as image_file:
                image_file.write(b"x" * (2 * 1024 * 1024))

            with patch.object(
                combined_engine,
                "load_image_index",
                return_value=[(path, None)]
            ):
                results = combined_engine.search_combined(
                    "photos from 1 MB to 3 MB",
                    [folder]
                )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][3], path)

    def test_query_parser_handles_relative_week_ranges(self):
        details = query_parser.parse_query("photos from last week")
        today = query_parser.datetime.now().date()
        expected_start = today - query_parser.relativedelta(
            days=today.weekday() + 7
        )

        self.assertEqual(details["date_start"], expected_start)
        self.assertEqual(
            details["date_end"],
            expected_start + query_parser.relativedelta(days=7)
        )

    def test_query_parser_handles_inclusive_size_filters(self):
        at_least = query_parser.parse_query("photos at least 5 MB")
        at_most = query_parser.parse_query("photos at most 2 GB")

        self.assertEqual(at_least["size_condition"], ">=")
        self.assertEqual(at_least["size_min"], 5)
        self.assertEqual(at_most["size_condition"], "<=")
        self.assertEqual(at_most["size_max"], 2048)

    def test_image_search_returns_matches_instead_of_none(self):
        fake_model = SimpleNamespace(
            text_model=lambda **inputs: SimpleNamespace(
                pooler_output=torch.tensor([[1.0, 0.0]])
            ),
            text_projection=lambda embedding: embedding
        )

        with tempfile.TemporaryDirectory() as folder:
            image_path = os.path.join(folder, "photo.jpg")
            with open(image_path, "wb") as image_file:
                image_file.write(b"indexed photo placeholder")

            with (
                patch.object(image_engine, "load_image_index", return_value=[
                    (image_path, [1.0, 0.0])
                ]),
                patch.object(image_engine, "processor", return_value={}),
                patch.object(image_engine, "model", fake_model),
            ):
                results = image_engine.search_images("a landscape", [folder])

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], image_path)
        self.assertAlmostEqual(results[0][1], 1.0)

    def test_image_index_reindexes_modified_and_removes_deleted_photos(self):
        import image_indexer

        with tempfile.TemporaryDirectory() as folder:
            image_path = os.path.join(folder, "photo.jpg")
            index_path = os.path.join(folder, "images.pt")
            with open(image_path, "wb") as image_file:
                image_file.write(b"image-placeholder")

            with (
                patch.object(image_indexer, "INDEX_PATH", index_path),
                patch.object(
                    image_indexer,
                    "get_image_embedding",
                    side_effect=[[1.0], [2.0]],
                ) as get_embedding,
                patch(
                    "person_detector.initialize_person_detector"
                ),
                patch(
                    "person_detector.index_person_image",
                    return_value=0.0,
                ),
                patch("person_detector.prune_person_images"),
            ):
                self.assertEqual(image_indexer.index_image_folder(folder), 1)

                old_mtime = os.stat(image_path).st_mtime_ns
                os.utime(
                    image_path,
                    ns=(old_mtime + 2_000_000_000, old_mtime + 2_000_000_000),
                )
                self.assertEqual(image_indexer.index_image_folder(folder), 0)
                self.assertEqual(get_embedding.call_count, 2)

                os.remove(image_path)
                image_indexer.index_image_folder(folder)
                saved_index = torch.load(index_path, weights_only=False)

        self.assertEqual(saved_index, [])

    def test_image_indexer_reuses_the_search_model(self):
        import image_indexer

        self.assertIs(image_indexer.model, image_engine.model)
        self.assertIs(image_indexer.processor, image_engine.processor)

    def test_image_index_rebuild_does_not_overwrite_unreadable_index(self):
        import image_indexer

        with tempfile.TemporaryDirectory() as folder:
            index_path = os.path.join(folder, "damaged.pt")
            with open(index_path, "wb") as index_file:
                index_file.write(b"preserve damaged index")

            with patch.object(image_indexer, "INDEX_PATH", index_path):
                with self.assertRaisesRegex(RuntimeError, "left it unchanged"):
                    image_indexer.index_image_folder(folder)

            with open(index_path, "rb") as index_file:
                saved_data = index_file.read()

        self.assertEqual(saved_data, b"preserve damaged index")


if __name__ == "__main__":
    unittest.main()
