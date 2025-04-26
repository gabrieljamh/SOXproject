import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QFileDialog,
                             QVBoxLayout, QMessageBox, QLabel, QSizePolicy, QSpacerItem) # Added QSizePolicy and QSpacerItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon # Imported QIcon
import json
import re
import os

class JSONTransformer(QWidget):
    def __init__(self):
        super().__init__()
        self.inputJson = None # Initialize attribute to store loaded data
        # Keep references to widgets that need state changes
        self.saveButton = None
        self.loadedFileLabel = None
        self.initUI()

    def initUI(self):
        # Create GUI components
        # Removed textSpacer - will use QSpacerItem
        textDesc = QLabel("Welcome to S.O.X. Project! This tool aims to convert XoulAI JSONs into TavernAI usable JSONs.\nThis one is dedicated to extract Xouls from chat backups and into Character Cards")
        textCredits = QLabel("<i>by Junji Dragonfox @ Project BomberCraft</i>")
        loadButton = QPushButton("Import Xoul Chat JSON")

        # --- Store reference to saveButton and disable it initially ---
        self.saveButton = QPushButton("Export Multiple TavernAI JSON")
        self.saveButton.setEnabled(False) # Disable button initially
        # --- End saveButton changes ---

        creditButton = QPushButton("SEE CREDITS")
        textInput = QLabel("VV Station XoulAI VV")
        textOutput = QLabel("<i>-->> Next Station: TavernAI -->></i>")

        # --- Create label to display loaded file ---
        self.loadedFileLabel = QLabel("No file loaded")
        self.loadedFileLabel.setAlignment(Qt.AlignCenter)
        # --- End loaded file label ---

        imageLabel = QLabel()

        # --- Widget Properties ---
        imageLabel.setAlignment(Qt.AlignCenter)
        textDesc.setAlignment(Qt.AlignCenter)
        textCredits.setAlignment(Qt.AlignRight)
        textCredits.setTextFormat(Qt.RichText)
        textCredits.setOpenExternalLinks(True) # QLabel cannot typically open links, consider QTextBrowser if needed
        textInput.setAlignment(Qt.AlignCenter)
        textOutput.setAlignment(Qt.AlignCenter)
        textOutput.setTextFormat(Qt.RichText) # Not strictly needed for this text
        textOutput.setOpenExternalLinks(True) # QLabel cannot typically open links

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
        layout.addWidget(imageLabel, alignment=Qt.AlignCenter) # Added alignment flag directly
        layout.addWidget(textDesc, alignment=Qt.AlignCenter)    # Added alignment flag directly

        # Add flexible space to push main content down
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)) # width, height, hPolicy, vPolicy

        # Middle section: Input/Load
        layout.addWidget(textInput, alignment=Qt.AlignCenter) # Added alignment flag directly
        layout.addWidget(loadButton) # Buttons stretch horizontally in QVBoxLayout by default

        # --- Add the loaded file label to the layout ---
        layout.addWidget(self.loadedFileLabel, alignment=Qt.AlignCenter)
        # --- End add label ---

        # Add a fixed space between Load and Save sections
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Middle section: Output/Save
        layout.addWidget(textOutput, alignment=Qt.AlignCenter) # Added alignment flag directly
        layout.addWidget(self.saveButton) # Use self.saveButton reference

        # Add flexible space to push credits to the bottom
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Bottom section: Credits
        layout.addWidget(textCredits, alignment=Qt.AlignRight) # Added alignment flag directly
        layout.addWidget(creditButton, alignment=Qt.AlignRight) # Align button to the right

        # --- Connections ---
        loadButton.clicked.connect(self.loadInputFile)
        self.saveButton.clicked.connect(self.transformJSONAndSave) # Connect using self.saveButton
        creditButton.clicked.connect(self.creditsWND)

        # --- Window Setup ---
        self.setLayout(layout)
        self.setWindowTitle("S.O.X. EXTRAS - Xoul/Character Extraction Tool")
        # Set Window Icon - Added error handling
        try:
            icon = QIcon('SOXico.png')
            if icon.isNull():
                 print("Warning: Could not load SOXico.png for window icon.")
            else:
                self.setWindowIcon(icon)
        except Exception as e:
             print(f"Error loading icon: {e}")

        # self.show() # Call show in the run method or __main__

    def creditsWND(self):
        info_text = """
R.I.P. XoulAI, we hope you return someday, thanks for the moments.

Thanks Zenna for the advice

Testers:
TBA

V0.0.2
"""
        QMessageBox.information(self, "CREDITS", info_text.strip())

    def loadInputFile(self):
        # Added file filter and default directory
        filename, _ = QFileDialog.getOpenFileName(self, "Load Input JSON", '.', 'JSON files (*.json)')
        if not filename:
            self.inputJson = None # Clear data if load is cancelled
            # --- Reset state on cancel ---
            if self.saveButton: self.saveButton.setEnabled(False)
            if self.loadedFileLabel: self.loadedFileLabel.setText("No file loaded")
            # --- End reset ---
            return

        try:
            # --- Encoding Fix + Better Error Handling ---
            # Specify encoding='utf-8' when opening the file
            with open(filename, 'r', encoding='utf-8') as f:
                self.inputJson = json.load(f)
            # --- End Fix ---

            # Check if the loaded data has the expected structure (at least 'conversation')
            if not isinstance(self.inputJson, dict) or "conversation" not in self.inputJson:
                self.inputJson = None # Data structure is not as expected
                # --- Reset state on failure ---
                if self.saveButton: self.saveButton.setEnabled(False)
                if self.loadedFileLabel: self.loadedFileLabel.setText("No file loaded")
                # --- End reset ---
                QMessageBox.critical(self, "Data Structure Error",
                                     f"The loaded JSON file does not appear to be a valid XoulAI chat backup format.\n"
                                     f"Missing expected 'conversation' key.")
                print(f"Data structure error: 'conversation' key not found in {filename}")
                return # Stop processing here

            # --- Update state on success ---
            if self.saveButton: self.saveButton.setEnabled(True) # Enable button
            if self.loadedFileLabel: self.loadedFileLabel.setText(f"Loaded: {os.path.basename(filename)}") # Display filename
            # --- End update ---

            QMessageBox.information(self, "Success!", "JSON loaded successfully!")

        except FileNotFoundError:
            self.inputJson = None
            # --- Reset state on failure ---
            if self.saveButton: self.saveButton.setEnabled(False)
            if self.loadedFileLabel: self.loadedFileLabel.setText("No file loaded")
            # --- End reset ---
            QMessageBox.critical(self, "Error", f"File not found:\n{filename}")
            print(f"Error: File not found: {filename}")
        except json.JSONDecodeError as e:
            self.inputJson = None
            # --- Reset state on failure ---
            if self.saveButton: self.saveButton.setEnabled(False)
            if self.loadedFileLabel: self.loadedFileLabel.setText("No file loaded")
            # --- End reset ---
            QMessageBox.critical(self, "JSON Error", f"Failed to parse JSON data.\nFile might not be a valid JSON or is corrupted:\n{e}")
            print(f"JSON parsing error details for {filename}: {e}")
        except UnicodeDecodeError as e:
            self.inputJson = None
            # --- Reset state on failure ---
            if self.saveButton: self.saveButton.setEnabled(False)
            if self.loadedFileLabel: self.loadedFileLabel.setText("No file loaded")
            if self.loadedFileLabel: self.loadedFileLabel.setText("No file loaded")
            # --- End reset ---
            QMessageBox.critical(self, "Encoding Error", f"Failed to read the file with UTF-8 encoding.\nFile might be saved in a different encoding or is corrupted:\n{e}\n\nTry opening it in a text editor (like VS Code or Notepad++) and saving it with UTF-8 encoding.")
            print(f"Decoding Error details for {filename}: {e}")
        except Exception as e:
            self.inputJson = None
            # --- Reset state on failure ---
            if self.saveButton: self.saveButton.setEnabled(False)
            if self.loadedFileLabel: self.loadedFileLabel.setText("No file loaded")
            # --- End reset ---
            QMessageBox.critical(self, "General Error", f"An unexpected error occurred while loading the file:\n{e}")
            print(f"General Error loading file {filename}:", str(e))


    def transformJSONAndSave(self):
        """
        Transforms multiple character entries from a specific input JSON
        format and saves each character as a separate JSON file in a
        user-selected directory.
        """
        # Check if inputJson exists and has the basic structure needed
        if not hasattr(self, 'inputJson') or not isinstance(self.inputJson, dict) or "conversation" not in self.inputJson:
             QMessageBox.warning(self, "Warning", "No valid Xoul Chat JSON data loaded.")
             # Optionally disable the button here too, though loadInputFile manages it.
             # if self.saveButton: self.saveButton.setEnabled(False)
             # if self.loadedFileLabel: self.loadedFileLabel.setText("No file loaded")
             return

        # Access the 'conversation' and 'xouls' list using .get()
        conversation_data = self.inputJson.get("conversation", {}) # Default to empty dict if missing
        xouls_list = conversation_data.get("xouls", []) # Default to empty list if missing

        if not xouls_list or not isinstance(xouls_list, list):
            QMessageBox.information(self, "Info", "No 'xouls' characters list found or list is empty in the loaded JSON.")
            return # Stop if no xouls to process

        # Get the overall conversation scenario, if any (using .get() and handling list format)
        overall_scenario_prompt = conversation_data.get("scenario", {}).get("prompt") # Default to empty dict then None
        if isinstance(overall_scenario_prompt, list):
            overall_scenario_prompt = overall_scenario_prompt[0] if overall_scenario_prompt else ""
        else:
            overall_scenario_prompt = overall_scenario_prompt if overall_scenario_prompt is not None else ""


        # Ask the user for a directory to save files
        directory = QFileDialog.getExistingDirectory(self, "Select Directory to Save Character JSONs")

        if not directory:
            return # User cancelled directory selection

        saved_count = 0
        failed_count = 0
        error_messages = []

        # Process each character in the 'xouls' list
        for index, character_data in enumerate(xouls_list):
            # Ensure character_data is a dictionary before processing
            if not isinstance(character_data, dict):
                 failed_count += 1
                 error_messages.append(f"Failed to process item at index {index}: Data is not a dictionary.")
                 print(f"Error processing item at index {index}: Expected dictionary, got {type(character_data)}")
                 continue # Skip this item

            try:
                # Transformation logic based on the input structure, using .get() for safety
                output_json = {
                    "name": character_data.get("name", ""),
                    "description": character_data.get("backstory", ""), # Backstory fits description
                    "personality": "", # No clear equivalent in the character item structure
                    "scenario": "", # Use character-specific scenario if available, otherwise overall? Keeping blank for now per original logic.
                    "first_mes": "",                                     # No clear equivalent
                    "mes_example": character_data.get("samples", ""),   # Use samples from character data
                    "creator_notes": character_data.get("bio", ""),     # Use bio from character data
                    "system_prompt": "",                                 # No equivalent
                    "post_history_instructions": "",                     # No equivalent
                    # Original had empty tags. If social_tags were expected per character item,
                    # it would be: character_data.get("social_tags", [])
                    "tags": [],
                    "creator": character_data.get("slug", ""),
                    "character_version": "imported",
                    "alternate_greetings": [], # No equivalent
                    "extensions": {
                        # Ensure talkativeness is a string as per example output
                        "talkativeness": str(character_data.get("talkativeness", "0.5")),
                        "fav": False, # No equivalent per character item
                        "world": "", # No equivalent per character item
                        "depth_prompt": { # No equivalent per character item
                            "prompt": "",
                            "depth": 4,
                            "role": "system"
                        }
                    },
                    "group_only_greetings": [] # No equivalent
                }

                # Determine filename based on name or slug, fallback to index
                character_name_slug = character_data.get("name") or character_data.get("slug")
                if not character_name_slug:
                     character_name_slug = f"unknown_character_{index}" # Fallback name if name/slug missing

                # Sanitize filename: remove invalid characters and replace spaces
                filename_base = re.sub(r'[^\w\-_\. ]', '', character_name_slug)
                filename_base = filename_base.replace(' ', '_')

                # Ensure filename is not empty after sanitization
                if not filename_base:
                    filename_base = f"character_{index}"

                filename = f"{filename_base}.json"
                full_path = os.path.join(directory, filename)

                # Ensure the target directory exists (moved outside loop for slight efficiency, but harmless here)
                # os.makedirs(directory, exist_ok=True) # Already done before the loop

                # Save the transformed JSON to the file
                # --- Encoding Fix + Indent ---
                with open(full_path, 'w', encoding='utf-8') as f:
                    json.dump(output_json, f, indent=4) # Use indent for readability
                # --- End Fix ---

                saved_count += 1

            except Exception as e: # Catching broad Exception for simplicity here
                failed_count += 1
                # Identify the character that failed for the error message
                char_identifier = character_data.get("slug", character_data.get("name", f"index_{index}"))
                error_messages.append(f"Failed to process '{char_identifier}': {e}")
                # Print error to console for debugging
                print(f"Error processing character {char_identifier}: {e}")


        # Provide feedback to the user based on the results
        if saved_count > 0 and failed_count == 0:
            QMessageBox.information(self, "Success!",
                                   f"Successfully transformed and saved {saved_count} character JSON files to\n{directory}")
        elif saved_count > 0 and failed_count > 0:
            QMessageBox.warning(self, "Partial Success",
                                f"Successfully transformed and saved {saved_count} character files.\n"
                                f"Failed to save {failed_count} files due to errors.")
            # Show detailed errors in a separate dialog or console
            detail_msg = "Details:\n" + "\n".join(error_messages[:10]) # Show up to 10 errors in message box
            if len(error_messages) > 10:
                 detail_msg += "\n..."
            QMessageBox.information(self, "Processing Details", detail_msg)
            print("\n--- Processing Errors ---")
            for msg in error_messages:
                print(msg)
            print("-------------------------")
        elif failed_count > 0:
            QMessageBox.critical(self, "Failure",
                                 f"Failed to save all {failed_count} character files.")
            detail_msg = "Details:\n" + "\n".join(error_messages[:10])
            if len(error_messages) > 10:
                 detail_msg += "\n..."
            QMessageBox.information(self, "Processing Details", detail_msg)
            print("\n--- Processing Errors ---")
            for msg in error_messages:
                print(msg)
            print("-------------------------")
        else:
            # This case happens if xouls_list was empty or load failed early
            QMessageBox.information(self, "Info", "No characters were processed or saved.")

    def run(self):
        self.show()
        # Window title and icon already set in initUI
        # self.setWindowTitle("S.O.X. EXTRAS - Xoul/Character Extraction Tool")
        # self.setWindowIcon(QIcon('SOXico.png'))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    transformer = JSONTransformer()
    transformer.run()
    sys.exit(app.exec_())