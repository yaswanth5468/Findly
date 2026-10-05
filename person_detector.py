import json
import os
import tempfile
import threading

import torch
from PIL import Image
from torchvision.models.detection import (
    SSDLite320_MobileNet_V3_Large_Weights,
    ssdlite320_mobilenet_v3_large,
)


PERSON_DETECTION_THRESHOLD = 0.35
PERSON_INDEX_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "person_detection_index.json"
)

_model = None
_person_label = None
_model_lock = threading.Lock()
_index_lock = threading.Lock()


def _normalise_path(path):

    return os.path.normcase(os.path.abspath(path))


def _load_index():

    if not os.path.exists(PERSON_INDEX_PATH):
        return {}

    with open(PERSON_INDEX_PATH, "r", encoding="utf-8") as index_file:
        data = json.load(index_file)

    if not isinstance(data, dict):
        raise ValueError("Person detection index must be a JSON object.")

    return data


def _save_index(data):

    directory = os.path.dirname(PERSON_INDEX_PATH)
    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=directory,
            suffix=".tmp",
            delete=False
        ) as index_file:
            temporary_path = index_file.name
            json.dump(data, index_file)

        os.replace(temporary_path, PERSON_INDEX_PATH)
    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.remove(temporary_path)


def _get_model():

    global _model, _person_label

    if _model is not None:
        return _model, _person_label

    with _model_lock:
        if _model is None:
            weights = SSDLite320_MobileNet_V3_Large_Weights.DEFAULT
            detector = ssdlite320_mobilenet_v3_large(
                weights=weights
            )
            detector.eval()
            _model = detector
            _person_label = weights.meta["categories"].index("person")

    return _model, _person_label


def initialize_person_detector():

    _get_model()


def detect_person_confidence(path):

    model, person_label = _get_model()
    weights = SSDLite320_MobileNet_V3_Large_Weights.DEFAULT
    transform = weights.transforms()

    with Image.open(path) as source_image:
        image = source_image.convert("RGB")

    image_tensor = transform(image)

    with torch.no_grad():
        prediction = model([image_tensor])[0]

    person_scores = prediction["scores"][
        prediction["labels"] == person_label
    ]

    if person_scores.numel() == 0:
        return 0.0

    return float(person_scores.max().item())


def index_person_image(path, force=False):

    key = _normalise_path(path)

    with _index_lock:
        data = _load_index()
        if key in data and not force:
            return None

    confidence = detect_person_confidence(path)

    with _index_lock:
        data = _load_index()
        data[key] = {
            "path": os.path.abspath(path),
            "confidence": confidence
        }
        _save_index(data)

    return confidence


def remove_person_image(path):

    key = _normalise_path(path)

    with _index_lock:
        data = _load_index()
        if key in data:
            del data[key]
            _save_index(data)


def search_person_images(folders=None):

    with _index_lock:
        data = _load_index()

    normalized_folders = [
        os.path.normcase(os.path.abspath(folder))
        for folder in (folders or [])
    ]

    matches = []

    for indexed_path, entry in data.items():
        if isinstance(entry, dict):
            path = entry.get("path", indexed_path)
            confidence = entry.get("confidence", 0.0)
        else:
            path = indexed_path
            confidence = entry

        if not os.path.isfile(path):
            continue

        if normalized_folders:
            normalized_path = _normalise_path(path)
            try:
                if not any(
                    os.path.commonpath([normalized_path, folder]) == folder
                    for folder in normalized_folders
                ):
                    continue
            except ValueError:
                continue

        if float(confidence) >= PERSON_DETECTION_THRESHOLD:
            matches.append((path, float(confidence)))

    matches.sort(key=lambda result: result[1], reverse=True)
    return matches
