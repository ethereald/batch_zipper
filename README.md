# Batch Zipper/Unzipper GUI

**Author:** Kelvin
**Date:** July 2025
**Version:** 1.0.0.1
**Description:** Tkinter-based GUI for batch zipping/unzipping folders using JSON encoding, with progress bar and console log. This tool provides a user-friendly interface to manage multiple files and directories efficiently.

## Features

*   **Configuration Management:** Stores a list of directories to be zipped or unzipped in a configuration file (`directory.config`).
*   **Power User Mode:** Enables password protection for the configuration file, enhancing security.
*   **Add/Remove Paths:** Easily add or remove directories from the configuration list.
*   **Zip and Unzip Operations:** Perform zip and unzip operations on selected directories with a progress bar.
*   **Progress Bar:** Displays real-time progress during long-running operations.
*   **Console Log:** Provides a detailed log of actions performed by the GUI, aiding in troubleshooting.
*   **All Operations:** Zip or unzipping all configured paths with one click.

## Requirements

*   Python 3.x
*   Tkinter (included in standard Python installation)
*   `zipper` package (install using `pip install zipper`)

## Usage

1.  **Run the script:** Execute `python batch_zipper_gui.py`.
2.  **Power User Mode (Optional):** Check the "Power User Mode" checkbox to enable password protection for the configuration file. If enabled, you'll be prompted to enter a password when accessing the configuration.
3.  **Add Directories:** Click the "Add Path" button and select the directories you want to include in the zip/unzip operation.
4.  **Select Directories:** Select one or more directories from the listbox.
5.  **Zip/Unzip:** Click either the "Zip Selected" or "Unzip Selected" button to perform the desired operation.
6.  **Monitor Progress:** The progress bar and console log will display the status of the operation.

## Configuration File (`directory.config`)

The configuration file stores the list of directories to be zipped/unzipped. It's a JSON file with the following structure:

```json
{
  "meta": {
    "pw": "encoded_password"
  },
  "paths": [
    "path/to/directory1",
    "path/to/directory2"
  ]
}
```

*   `meta.pw`: Encoded password for Power User Mode (if enabled).
*   `paths`: List of absolute paths to the directories to be zipped or unzipped.

## Included Tools

This GUI utilizes several helper scripts:

*   **`zipper.py`:**  The core script responsible for performing the actual zipping and unzipping operations using the `zipper` package. It handles chunking large files for efficient compression and decompression.
*   **`rename_by_date.py`:** This script renames files in a directory based on their last modified date, prepending a prefix to ensure unique filenames.

## Notes

*   The `zipper` package is required for this script to function. Install it using `pip install zipper`.
*   Ensure that the specified paths are valid and accessible.
*   Consider using relative paths in the configuration file for portability.
*   The console log provides valuable information about the operation's progress and any potential errors.

## Author

Kelvin