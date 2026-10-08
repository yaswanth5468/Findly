# Findly

Findly is a local-first Windows desktop file and photo search application. It
indexes only folders that the user explicitly approves. Supported searches
include file names and types, dates and sizes, document contents (TXT, PDF and
DOCX), CLIP-based photo similarity, and person detection.
Photo matches appear in a thumbnail gallery with paging and direct open
actions.

## Run on Windows

Use Python 3.12 and run the following commands from the project folder:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python findly_app.py
```

The first launch may download the CLIP, document embedding and person-detection
models. The models and search indexes are stored locally. Model downloads
require an internet connection; indexed file contents and photos are processed
locally.

Use **ADD FOLDER** to choose a folder and approve access. Findly scans that
folder and its subfolders. Approved folder paths are saved in
`%LOCALAPPDATA%\Findly\approved_folders.json` so Findly can restore and update
the indexes on later launches. Use **FOLDERS** to remove an approval; removing
it does not delete the folder or its contents. This application-level approval
does not override Windows or network-drive permissions.

Findly monitors approved folders while open and performs a periodic
reconciliation. **REFRESH INDEX** starts a manual reconciliation without
blocking the desktop UI.

## Voice and privacy

Desktop voice input uses the SpeechRecognition Google transcription service.
Findly asks for consent before each voice search; microphone audio is sent to
Google for transcription. Speech output uses the local system voice when
available. Browser voice input is handled by the browser and may send audio to
the browser vendor's recognition service; the web UI asks before starting.

## Optional local web UI

The Flask UI is a local companion to the desktop app. Approve folders in the
desktop application first, then run:

```powershell
python app.py
```

The server binds to `127.0.0.1` and searches only the saved approved folders.
The web UI cannot grant folder access. Do not change the server to listen on a
public network interface without adding authentication and an explicit
permission model.

## Tests

Run the focused regression suite from the project folder:

```powershell
python -m unittest test_search_smoke -v
```

## Current boundaries

- Folder approval is local to this Windows user and is not whole-device or
  cross-device access.
- Document content indexing/search currently supports TXT, PDF and DOCX;
  other listed office formats can be found by file type/name only.
- Video search is file metadata/name search. Findly does not inspect video
  frames or audio.
- Person detection and CLIP similarity are probabilistic and can miss or
  misrank content.
- Mobile apps, cross-device synchronization, and encryption of the local index
  are not implemented.
