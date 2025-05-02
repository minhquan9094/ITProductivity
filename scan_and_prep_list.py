import argparse
import datetime
from pathlib import Path
import fnmatch
import sys

# --- Default Ignore Patterns ---
# Common directories to exclude from the scan
DEFAULT_IGNORE_DIRS = [
    '.git', '__pycache__', '.venv', 'venv', 'env',
    'node_modules', '.vscode', '.idea', 'build', 'dist',
    '*.egg-info', '$RECYCLE.BIN', 'System Volume Information'
]
# --- End Default Ignore Patterns ---

# Global list to store discovered folder absolute path strings
discovered_paths = []

def find_folders_recursive(
    current_path: Path,
    start_path: Path,
    current_depth: int,
    max_depth: int,
    include_hidden: bool,
    ignore_patterns: list):
    """
    Recursively finds folders up to max_depth and adds their absolute paths
    to the global discovered_paths list.
    """
    global discovered_paths

    # --- Check if current folder should be processed/added ---
    # We typically skip adding the start directory itself (depth 0)
    # as we want the list of folders *inside* it.
    if current_depth > 0:
            # Apply ignore filters before adding the path
            if any(fnmatch.fnmatch(current_path.name, pattern) for pattern in ignore_patterns):
                return # Don't add or scan deeper
            if not include_hidden and current_path.name.startswith('.'):
                return # Don't add or scan deeper

            # Add the absolute path string to our list
            try:
                discovered_paths.append(str(current_path.resolve()))
            except Exception as e:
                # Handle cases where resolving might fail (e.g., dangling symlink)
                print(f"Warning: Could not resolve path for '{current_path}', skipping. Error: {e}")
                return


    # --- Stop Recursion if max depth reached ---
    # No need to look inside folders at the max_depth level
    if current_depth >= max_depth:
        return

    # --- Scan Subdirectories ---
    try:
        sub_dirs_to_scan = []
        # Use try-except around iterdir for permission issues on the current_path itself
        for item in current_path.iterdir():
            # Check if it's a directory
            # Add basic error handling for stat calls (e.g. broken symlinks)
            try:
                if item.is_dir():
                    # Apply filters *before* adding to the list for recursion
                    if any(fnmatch.fnmatch(item.name, pattern) for pattern in ignore_patterns):
                        continue # Ignore pattern matched
                    if not include_hidden and item.name.startswith('.'):
                        continue # Hidden directory ignored
                    sub_dirs_to_scan.append(item)
            except OSError as stat_error:
                 print(f"Warning: Could not access attributes of '{item.name}' in '{current_path}'. Skipping. Error: {stat_error}")
            except Exception as general_error:
                 print(f"Warning: Unexpected error checking item '{item.name}' in '{current_path}'. Skipping. Error: {general_error}")


        # Sort for consistent order
        sub_dirs_to_scan.sort(key=lambda p: p.name.lower())

        # Recurse into valid subdirectories
        for sub_dir in sub_dirs_to_scan:
                find_folders_recursive(
                    sub_dir,
                    start_path,
                    current_depth + 1, # Increment depth
                    max_depth,
                    include_hidden,
                    ignore_patterns
                )

    except PermissionError:
        # Note permission error for the directory we tried to scan *into*
        print(f"Warning: Permission denied scanning inside '{current_path}'")
    except FileNotFoundError:
        print(f"Warning: Folder '{current_path}' not found during scan (might have been deleted).")
    except Exception as e:
        # Catch other potential errors during directory iteration
        print(f"Warning: Error scanning inside '{current_path}': {e}")


