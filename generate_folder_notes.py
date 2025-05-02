import argparse
import datetime
from pathlib import Path
import sys

def generate_folder_reference(config_file_path: str, output_file_path: str, separator: str = '|'):
    """
    Generates a Markdown reference page for specified folders and their descriptions
    based on an input text file.
    """
    config_file = Path(config_file_path)
    output_file = Path(output_file_path)

    # Get current time using timezone information if possible
    try:
        # This relies on the system's timezone setting
        timestamp = datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception:
        # Fallback if timezone info isn't available easily
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not config_file.is_file():
        print(f"Error: Configuration file not found at '{config_file}'")
        return

    entries = []
    print(f"Reading configuration from: {config_file}")
    try:
        with config_file.open('r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                line = line.strip()
                if not line or line.startswith('#'): # Skip empty lines and comments
                    continue
                if separator not in line:
                    print(f"Warning: Skipping line {i+1} in config file - missing separator '{separator}': {line}")
                    continue

                parts = line.split(separator, maxsplit=1)
                folder_path_str = parts[0].strip()
                description = parts[1].strip()

                if not folder_path_str or not description:
                    print(f"Warning: Skipping line {i+1} - empty path or description.")
                    continue

                # Resolve the path to make it absolute and check existence
                try:
                    # Use resolve(strict=False) on Windows in case of network paths
                    # that might temporarily not be accessible but are valid syntax.
                    # On non-Windows, strict=True is usually fine.
                    is_windows = sys.platform.startswith('win')
                    folder_path = Path(folder_path_str).resolve(strict=not is_windows)
                    exists = folder_path.is_dir() # Check if it's actually a directory
                    path_resolved_str = str(folder_path)
                except FileNotFoundError:
                     # Path doesn't exist or strict=True failed
                     exists = False
                     # Keep the original string, maybe add note it's not absolute/resolved
                     path_resolved_str = f"{folder_path_str} (Could not resolve fully)"
                except OSError as oe:
                     # Other OS errors, e.g. permissions, invalid network path format
                     print(f"Warning: OS error checking path '{folder_path_str}' on line {i+1}: {oe}")
                     exists = False
                     path_resolved_str = f"{folder_path_str} (Error checking path)"
                except Exception as e: # Catch other potential Path exceptions
                    print(f"Warning: Error processing path '{folder_path_str}' on line {i+1}: {e}")
                    exists = False
                    path_resolved_str = f"{folder_path_str} (Error processing path)"


                entries.append({
                    'path_original': folder_path_str, # Keep original string for display
                    'path_resolved': path_resolved_str,
                    'description': description,
                    'exists': exists,
                    'name': Path(folder_path_str).name # Get the folder name itself from original string
                })

    except Exception as e:
        print(f"Error reading config file '{config_file}': {e}")
        return

    # Generate Markdown Output
    print(f"Generating Markdown output to: {output_file}")
    try:
        with output_file.open('w', encoding='utf-8') as f:
            f.write("# Work Folder Quick Reference\n\n")
            f.write(f"_Generated on: {timestamp} (Vietnam Time)_\n\n") # Added location context
            f.write("---\n\n") # Horizontal rule

            if not entries:
                    f.write("No folder entries found in the configuration file.\n")
            else:
                for entry in entries:
                    # Use the folder name from the original path for the heading
                    f.write(f"## {entry['name']}\n\n")
                    # Display the original path provided by the user for easy recognition
                    f.write(f"* **Location:** `{entry['path_original']}`\n")
                    if not entry['exists']:
                            # Add a clear warning if the path wasn't found or isn't a directory
                            f.write(f"    * **(Warning: Path may not exist or is not a directory)**\n")
                    f.write(f"* **Purpose/Notes:** {entry['description']}\n\n")
                    f.write("---\n\n") # Separator between entries

        print(f"Successfully generated folder reference: {output_file.resolve()}")

    except IOError as e:
        print(f"Error writing to output file '{output_file}': {e}")
    except Exception as e:
        print(f"An unexpected error occurred during generation: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a Markdown reference page for specified folders and their descriptions from a config file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Configuration file format (e.g., my_folders.txt):
  # Lines starting with # are comments and ignored
  /path/to/folder | Description for the folder
  C:\\Work\\ProjectX | Client files for Project X, includes designs.

Example usage:
  # Using default separator '|' and output file 'folder_reference.md'
  python generate_folder_notes.py my_work_folders.txt

  # Specifying output file and using '::' as separator
  python generate_folder_notes.py config.txt -o my_notes.md --separator ::
        """
    )
    parser.add_argument(
        "config_file",
        help="Path to the text file containing folder paths and descriptions (one per line)."
    )
    parser.add_argument(
        "-o", "--output",
        default="folder_reference.md",
        help="Path for the output Markdown file (default: folder_reference.md)"
    )
    parser.add_argument(
        "--separator",
        default="|",
        help="The character sequence used to separate the folder path from its description in the config file (default: '|')"
    )
    args = parser.parse_args()
    generate_folder_reference(args.config_file, args.output, args.separator)