import os
import re
import shutil

def organize_log_files():
    """
    Organizes log files in the current directory into date-based folders.

    Looks for files ending in '.log', extracts the date from the filename
    (assuming the format YYYYMMDD), creates a folder named YYYY-MM-DD
    if it doesn't exist, and moves the log file into that folder.
    """
    current_directory = os.getcwd()
    print(f"Starting log file organization in: {current_directory}")

    # Regex to find the date pattern YYYYMMDD in the filename
    # It looks for 8 digits preceded by a hyphen and followed by a hyphen
    date_pattern = re.compile(r'-(\d{8})-')

    # Iterate through all items in the current directory
    for item_name in os.listdir(current_directory):
        item_path = os.path.join(current_directory, item_name)

        # Check if the item is a file and ends with .log
        if os.path.isfile(item_path) and item_name.endswith('.log'):
            print(f"Processing file: {item_name}")

            # Try to find the date in the filename using the regex
            match = date_pattern.search(item_name)

            if match:
                date_str_yyyymmdd = match.group(1) # Extract the YYYYMMDD part
                # Format the date as YYYY-MM-DD for the folder name
                date_folder_name = f"{date_str_yyyymmdd[:4]}-{date_str_yyyymmdd[4:6]}-{date_str_yyyymmdd[6:]}"
                date_folder_path = os.path.join(current_directory, date_folder_name)

                # Create the date folder if it doesn't exist
                if not os.path.exists(date_folder_path):
                    print(f"Creating directory: {date_folder_name}")
                    os.makedirs(date_folder_path)

                # Define the destination path for the log file
                destination_path = os.path.join(date_folder_path, item_name)

                # Move the log file to the date folder
                try:
                    shutil.move(item_path, destination_path)
                    print(f"Moved '{item_name}' to '{date_folder_name}'")
                except Exception as e:
                    print(f"Error moving file {item_name}: {e}")
            else:
                print(f"Could not find date pattern in filename: {item_name}")
        # Optional: Add an else here if you want to print messages for non-log files or directories
        # else:
        #     print(f"Skipping item: {item_name} (not a log file)")

    print("Log file organization complete.")

# Run the organization function when the script is executed
if __name__ == "__main__":
    organize_log_files()