def generate_folder_list_for_input(
    start_dir_path: str,
    output_file_path: str,
    max_depth: int,
    include_hidden: bool,
    user_ignore_dirs: list | None,
    separator: str = '|'):
    """
    Sets up and runs the folder scan, then writes the results to a text file
    formatted as input for the generate_folder_notes.py script.
    """
    global discovered_paths
    discovered_paths = [] # Ensure the list is empty before starting

    start_dir = Path(start_dir_path).resolve() # Get absolute path
    output_file = Path(output_file_path)

    if not start_dir.is_dir():
        print(f"Error: Start directory not found or is not a directory: '{start_dir}'")
        return

    # Combine default and user ignore patterns
    ignore_patterns = DEFAULT_IGNORE_DIRS + (user_ignore_dirs or [])

    print(f"Scanning directory: {start_dir}")
    print(f"Maximum depth: {max_depth}")
    print(f"Include hidden: {include_hidden}")
    print(f"Ignoring patterns: {ignore_patterns}")
    print(f"Output file: {output_file}")
    print("-" * 30)

    # Start the recursive scanning process
    find_folders_recursive(
        start_dir,
        start_dir,
        0, # Initial depth is 0
        max_depth,
        include_hidden,
        ignore_patterns
    )

    print("-" * 30)
    print(f"Scan complete. Found {len(discovered_paths)} subfolders matching criteria.")

    # Write the collected paths to the output file
    try:
        # Get current time using timezone information if possible
        try:
            timestamp = datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
        except Exception:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with output_file.open('w', encoding='utf-8') as f:
            # Write header comments explaining the file format and purpose
            f.write(f"# Automatically generated list of folders found in: {start_dir}\n")
            f.write(f"# Maximum Scan Depth Relative to Start: {max_depth}\n")
            f.write(f"# Generated on: {timestamp} (Vietnam Time)\n") # Added location context
            f.write("#\n")
            f.write("# Instructions for use with 'generate_folder_notes.py':\n")
            f.write("# 1. Review the folder paths below.\n")
            f.write("# 2. Delete lines for folders you don't want to include in your final notes.\n")
            f.write(f"# 3. Replace 'PLEASE ADD DESCRIPTION' after the '{separator}' with your notes for each folder.\n")
            f.write("# 4. Save this file.\n")
            f.write("# 5. Run: python generate_folder_notes.py <this_file_name>.txt -o final_notes.md\n")
            f.write("#---------------------------------------------------------------------------\n\n")

            if not discovered_paths:
                f.write("# No subfolders found matching the criteria.\n")
            else:
                # Sort the paths alphabetically for consistency and easier editing
                discovered_paths.sort()
                for path_str in discovered_paths:
                    # Write in the specific format: path separator description
                    f.write(f"{path_str} {separator} PLEASE ADD DESCRIPTION\n")

        print(f"\nSuccessfully generated folder list for editing: {output_file.resolve()}")
        print("Next steps:")
        print(f" 1. Edit the file '{output_file.name}' to add descriptions and remove unwanted lines.")
        print(f" 2. Run 'python generate_folder_notes.py {output_file.name}' to create the final Markdown for OneNote.")


    except IOError as e:
        print(f"Error writing to output file '{output_file}': {e}")
    except Exception as e:
        print(f"An unexpected error occurred during file writing: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scans a directory up to a specified depth and generates a list of found folders formatted for use as input with 'generate_folder_notes.py'.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan current directory (depth 1), output to 'folder_list_for_editing.txt'
  python scan_and_prep_list.py .

  # Scan 'C:\\Work' (depth 2), output to 'Work_prep.txt'
  python scan_and_prep_list.py "C:\\Work" -d 2 -o Work_prep.txt

  # Scan 'Documents' (depth 1), include hidden, ignore 'Archive', use '::' separator
  python scan_and_prep_list.py Documents -d 1 --include-hidden --ignore-dir Archive --separator ::
        """
    )
    parser.add_argument(
        "start_dir",
        help="The starting directory path to scan."
    )
    parser.add_argument(
        "-d", "--depth",
        type=int,
        default=1,
        help="Maximum depth to scan folders relative to start_dir (0=no subfolders, 1=immediate subdirs, etc.). Default: 1"
    )
    parser.add_argument(
        "-o", "--output",
        default="folder_list_for_editing.txt", # Default output is now a .txt file
        help="Path for the output text file (default: folder_list_for_editing.txt)"
    )
    parser.add_argument(
        "--ignore-dir",
        action="append",
        default=[],
        metavar="PATTERN",
        help="Directory name/pattern to ignore (e.g., 'temp', 'build*'). Uses fnmatch wildcards. Can be used multiple times."
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden directories (those starting with '.'). Default ignores like '.git' might still apply."
    )
    # Added separator option consistent with generate_folder_notes.py
    parser.add_argument(
        "--separator",
        default="|",
        help="The separator character to use between path and description in the output file (default: '|'). Should match the one used by generate_folder_notes.py."
    )

    args = parser.parse_args()

    if args.depth < 0:
        print("Error: Depth cannot be negative.")
    else:
            generate_folder_list_for_input(
                start_dir_path=args.start_dir,
                output_file_path=args.output,
                max_depth=args.depth,
                include_hidden=args.include_hidden,
                user_ignore_dirs=args.ignore_dir,
                separator=args.separator # Pass the separator
            )