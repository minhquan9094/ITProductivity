#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Folder Documentation Assistant
A script to help document and find work folders using two main commands:
1. 'scan': Automatically discover folders up to a certain depth.
2. 'generate': Create a Markdown reference page from a manually curated list.
"""

import argparse
import datetime
from pathlib import Path
import fnmatch
import sys
import os

# --- Shared Constants ---
DEFAULT_IGNORE_DIRS = [
    '.git', '__pycache__', '.venv', 'venv', 'env',
    'node_modules', '.vscode', '.idea', 'build', 'dist',
    '*.egg-info', '$RECYCLE.BIN', 'System Volume Information'
]
DEFAULT_SCAN_OUTPUT_FILENAME = "folder_list_for_editing.txt"
DEFAULT_GENERATE_OUTPUT_FILENAME = "folder_reference.md"
DEFAULT_SEPARATOR = "|"

# --- Utility Functions ---
def get_local_timestamp():
    """Gets the current timestamp with local timezone information if possible."""
    try:
        # Get current time, convert to local timezone aware object
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        local_tz_time = now_utc.astimezone()
        return local_tz_time.strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception:
        # Fallback if timezone info isn't available easily or fails
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S (Local Timezone Unknown)")

# --- Scan Functionality ---
# Global list for recursive scan - reset before each scan run
discovered_paths_scan = []

def _find_folders_recursive(
    current_path: Path,
    start_path: Path,
    current_depth: int,
    max_depth: int,
    include_hidden: bool,
    ignore_patterns: list):
    """
    Internal recursive function for scanning folders. Appends absolute path strings
    of discovered folders (excluding start_path itself) to discovered_paths_scan.
    """
    global discovered_paths_scan

    # --- Check if current folder should be processed/added ---
    # Skip adding the start directory itself (depth 0), only add subfolders
    if current_depth > 0:
            # Apply ignore filters before adding the path
            if any(fnmatch.fnmatch(current_path.name, pattern) for pattern in ignore_patterns):
                return # Don't add or scan deeper
            if not include_hidden and current_path.name.startswith('.'):
                return # Don't add or scan deeper

            # Add the absolute path string to our list
            try:
                # Resolve to get a clean, absolute path
                discovered_paths_scan.append(str(current_path.resolve()))
            except Exception as e:
                # Handle cases where resolving might fail (e.g., dangling symlink, permissions)
                print(f"Warning: Could not resolve path for '{current_path}', skipping. Error: {e}", file=sys.stderr)
                return


    # --- Stop Recursion if max depth reached ---
    # No need to look inside folders *at* the max_depth level
    if current_depth >= max_depth:
        return

    # --- Scan Subdirectories ---
    try:
        sub_dirs_to_scan = []
        # Use try-except around iterdir for permission issues on the current_path itself
        for item in current_path.iterdir():
            # Check if it's a directory
            # Add basic error handling for stat calls (e.g. broken symlinks, permissions)
            try:
                # Use is_dir() with follow_symlinks=False if you want to list symlinks TO directories,
                # but not follow them into potentially infinite loops or unexpected locations.
                # Default is_dir() follows symlinks. Let's stick with default for now.
                if item.is_dir():
                    # Apply filters *before* adding to the list for recursion
                    if any(fnmatch.fnmatch(item.name, pattern) for pattern in ignore_patterns):
                        continue # Ignore pattern matched
                    if not include_hidden and item.name.startswith('.'):
                        continue # Hidden directory ignored
                    sub_dirs_to_scan.append(item)
            except OSError as stat_error:
                 # Error accessing file/folder attributes
                 print(f"Warning: Could not access attributes of '{item.name}' in '{current_path}'. Skipping. Error: {stat_error}", file=sys.stderr)
            except Exception as general_error:
                 # Other unexpected errors
                 print(f"Warning: Unexpected error checking item '{item.name}' in '{current_path}'. Skipping. Error: {general_error}", file=sys.stderr)


        # Sort for consistent order
        sub_dirs_to_scan.sort(key=lambda p: p.name.lower())

        # Recurse into valid subdirectories
        for sub_dir in sub_dirs_to_scan:
                _find_folders_recursive(
                    sub_dir,
                    start_path, # Keep passing the original start_path for reference
                    current_depth + 1, # Increment depth
                    max_depth,
                    include_hidden,
                    ignore_patterns
                )

    except PermissionError:
        # Note permission error for the directory we tried to scan *into*
        print(f"Warning: Permission denied scanning inside '{current_path}'", file=sys.stderr)
    except FileNotFoundError:
        # Can happen if directory is deleted between checks
        print(f"Warning: Folder '{current_path}' not found during scan (might have been deleted).", file=sys.stderr)
    except Exception as e:
        # Catch other potential errors during directory iteration (e.g., network issues)
        print(f"Warning: Error scanning inside '{current_path}': {e}", file=sys.stderr)


def run_scan_action(args):
    """Executes the scan action based on parsed arguments."""
    global discovered_paths_scan
    discovered_paths_scan = [] # Reset global list for this run

    try:
        start_dir = Path(args.start_dir).resolve() # Attempt to resolve early
    except Exception as e:
        print(f"Error: Could not resolve start directory path '{args.start_dir}'. Error: {e}", file=sys.stderr)
        sys.exit(1)

    output_file = Path(args.output)
    max_depth = args.depth
    include_hidden = args.include_hidden
    user_ignore_dirs = args.ignore_dir or [] # Handle None case
    separator = args.separator

    if not start_dir.is_dir():
        print(f"Error: Start directory not found or is not a directory: '{start_dir}'", file=sys.stderr)
        sys.exit(1)
    if max_depth < 0:
        print("Error: Depth cannot be negative.", file=sys.stderr)
        sys.exit(1)

    ignore_patterns = DEFAULT_IGNORE_DIRS + user_ignore_dirs

    print(f"Starting Scan...")
    print(f"  Directory:      {start_dir}")
    print(f"  Max Depth:      {max_depth}")
    print(f"  Include Hidden: {include_hidden}")
    # print(f"  Ignoring patterns: {ignore_patterns}") # Can be very long
    print(f"  Output File:    {output_file}")
    print("-" * 30, file=sys.stderr) # Print progress/warnings to stderr

    _find_folders_recursive(start_dir, start_dir, 0, max_depth, include_hidden, ignore_patterns)

    print("-" * 30, file=sys.stderr)
    print(f"Scan complete. Found {len(discovered_paths_scan)} subfolders matching criteria.", file=sys.stderr)

    # Write output file
    try:
        timestamp = get_local_timestamp() # Use Ho Chi Minh City Time

        # Create parent directories if they don't exist
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with output_file.open('w', encoding='utf-8') as f:
            # Write header comments for the .txt file
            f.write(f"# Automatically generated list of folders found in: {start_dir}\n")
            f.write(f"# Maximum Scan Depth Relative to Start: {max_depth}\n")
            f.write(f"# Generated on: {timestamp}\n")
            f.write("#\n")
            f.write("# Instructions for use with the 'generate' command:\n")
            f.write("# 1. Review the folder paths below.\n")
            f.write("# 2. Remove any folders you don't need to document.\n")
            f.write(f"# 3. Replace 'PLEASE ADD DESCRIPTION' after the '{separator}' with your actual notes for each folder.\n")
            f.write("# 4. Save this file.\n")
            f.write(f"# 5. Run: python {os.path.basename(sys.argv[0])} generate <this_file_name> -o final_notes.md\n")
            f.write("#---------------------------------------------------------------------------\n\n")


            if not discovered_paths_scan:
                f.write("# No subfolders found matching the criteria.\n")
            else:
                # Sort the paths alphabetically for consistency and easier editing
                discovered_paths_scan.sort()
                for path_str in discovered_paths_scan:
                    # Write in the specific format: path separator description
                    f.write(f"{path_str} {separator} PLEASE ADD DESCRIPTION\n")

        print(f"\nSuccessfully generated folder list for editing: {output_file.resolve()}")
        print("\nNext steps:")
        print(f" 1. Edit the file '{output_file.name}' to add descriptions and remove unwanted lines.")
        print(f" 2. Run 'python {os.path.basename(sys.argv[0])} generate {output_file.name}' to create the final Markdown.")

    except IOError as e:
        print(f"\nError: Could not write to output file '{output_file}': {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nAn unexpected error occurred during file writing: {e}", file=sys.stderr)
        sys.exit(1)


# --- Generate Functionality ---
def run_generate_action(args):
    """Executes the generate action based on parsed arguments."""
    config_file = Path(args.config_file)
    output_file = Path(args.output)
    separator = args.separator

    if not config_file.is_file():
        print(f"Error: Configuration file not found at '{config_file}'", file=sys.stderr)
        sys.exit(1)

    entries = []
    print(f"Reading configuration from: {config_file}")
    line_warnings = 0
    try:
        with config_file.open('r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1): # Start line count at 1
                line = line.strip()
                if not line or line.startswith('#'): # Skip empty lines and comments
                    continue
                if separator not in line:
                    print(f"Warning: Skipping line {i} in config file - missing separator '{separator}': {line}", file=sys.stderr)
                    line_warnings += 1
                    continue

                parts = line.split(separator, maxsplit=1)
                folder_path_str = parts[0].strip()
                description = parts[1].strip()

                if not folder_path_str or not description:
                    print(f"Warning: Skipping line {i} - empty path or description.", file=sys.stderr)
                    line_warnings += 1
                    continue
                # Basic check for placeholder description
                if description == "PLEASE ADD DESCRIPTION":
                     print(f"Warning: Line {i} still has the placeholder description for '{folder_path_str}'", file=sys.stderr)
                     line_warnings += 1


                # Resolve and check existence - handle errors gracefully
                path_resolved_str = folder_path_str # Default to original if resolve fails
                exists = False
                folder_path = Path(folder_path_str) # Start with original path object
                try:
                    # Attempt to resolve, handle potential strict errors based on OS
                    is_windows = sys.platform.startswith('win')
                    folder_path = folder_path.resolve(strict=not is_windows)
                    exists = folder_path.is_dir() # Check if the resolved path is a directory
                    path_resolved_str = str(folder_path) # Use the resolved string if successful
                except FileNotFoundError:
                     # Path doesn't exist or strict=True failed on non-Windows
                     exists = False
                except OSError as oe:
                     # Other OS errors, e.g. permissions, invalid network path format
                     print(f"Warning: OS error checking path '{folder_path_str}' on line {i}. It might be inaccessible. Error: {oe}", file=sys.stderr)
                     exists = False
                     line_warnings += 1
                except Exception as e: # Catch other potential Path exceptions during resolve/check
                    print(f"Warning: Error processing path '{folder_path_str}' on line {i}. Error: {e}", file=sys.stderr)
                    exists = False
                    line_warnings += 1

                entries.append({
                    'path_original': folder_path_str,
                    'path_resolved': path_resolved_str, # Use resolved path string for display
                    'description': description,
                    'exists': exists,
                    'name': Path(folder_path_str).name # Get folder name from original string for heading consistency
                })

        if line_warnings > 0:
             print(f"-> Found {line_warnings} potential issues in config file lines (see warnings above).", file=sys.stderr)

    except Exception as e:
        print(f"Error reading config file '{config_file}': {e}", file=sys.stderr)
        sys.exit(1)

    # Generate Markdown Output
    print(f"Generating Markdown output to: {output_file}")
    try:
        timestamp = get_local_timestamp() # Use local timezone

        # Create parent directories if they don't exist
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with output_file.open('w', encoding='utf-8') as f:
            f.write("# Work Folder Quick Reference\n\n")
            f.write(f"_Generated on: {timestamp}_\n\n")
            f.write("---\n\n") # Horizontal rule

            if not entries:
                f.write("No folder entries found or processed from the configuration file.\n")
            else:
                # Entries are already in the order they appeared in the config file
                for entry in entries:
                    f.write(f"## {entry['name']}\n\n")
                    # Display resolved path, fallback to original if needed
                    f.write(f"* **Location:** `{entry['path_resolved']}`\n")
                    if not entry['exists']:
                        f.write(f"    * **(Warning: Path may not exist or is not a directory at generation time)**\n")
                    # Use the user provided description
                    f.write(f"* **Purpose/Notes:** {entry['description']}\n\n")
                    f.write("---\n\n") # Separator between entries

        print(f"\nSuccessfully generated folder reference: {output_file.resolve()}")
        if line_warnings > 0:
             print("Note: Review warnings printed earlier regarding config file lines or path checks.", file=sys.stderr)


    except IOError as e:
        print(f"Error: Could not write to output file '{output_file}': {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred during Markdown generation: {e}", file=sys.stderr)
        sys.exit(1)


# --- Main Execution & Argument Parsing ---
def main():
    """Parses command-line arguments and runs the appropriate action."""
    # Use the script's base name (e.g., folder_documenter.py) in help messages
    prog_name = os.path.basename(sys.argv[0])

    parser = argparse.ArgumentParser(
        prog=prog_name, # Set the program name for help messages
        description="Folder Documentation Assistant: Scan folders or generate Markdown notes from a list.",
        formatter_class=argparse.RawDescriptionHelpFormatter, # Preserve formatting in epilog
        epilog=f"Workflow: Use 'scan' to create a list, edit it, then use 'generate'."
    )
    # Make subparsers required in Python 3.7+ style
    subparsers = parser.add_subparsers(dest='command', required=True, help='Available commands')

    # --- Scan command ---
    parser_scan = subparsers.add_parser(
        'scan',
        help="Scan a directory to generate a preliminary folder list (.txt) for editing.",
        description="Scans a directory up to a specified depth and generates a list of found subfolders formatted for use as input with the 'generate' command.",
        epilog=f"""
