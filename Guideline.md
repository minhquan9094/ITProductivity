# Folder Documentation Assistant

A Python script to help you document and quickly find your important work folders, designed for use with searchable note-taking apps like OneNote, Obsidian, or any text search tool.

It follows a simple two-step workflow:

1.  **Scan:** Automatically scan a directory (like your `Documents` or `Work` folder) up to a specified depth to generate a plain text list (`.txt`) of subfolders found.
2.  **Generate:** Edit the generated text list to remove unwanted folders and add your own descriptions/notes for the remaining ones. Then, use this edited list to generate a structured Markdown file (`.md`) perfect for pasting into your notes.

This allows you to leverage your note app's search functionality to quickly find the location and purpose of your folders based on your descriptions.

## Features

* **Automatic Folder Discovery (`scan`):** Scans directories to quickly find main work folders.
* **Configurable Scan Depth (`scan`):** Limits scanning to top levels (e.g., 1 or 2 levels deep relative to the start).
* **Ignore Patterns (`scan`):** Excludes common clutter (like `.git`, `__pycache__`, `node_modules`) and allows specifying custom folders/patterns to ignore using `fnmatch` wildcards (e.g., `Temp*`, `Archive`).
* **Hidden File Handling (`scan`):** Option to include or exclude hidden folders (those starting with `.`).
* **Prepare Input List (`scan`):** Outputs a simple text file (`path | description`) ready for editing.
* **Manual Curation (Editing Step):** Simple text file format for easily adding descriptions and removing irrelevant folders.
* **Markdown Note Generation (`generate`):** Generates clean Markdown from the curated list, suitable for pasting into OneNote, Obsidian, etc., preserving structure and making descriptions searchable. Checks for basic path existence.
* **Cross-Platform:** Uses Python's `pathlib` for better compatibility between Windows, macOS, and Linux.
* **No External Libraries:** Uses only Python's standard library.

## Workflow

1.  **Scan Folders (`scan` command):**
    * Run the script with the `scan` command, specifying the directory you want to start scanning (`start_dir`) and the desired depth (`--depth`).
    * This creates a `.txt` file (default: `folder_list_for_editing.txt`). Each line contains the full path to a discovered subfolder, a separator (`|` by default), and a placeholder description `PLEASE ADD DESCRIPTION`.
    ```bash
    # Scan C:\Work folder, only immediate subdirectories (depth 1)
    python folder_documenter.py scan "C:\Path\To\Your\WorkFolder" --depth 1 -o scan_results.txt
    ```

2.  **Edit the List:**
    * Open the generated `.txt` file (e.g., `scan_results.txt`) in a text editor.
    * **Delete** lines corresponding to folders you don't need/want to document.
    * **Replace** `PLEASE ADD DESCRIPTION` on the remaining lines with your own notes about what each folder contains or is used for. *Use keywords you might search for later!*
    * Save the edited file.

3.  **Generate Notes (`generate` command):**
    * Run the script with the `generate` command, providing your edited `.txt` file as the `config_file` argument.
    * This creates a `.md` file (default: `folder_reference.md`) containing your folder list formatted nicely with descriptions.
    ```bash
    # Generate the Markdown file from the edited list
    python folder_documenter.py generate scan_results.txt -o MyWorkReference.md
    ```

4.  **Copy to Notes App:**
    * Open the generated `.md` file (e.g., `MyWorkReference.md`) in a text editor or Markdown viewer.
    * Select all content (Ctrl+A or Cmd+A) and copy it (Ctrl+C or Cmd+C).
    * Paste it (Ctrl+V or Cmd+V) into a new page in OneNote, Obsidian, or your preferred app.

5.  **Search:** Use your note app's search function (e.g., Ctrl+F) to find folders based on their name, path segments, or keywords in your descriptions!

## Requirements

* Python 3.7 or later recommended (uses `pathlib`, f-strings, and `argparse` features). Should work on 3.6+ but tested primarily on newer versions.
* No external libraries required.

## Setup

1.  Save the combined Python code as a file named `folder_documenter.py`.
2.  Ensure you can run Python from your command line or terminal (`python --version` or `python3 --version`).

## Usage

The script uses two main commands: `scan` and `generate`. Run `python folder_documenter.py --help` for top-level help.

```bash
python folder_documenter.py <command> [options...]


scan Command
Scans a directory to generate a preliminary folder list (.txt) for editing.
usage: folder_documenter.py scan [-h] [-d DEPTH] [-o OUTPUT] [--ignore-dir PATTERN] [--include-hidden] [--separator SEPARATOR] start_dir

Scans a directory up to a specified depth and generates a list of found subfolders formatted for use as input with the 'generate' command.

positional arguments:
  start_dir             The starting directory path to scan.

options:
  -h, --help            show this help message and exit
  -d DEPTH, --depth DEPTH
                        Maximum depth to scan folders relative to start_dir (0=no subfolders, 1=immediate subdirs, etc.). Default: 1
  -o OUTPUT, --output OUTPUT
                        Path for the output text file (default: folder_list_for_editing.txt)
  --ignore-dir PATTERN  Directory name/pattern to ignore (fnmatch wildcards like 'Temp*'). Can be used multiple times.
  --include-hidden      Include hidden directories (starting with '.'). Default ignores might still apply.
  --separator SEPARATOR
                        Separator character to use between path and description in the output file (default: '|')

Example usage:
  python folder_documenter.py scan . -d 1 -o my_scan.txt
  python folder_documenter.py scan "C:\Work" --depth 2 --ignore-dir "Temp" --ignore-dir "Archive*"


generate Command
Generates the final Markdown notes from a prepared text file.
usage: folder_documenter.py generate [-h] [-o OUTPUT] [--separator SEPARATOR] config_file

Generates a Markdown reference page from a text file listing folder paths and descriptions.

positional arguments:
  config_file           Path to the text file containing folder paths and descriptions (one per line, path<separator>description).

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Path for the output Markdown file (default: folder_reference.md)
  --separator SEPARATOR
                        Separator character used in the config file to separate path from description (default: '|')

Example usage:
  python folder_documenter.py generate folder_list_for_editing.txt
  python folder_documenter.py generate my_edited_list.txt -o MyNotes.md --separator ::


Configuration File Format (.txt)
The text file used as input for the generate command (and produced by the scan command) should follow this format:
Each line represents one folder you want to include in the final Markdown.
Lines starting with # are treated as comments and ignored by the generate command.
Empty lines are ignored.
Each non-comment line must contain: <Full Folder Path><Separator><Description>
The <Separator> is | by default but can be changed using the --separator argument in both commands (ensure they match!).
The <Description> is the text that will appear in the Markdown notes. The scan command outputs PLEASE ADD DESCRIPTION as a placeholder.
Example .txt File Content (After Editing):
# My important work folders - Ready for generate command
C:\Work\Clients\Alpha Corp | Project files, contracts, meeting notes for Alpha. Final deliverables stored here.
C:\Work\Scripts\Python | My utility scripts for various automation tasks. Needs cleanup. Check 'main_runner.py' first.
\\Server\SharedDocs\Templates | Official document and presentation templates. Read-only access for team members.
# C:\Work\Archive | Old project archive (This line is commented out - will be ignored by generate)
C:\Work\Personal\Travel Plans | Notes and bookings for upcoming trips.


License
This project is licensed under the MIT License.
Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


