import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QFileDialog, QVBoxLayout, QMessageBox, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import QIcon
import json
import os
import requests # Import the requests library
from urllib.parse import urlparse # Useful for parsing URLs

class JSONTransformer(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        # Create GUI components
        textSpacer = QLabel()
        textDesc = QLabel("Welcome to S.O.X. Project! This tool aims to convert XoulAI JSONs into TavernAI usable JSONs.\nThis one is dedicated to simply download every icon/avatar on the JSON file")
        textCredits = QLabel("<i>by Junji Dragonfox @ Project BomberCraft</i>")
        loadButton = QPushButton("Get XoulAI JSON")
        creditButton = QPushButton("SEE CREDITS")
        textInput = QLabel("VV Station XoulAI VV")
        textOutput = QLabel("<i>-->> Next Station: TavernAI -->></i>")
        imageLabel = QLabel()
        
        imageLabel.setAlignment(Qt.AlignCenter)
        textDesc.setAlignment(Qt.AlignCenter)
        textCredits.setAlignment(Qt.AlignRight)
        textCredits.setTextFormat(Qt.RichText)
        textCredits.setOpenExternalLinks(True)
        textInput.setAlignment(Qt.AlignCenter)
        textOutput.setAlignment(Qt.AlignCenter)
        textOutput.setTextFormat(Qt.RichText)
        textOutput.setOpenExternalLinks(True)
        
        # Set an image
        imageLabel.setPixmap(QPixmap('SOX.png'))  # Replace 'your_image.png' with your actual image path
        # Layout the UI
        layout = QVBoxLayout()
        layout.addWidget(imageLabel)
        layout.addWidget(textSpacer)
        layout.addWidget(textDesc)
        layout.addWidget(textSpacer)
        layout.addWidget(textInput)
        layout.addWidget(loadButton)
        layout.addWidget(textSpacer)
        layout.addWidget(textOutput)
        layout.addWidget(textSpacer)
        layout.addWidget(textCredits)
        layout.addWidget(creditButton)
        loadButton.clicked.connect(self.getAvatars)
        creditButton.clicked.connect(self.creditsWND)
        self.setLayout(layout)
    def creditsWND(self):
        QMessageBox.information(self, "CREDITS", "R.I.P. XoulAI, we hope you return someday, thanks for the moments.\n\nTesters:\n\nTBA\n\nV0.0.1")
    def getAvatars(self):
        """
        Opens a file dialog to select a JSON file, prompts for an output directory,
        finds image URLs within the JSON, downloads them, and saves them to the
        output directory.
        """
        # 1. Get JSON file path
        json_path, _ = QFileDialog.getOpenFileName(
            self, "Select XoulAI JSON File", "", "JSON Files (*.json);;All Files (*)"
        )
        if not json_path:
            return # User cancelled

        # 2. Get output directory path
        output_dir = QFileDialog.getExistingDirectory(
            self, "Select Directory to Save Avatars"
        )
        if not output_dir:
            return # User cancelled

        json_data = None
        try:
            # 3. Read and parse JSON
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", f"File not found: {json_path}")
            return
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", f"Invalid JSON format in file: {json_path}")
            return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred while reading the file: {e}")
            return

        if not json_data:
             QMessageBox.information(self, "Info", "No data loaded from JSON.")
             return

        # --- Helper functions for finding and downloading images ---

        def is_image_url(url_string):
            """Checks if a string looks like a potential image URL."""
            if not isinstance(url_string, str):
                return False
            url_string_lower = url_string.lower()
            # Basic check for common URL schemes and common image extensions
            if url_string_lower.startswith(('http://', 'https://')):
                # Get the path part of the URL, ignoring query parameters or fragments
                parsed_url = urlparse(url_string_lower)
                path = parsed_url.path
                # Check if the path ends with a common image extension
                # Use os.path.splitext for better handling of dots in names
                _, ext = os.path.splitext(path)
                # List of common image extensions (can be expanded)
                image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg')
                return ext in image_extensions
            return False

        def find_image_urls_recursive(data, found_urls):
            """Recursively finds potential image URLs in nested JSON structures."""
            if isinstance(data, dict):
                for key, value in data.items():
                    # Check if the value itself is a string URL
                    if is_image_url(value):
                         found_urls.add(value)
                    # Also check if the key name suggests it might contain an image URL in its value
                    # (e.g., "avatar", "icon", "image_url" - optional but could be helpful)
                    # if isinstance(value, str) and any(keyword in key.lower() for keyword in ('avatar', 'icon', 'image', 'image_url')):
                    #     if is_image_url(value):
                    #         found_urls.add(value)

                    # Recurse into the value
                    find_image_urls_recursive(value, found_urls)
            elif isinstance(data, list):
                for item in data:
                    # Check if the item itself is a string URL
                    if is_image_url(item):
                         found_urls.add(item)
                    # Recurse into the item
                    find_image_urls_recursive(item, found_urls)
            elif isinstance(data, str):
                # Check if the string itself is an image URL
                if is_image_url(data):
                    found_urls.add(data)
            # Ignore other data types (int, float, bool, None)


        def get_unique_filename(directory, url):
            """Generates a safe and unique filename based on the URL in the directory."""
            parsed_url = urlparse(url)
            # Get the base filename from the URL path, removing query params/fragments
            original_filename = os.path.basename(parsed_url.path)

            if not original_filename:
                 # If basename is empty (e.g., url ends with a slash), create a generic name + hash
                 import hashlib
                 hash_object = hashlib.md5(url.encode())
                 original_filename = f"image_{hash_object.hexdigest()[:8]}.png" # Default to png if no extension obvious

            # Sanitize the filename further if necessary (basic replacement of problematic chars)
            safe_filename = "".join(c if c.isalnum() or c in ('_', '.', '-') else '_' for c in original_filename)
            # Ensure it's not empty after sanitization
            if not safe_filename or safe_filename.startswith('.'):
                 import hashlib
                 hash_object = hashlib.md5(url.encode())
                 safe_filename = f"sanitized_image_{hash_object.hexdigest()[:8]}.png"


            name, ext = os.path.splitext(safe_filename)
            if not ext: # Add a default extension if missing
                 ext = ".png"
                 safe_filename = f"{name}{ext}"


            output_path = os.path.join(directory, safe_filename)

            # Check for existing file and append a number if needed
            counter = 1
            while os.path.exists(output_path):
                output_path = os.path.join(directory, f"{name}_{counter}{ext}")
                counter += 1

            return output_path

        # --- Main download logic ---

        found_urls = set() # Use a set to avoid duplicate URLs
        find_image_urls_recursive(json_data, found_urls)

        if not found_urls:
            QMessageBox.information(self, "Info", "No potential image URLs found in the JSON file.")
            return

        download_count = 0
        failed_downloads = {} # Store failed URLs and reasons

        QApplication.setOverrideCursor(Qt.WaitCursor) # Show busy cursor
        try:
            for url in found_urls:
                output_path = None # Define output_path here
                try:
                    # Get unique filename before attempting download
                    output_path = get_unique_filename(output_dir, url)

                    response = requests.get(url, stream=True, timeout=10) # Use stream=True for potentially large files
                    response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

                    # Ensure the directory exists (should already, but good practice)
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)

                    with open(output_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192): # Download in chunks
                            f.write(chunk)

                    download_count += 1

                except requests.exceptions.RequestException as e:
                    failed_downloads[url] = f"Request error: {e}"
                    print(f"Failed to download {url}: {e}") # Print to console for debugging
                except IOError as e:
                    failed_downloads[url] = f"File writing error: {e} (Path: {output_path})"
                    print(f"Failed to write file for {url}: {e} (Path: {output_path})") # Print to console
                except Exception as e:
                    failed_downloads[url] = f"An unexpected error occurred during download: {e}"
                    print(f"An unexpected error occurred while processing {url}: {e}") # Print to console

        finally:
             QApplication.restoreOverrideCursor() # Restore cursor

        # 4. Provide Feedback
        total_urls = len(found_urls)
        failed_count = len(failed_downloads)
        success_count = download_count # This should be the same as download_count

        message = f"Download process finished.\n"
        message += f"Total potential URLs found: {total_urls}\n"
        message += f"Successfully downloaded: {success_count}\n"
        message += f"Failed downloads: {failed_count}"

        if failed_count > 0:
            message += "\n\nDetails of failures written to console/log."
            # Optionally, show failures in a message box, but might be too long
            # failure_details = "\n".join([f"- {url}: {reason}" for url, reason in failed_downloads.items()])
            # message += f"\n\nFailed:\n{failure_details}"

        QMessageBox.information(self, "Download Complete", message)
            
    def run(self):
        self.show()
        self.setWindowTitle("S.O.X. EXTRAS - Avatar/Icon Downloader")
        self.setWindowIcon(QIcon('SOXico.png'))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    transformer = JSONTransformer()
    transformer.run()
    sys.exit(app.exec_())