Example usage:
  python {prog_name} scan . -d 1 -o my_scan.txt
  python {prog_name} scan "C:\\Work" --depth 2 --ignore-dir "Temp" --ignore-dir "Archive*"
        """
    )
    parser_scan.add_argument(
        "start_dir",
        help="The starting directory path to scan."
        )
    parser_scan.add_argument(
        "-d", "--depth",
        type=int,
        default=1,
        help="Maximum depth to scan folders relative to start_dir (0=no subfolders, 1=immediate subdirs, etc.). Default: 1"
        )
    parser_scan.add_argument(
        "-o", "--output",
        default=DEFAULT_SCAN_OUTPUT_FILENAME,
        help=f"Path for the output text file (default: {DEFAULT_SCAN_OUTPUT_FILENAME})"
        )
    parser_scan.add_argument(
        "--ignore-dir",
        action="append",
        metavar="PATTERN",
        help="Directory name/pattern to ignore (fnmatch wildcards like 'Temp*'). Can be used multiple times."
        )
    parser_scan.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden directories (starting with '.'). Default ignores might still apply."
        )
    parser_scan.add_argument(
        "--separator",
        default=DEFAULT_SEPARATOR,
        help=f"Separator character to use between path and description in the output file (default: '{DEFAULT_SEPARATOR}')"
        )
    parser_scan.set_defaults(func=run_scan_action) # Link scan command to its function

    # --- Generate command ---
    parser_generate = subparsers.add_parser(
        'generate',
        help="Generate the final Markdown notes from a prepared text file.",
        description="Generates a Markdown reference page from a text file listing folder paths and descriptions.",
         epilog=f"""
Example usage:
  python {prog_name} generate folder_list_for_editing.txt
  python {prog_name} generate my_edited_list.txt -o MyNotes.md --separator ::
        """
    )
    parser_generate.add_argument(
        "config_file",
        help="Path to the text file containing folder paths and descriptions (one per line, path<separator>description)."
        )
    parser_generate.add_argument(
        "-o", "--output",
        default=DEFAULT_GENERATE_OUTPUT_FILENAME,
        help=f"Path for the output Markdown file (default: {DEFAULT_GENERATE_OUTPUT_FILENAME})"
        )
    parser_generate.add_argument(
        "--separator",
        default=DEFAULT_SEPARATOR,
        help=f"Separator character used in the config file to separate path from description (default: '{DEFAULT_SEPARATOR}')"
        )
    parser_generate.set_defaults(func=run_generate_action) # Link generate command to its function

    # Parse args and call the appropriate function assigned to 'func'
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()