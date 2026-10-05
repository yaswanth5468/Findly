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
import scanner
import torch


class SearchSmokeTests(unittest.TestCase):

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


if __name__ == "__main__":
    unittest.main()
