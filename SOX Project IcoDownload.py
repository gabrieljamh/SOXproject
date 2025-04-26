import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QFileDialog,
                             QVBoxLayout, QMessageBox, QLabel, QSizePolicy, QSpacerItem,
                             QProgressBar) # Import QProgressBar
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon
import json
import os
import requests
from urllib.parse import urlparse
import re
import hashlib

class JSONTransformer(QWidget):
    def __init__(self):
        super().__init__()
        # Initialize attribute to store the loaded JSON data (optional for this script, but kept)
        # and filename
        self.inputJson = None
        self._input_filename = None  # Store filename

        # Keep references to widgets that need state changes
        self.loadedFileLabel = None
        self.progressBar = None # Add attribute for the progress bar

        self.initUI()

    def initUI(self):
        # Create GUI components
        # Removed textSpacer - will use QSpacerItem
        textDesc = QLabel("Welcome to S.O.X. Project! This tool aims to convert XoulAI JSONs into TavernAI usable JSONs.\nThis one is dedicated to simply download every icon/avatar on the JSON file")
        textCredits = QLabel("<i>by Junji Dragonfox @ Project BomberCraft</i>")

        # --- The single functional button ---
        self.loadButton = QPushButton("Get XoulAI JSON & Download Avatars")
        # --- End button setup ---

        creditButton = QPushButton("SEE CREDITS")
        textInput = QLabel("VV Station XoulAI VV")
        # textOutput label is not strictly needed as there's no separate export step
        # textOutput = QLabel("<i>-->> Next Station: TavernAI -->></i>")

        # --- Create label to display loaded file ---
        self.loadedFileLabel = QLabel("No file selected")
        self.loadedFileLabel.setAlignment(Qt.AlignCenter)
        # --- End loaded file label ---

        # --- Create the progress bar ---
        self.progressBar = QProgressBar()
        self.progressBar.setAlignment(Qt.AlignCenter) # Center the percentage text
        self.progressBar.setRange(0, 0) # Initial state: 0%
        # self.progressBar.setVisible(False) # Optionally hide it until a file is selected
        # --- End progress bar ---


        imageLabel = QLabel()

        # --- Widget Properties ---
        imageLabel.setAlignment(Qt.AlignCenter)
        textDesc.setAlignment(Qt.AlignCenter)
        textCredits.setAlignment(Qt.AlignRight)
        textCredits.setTextFormat(Qt.RichText)
        textCredits.setOpenExternalLinks(True)  # QLabel typically cannot open links
        textInput.setAlignment(Qt.AlignCenter)
        # textOutput.setAlignment(Qt.AlignCenter) # Removed
        # textOutput.setTextFormat(Qt.RichText) # Removed
        # textOutput.setOpenExternalLinks(True) # Removed

        # Set an image - Added error handling
        try:
            pixmap = QPixmap('SOX.png')
            if pixmap.isNull():
                print("Warning: Could not load SOX.png. Make sure it's in the same directory as the script.")
                imageLabel.setText("SOX Image Placeholder")
            else:
                # Optional: Scale image if too large
                # pixmap = pixmap.scaled(300, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                imageLabel.setPixmap(pixmap)
        except Exception as e:
            print(f"Error loading image: {e}")
            imageLabel.setText("SOX Image Placeholder")

        # --- Layout the UI using QSpacerItem ---
        layout = QVBoxLayout()

        # Top section: Image and Description
        layout.addWidget(imageLabel, alignment=Qt.AlignCenter)
        layout.addWidget(textDesc, alignment=Qt.AlignCenter)

        # Add flexible space
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Middle section: Input/Load & Progress
        layout.addWidget(textInput, alignment=Qt.AlignCenter)
        layout.addWidget(self.loadButton) # Use self.loadButton reference
        layout.addWidget(self.loadedFileLabel, alignment=Qt.AlignCenter) # Add label for file
        layout.addWidget(self.progressBar) # Add the progress bar here

        # Add a fixed space between Load/Process and Credits sections
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Removed textOutput and its spacer

        # Bottom section: Credits
        # Add flexible space to push credits to the bottom
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)) # Push to bottom
        layout.addWidget(textCredits, alignment=Qt.AlignRight)
        layout.addWidget(creditButton, alignment=Qt.AlignRight)

        # --- Connections ---
        self.loadButton.clicked.connect(self.getAvatars) # Connect using self.loadButton
        creditButton.clicked.connect(self.creditsWND)

        # --- Window Setup ---
        self.setLayout(layout)
        self.setWindowTitle("S.O.X. EXTRAS - Avatar/Icon Downloader")
        # Set Window Icon - Added error handling
        try:
            icon = QIcon('SOXico.png')
            if icon.isNull():
                print("Warning: Could not load SOXico.png for window icon.")
            else:
                self.setWindowIcon(icon)
        except Exception as e:
            print(f"Error loading icon: {e}")


    def creditsWND(self):
        # Use triple quotes for multi-line string
        info_text = """
R.I.P. XoulAI, we hope you return someday, thanks for the moments.

Testers:
TBA

V0.0.1
"""
        QMessageBox.information(self, "CREDITS", info_text.strip())  # Use strip() for cleaner message


    def getAvatars(self):
        """
        Opens file/directory dialogs, reads JSON, finds image URLs, downloads them,
        and saves them to the output directory. Shows progress with a progress bar.
        """
        self.loadedFileLabel.setText("No file selected") # Reset label at start
        self.progressBar.setRange(0, 0) # Reset progress bar
        self.progressBar.setValue(0)

        # 1. Get JSON file path
        json_path, _ = QFileDialog.getOpenFileName(
            self, "Select XoulAI JSON File", '', 'JSON files (*.json);;All Files (*)'
        )
        if not json_path:
            self.loadedFileLabel.setText("File selection cancelled")
            return # User cancelled

        self._input_filename = json_path # Store filename
        self.loadedFileLabel.setText(f"Selected: {os.path.basename(json_path)}") # Display filename


        # 2. Get output directory path
        output_dir = QFileDialog.getExistingDirectory(
            self, f"Select Directory to Save Avatars from {os.path.basename(json_path)}"
        )
        if not output_dir:
            self.loadedFileLabel.setText(f"Selected: {os.path.basename(json_path)}") # Keep file name displayed
            return # User cancelled directory selection

        # Ensure the target directory exists
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
             QMessageBox.critical(self, "Directory Error", f"Failed to create or access output directory:\n{output_dir}\n{e}")
             self.loadedFileLabel.setText("Error accessing directory")
             return


        json_data = None
        try:
            # 3. Read and parse JSON - Added encoding and specific error handling
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)

            # Basic check if it's a dictionary or list (most JSONs are one of these)
            if not isinstance(json_data, (dict, list)):
                QMessageBox.warning(self, "JSON Structure Warning", f"Top level element in '{os.path.basename(json_path)}' is not a dictionary or list. Found {type(json_data).__name__}.\nAttempting to search anyway, but results may be limited.")
                # Don't return, try to search whatever structure it is

        except FileNotFoundError:
            self.loadedFileLabel.setText("File not found")
            QMessageBox.critical(self, "Error", f"File not found: {json_path}")
            return
        except json.JSONDecodeError as e:
            self.loadedFileLabel.setText("JSON Error")
            QMessageBox.critical(self, "JSON Parsing Error", f"Failed to parse JSON from file:\n{json_path}\n{e}")
            return
        except UnicodeDecodeError as e:
            self.loadedFileLabel.setText("Encoding Error")
            QMessageBox.critical(self, "Encoding Error", f"Failed to read file with UTF-8 encoding:\n{json_path}\n{e}\n\nTry opening it in a text editor and saving as UTF-8.")
            return
        except Exception as e:
            self.loadedFileLabel.setText("File Read Error")
            QMessageBox.critical(self, "Error", f"An unexpected error occurred while reading the file:\n{json_path}\n{e}")
            return

        if json_data is None: # Should have returned earlier, but safe check
             self.loadedFileLabel.setText("Loading failed")
             QMessageBox.information(self, "Info", "No data loaded from JSON.")
             return

        # --- Helper functions for finding and downloading images (refined) ---

        def is_potential_image_url(url_string):
            """Checks if a string looks like a potential image URL (http/https + common extension)."""
            if not isinstance(url_string, str):
                return False
            url_string_lower = url_string.lower()
            if url_string_lower.startswith(('http://', 'https://')):
                 parsed_url = urlparse(url_string_lower)
                 path = parsed_url.path
                 _, ext = os.path.splitext(path)
                 image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg')
                 if ext in image_extensions:
                      return True
            return False


        def find_image_urls_recursive(data, found_urls, depth=0, max_depth=20):
            """Recursively finds potential image URLs in nested JSON structures up to a max depth."""
            if depth > max_depth:
                return

            if isinstance(data, dict):
                for key, value in data.items():
                    if is_potential_image_url(value):
                         found_urls.add(value)
                    # Optional: check key name hints
                    # if isinstance(value, str) and any(keyword in key.lower() for keyword in ('avatar', 'icon', 'image', 'image_url', 'url')):
                    #    if is_potential_image_url(value): found_urls.add(value)

                    find_image_urls_recursive(value, found_urls, depth + 1, max_depth)

            elif isinstance(data, list):
                for item in data:
                    if is_potential_image_url(item):
                         found_urls.add(item)
                    find_image_urls_recursive(item, found_urls, depth + 1, max_depth)

            elif isinstance(data, str):
                if is_potential_image_url(data):
                    found_urls.add(data)


        def get_safe_filename_from_url(url, directory):
            """Generates a safe and unique filename based on the URL in the directory."""
            parsed_url = urlparse(url)
            original_filename = os.path.basename(parsed_url.path)

            if not original_filename:
                 original_filename = "downloaded_image"

            safe_filename = re.sub(r'[^\w\-_\.]', '_', original_filename)

            if not safe_filename or all(c in '_.' for c in safe_filename):
                 hash_object = hashlib.md5(url.encode()).hexdigest()
                 safe_filename = f"hashed_image_{hash_object[:8]}"

            if safe_filename.startswith('.'):
                 safe_filename = '_' + safe_filename[1:]


            name, ext = os.path.splitext(safe_filename)
            common_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg')
            if not ext or ext.lower() not in common_extensions:
                 if '.png' in url.lower(): ext = '.png'
                 elif '.jpg' in url.lower() or '.jpeg' in url.lower(): ext = '.jpg'
                 elif '.gif' in url.lower(): ext = '.gif'
                 else: ext = ".png" # Default fallback

                 safe_filename = f"{name}{ext}"


            output_path = os.path.join(directory, safe_filename)

            counter = 1
            base_name, file_ext = os.path.splitext(output_path)
            while os.path.exists(output_path):
                output_path = f"{base_name}_{counter}{file_ext}"
                counter += 1

            return output_path

        # --- Main download execution ---

        found_urls = set() # Use a set to avoid duplicate URLs
        find_image_urls_recursive(json_data, found_urls)

        total_urls = len(found_urls)

        if total_urls == 0:
            QMessageBox.information(self, "Info", "No potential image URLs found in the JSON file.")
            self.loadedFileLabel.setText(f"Processed: {os.path.basename(json_path)} (No URLs found)")
            self.progressBar.setRange(0, 0) # Reset progress bar
            self.progressBar.setValue(0)
            return

        # --- Set up progress bar ---
        self.progressBar.setRange(0, total_urls)
        self.progressBar.setValue(0)
        # self.progressBar.setVisible(True) # Make visible if it was hidden
        # --- End progress bar setup ---


        download_count = 0 # Count successful downloads
        processed_urls_count = 0 # Count URLs attempted
        failed_downloads = {} # Store failed URLs and reasons

        QApplication.setOverrideCursor(Qt.WaitCursor) # Show busy cursor
        self.loadButton.setEnabled(False) # Disable button during download

        try:
            for url in found_urls:
                output_path = None
                try:
                    output_path = get_safe_filename_from_url(url, output_dir)

                    # Use timeout and handle request errors
                    response = requests.get(url, stream=True, timeout=15) # Increased timeout slightly
                    response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

                    with open(output_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)

                    download_count += 1
                    print(f"Successfully downloaded: {url} -> {os.path.basename(output_path)}")

                except requests.exceptions.Timeout:
                     failed_downloads[url] = f"Timeout occurred after 15 seconds."
                     print(f"Failed to download {url}: Timeout")
                except requests.exceptions.ConnectionError as e:
                    failed_downloads[url] = f"Connection error: {e}"
                    print(f"Failed to download {url}: Connection error: {e}")
                except requests.exceptions.HTTPError as e:
                     failed_downloads[url] = f"HTTP error: {e.response.status_code} {e.response.reason}"
                     print(f"Failed to download {url}: HTTP error: {e.response.status_code}")
                except requests.exceptions.RequestException as e:
                    failed_downloads[url] = f"Request error: {e}"
                    print(f"Failed to download {url}: Request error: {e}")
                except IOError as e:
                    failed_downloads[url] = f"File writing error: {e} (Path: {output_path})"
                    print(f"Failed to write file for {url}: {e} (Path: {output_path})")
                except Exception as e:
                    failed_downloads[url] = f"An unexpected error occurred during download: {e}"
                    print(f"An unexpected error occurred while processing {url}: {e}")

                finally:
                    # --- Update progress bar ---
                    processed_urls_count += 1
                    self.progressBar.setValue(processed_urls_count)
                    QApplication.processEvents() # Keep the GUI responsive by processing events
                    # --- End update ---

        finally:
             QApplication.restoreOverrideCursor() # Restore cursor even if errors occur
             self.loadButton.setEnabled(True) # Re-enable button

        # 4. Provide Feedback
        failed_count = len(failed_downloads)
        success_count = download_count # This is the count of successful downloads

        message = f"Avatar/Icon Download Process Finished.\n"
        message += f"Total potential URLs found in JSON: {total_urls}\n"
        message += f"Successfully downloaded: {success_count}\n"
        message += f"Failed downloads: {failed_count}"

        if failed_count > 0:
            message += "\n\nDetails of failures have been printed to the console."

        QMessageBox.information(self, "Download Complete", message)
        self.loadedFileLabel.setText(f"Processed: {os.path.basename(json_path)} ({success_count}/{total_urls} downloaded)")


    def run(self):
        self.show()


if __name__ == '__main__':
    # Optional: High-DPI scaling setup
    # from PyQt5.QtCore import QT_VERSION_STR
    # print(f"PyQt5 version: {QT_VERSION_STR}")
    # if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    #     QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    # if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
    #      QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    transformer = JSONTransformer()
    transformer.run()
    sys.exit(app.exec_())