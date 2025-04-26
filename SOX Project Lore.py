import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QFileDialog,
                             QVBoxLayout, QMessageBox, QLabel, QSizePolicy, QSpacerItem) # Added QSizePolicy and QSpacerItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon
import json
import os
import re # Need re for filename sanitization

class JSONTransformer(QWidget):
    def __init__(self):
        super().__init__()
        # Initialize attribute to store loaded data and filename
        self.inputJson = None
        self._input_filename = None # Store filename

        # Keep references to widgets that need state changes
        self.saveButton = None
        self.loadedFileLabel = None

        self.initUI()

    def initUI(self):
        # Create GUI components
        # Removed textSpacer - will use QSpacerItem
        textDesc = QLabel("Welcome to S.O.X. Project! This tool aims to convert XoulAI JSONs into TavernAI usable JSONs.\nThis one is dedicated to convert Lorebooks into TavernAI World Entries")
        textCredits = QLabel("<i>by Junji Dragonfox @ Project BomberCraft</i>")
        loadButton = QPushButton("Import Xoul Lorebook JSON")

        # --- Store reference to saveButton and disable it initially ---
        self.saveButton = QPushButton("Export TavernAI World JSON")
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
        textCredits.setOpenExternalLinks(True) # QLabel typically cannot open links
        textInput.setAlignment(Qt.AlignCenter)
        textOutput.setAlignment(Qt.AlignCenter)
        textOutput.setTextFormat(Qt.RichText) # Not strictly needed
        textOutput.setOpenExternalLinks(True) # QLabel typically cannot open links

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
        self.setWindowTitle("S.O.X. - Lorebook Conversion Tool")
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
        # Use triple quotes for multi-line string
        info_text = """
R.I.P. XoulAI, we hope you return someday, thanks for the moments.

Testers:
TBA

V0.0.1
"""
        QMessageBox.information(self, "CREDITS", info_text.strip()) # Use strip() for cleaner message

    def _check_enable_save(self):
        """Checks if the input file is loaded and enables/disables save button."""
        if self.inputJson is not None:
            self.saveButton.setEnabled(True)
            print("Input file loaded. Save button enabled.")
        else:
            self.saveButton.setEnabled(False)
            print("Waiting for input file to be loaded.")


    def loadInputFile(self):
        # Load Xoul Lorebook JSON file
        # Added file filter and default directory
        filename, _ = QFileDialog.getOpenFileName(self, "Load Xoul Lorebook JSON", '.', 'JSON files (*.json)')
        if not filename:
            self.inputJson = None
            self._input_filename = None
            if self.loadedFileLabel: self.loadedFileLabel.setText("No file loaded")
            self._check_enable_save() # Re-check save button state
            return

        try:
            # --- Encoding Fix + Better Error Handling ---
            # Specify encoding='utf-8' when opening the file
            with open(filename, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            # --- End Fix ---

            # Basic data structure check for Xoul Lorebook
            # Expecting a dictionary with an "embedded" key containing a "sections" list
            if not isinstance(loaded_data, dict) or \
               "embedded" not in loaded_data or \
               not isinstance(loaded_data["embedded"], dict) or \
               "sections" not in loaded_data["embedded"] or \
               not isinstance(loaded_data["embedded"]["sections"], list):

                self.inputJson = None
                self._input_filename = None
                if self.loadedFileLabel: self.loadedFileLabel.setText("Invalid file structure")
                QMessageBox.critical(self, "Data Structure Error",
                                     f"The loaded file does not appear to be a valid Xoul Lorebook JSON.\n"
                                     f"Missing expected structure (e.g., 'embedded.sections').")
                print(f"Data structure error in {filename}: Missing expected keys or wrong types.")
            else:
                self.inputJson = loaded_data
                self._input_filename = filename # Store filename on success
                if self.loadedFileLabel: self.loadedFileLabel.setText(f"Loaded: {os.path.basename(filename)}") # Display filename
                QMessageBox.information(self, "Success!", "JSON loaded successfully!")

        except FileNotFoundError:
            self.inputJson = None
            self._input_filename = None
            if self.loadedFileLabel: self.loadedFileLabel.setText("File not found")
            QMessageBox.critical(self, "Error", f"File not found:\n{filename}")
            print(f"Error: File not found: {filename}")
        except json.JSONDecodeError as e:
            self.inputJson = None
            self._input_filename = None
            if self.loadedFileLabel: self.loadedFileLabel.setText("JSON Error")
            QMessageBox.critical(self, "JSON Error", f"Failed to parse JSON data.\nFile might not be a valid JSON or is corrupted:\n{e}")
            print(f"JSON parsing error details for {filename}: {e}")
        except UnicodeDecodeError as e:
            self.inputJson = None
            self._input_filename = None
            if self.loadedFileLabel: self.loadedFileLabel.setText("Encoding Error")
            QMessageBox.critical(self, "Encoding Error", f"Failed to read the file with UTF-8 encoding.\nFile might be saved in a different encoding or is corrupted:\n{e}\n\nTry opening it in a text editor and saving it with UTF-8.")
            print(f"Decoding Error details for {filename}: {e}")
        except Exception as e:
            self.inputJson = None
            self._input_filename = None
            if self.loadedFileLabel: self.loadedFileLabel.setText("Load failed")
            QMessageBox.critical(self, "General Error", f"An unexpected error occurred while loading the file:\n{e}")
            print(f"General Error loading file {filename}:", str(e))

        self._check_enable_save() # Always check state after attempting load


    def transformJSONAndSave(self):
        # Check if inputJson is loaded and is a dictionary (expected format)
        if not isinstance(self.inputJson, dict) or \
           "embedded" not in self.inputJson or \
           not isinstance(self.inputJson["embedded"], dict) or \
           "sections" not in self.inputJson["embedded"] or \
           not isinstance(self.inputJson["embedded"]["sections"], list):
            # This warning should ideally not be needed if the button state is managed correctly,
            # but it's a safe fallback. Also catches if load was successful but structure check failed.
            QMessageBox.warning(self, "Error", "No valid Lorebook JSON data loaded! Please load a lorebook JSON first.")
            # Optionally disable the button here too, though loadInputFile manages it.
            # if self.saveButton: self.saveButton.setEnabled(False)
            # if self.loadedFileLabel: self.loadedFileLabel.setText("No file loaded")
            return

        try:
            # Use the loaded input dictionary directly
            input_data = self.inputJson

            # Create a new dictionary to hold the output structure
            output_json = {"entries": {}}
            entries_dict = {} # Dictionary to hold the transformed entries

            # --- Transformation Logic ---

            # Access the 'sections' list safely
            sections_list = input_data.get("embedded", {}).get("sections", []) # Default to empty list

            if not sections_list:
                 QMessageBox.information(self, "Info", "No 'sections' found in the loaded Lorebook JSON to convert.")
                 return # Exit if no sections to process

            # Iterate over the 'sections' array and create a new entry for each item
            failed_count = 0
            error_messages = []
            for i, section in enumerate(sections_list):
                if not isinstance(section, dict):
                    failed_count += 1
                    error_messages.append(f"Skipping item at index {i}: Data is not a dictionary.")
                    print(f"Error processing item at index {i}: Expected dictionary, got {type(section)}")
                    continue # Skip this item

                try:
                    # Use .get() for safe access to section properties
                    entry = {
                        "uid": i,
                        "key": section.get("keywords", []), # Default to empty list
                        "keysecondary": [], # Fixed value
                        "comment": section.get("name", ""), # Default to empty string
                        "content": section.get("text", ""), # Default to empty string
                        "constant": False, # Fixed value as per TavernAI Lorebooks
                        "vectorized": False, # Fixed value
                        "selective": True, # Fixed value
                        "selectiveLogic": 0, # Fixed value
                        "addMemo": True, # Fixed value
                        "order": 100, # Fixed value
                        "position": 0, # Fixed value (could potentially use i?)
                        "disable": False, # Fixed value
                        "excludeRecursion": False, # Fixed value
                        "preventRecursion": False, # Fixed value
                        "delayUntilRecursion": False, # Fixed value
                        "probability": 100, # Fixed value
                        "useProbability": True, # Fixed value
                        "depth": 4, # Fixed value
                        "group": "", # Fixed value
                        "groupOverride": False, # Fixed value
                        "groupWeight": 100, # Fixed value
                        "scanDepth": None, # Fixed value
                        "caseSensitive": None, # Fixed value
                        "matchWholeWords": None, # Fixed value
                        "useGroupScoring": None, # Fixed value
                        "automationId": "", # Fixed value
                        "role": None, # Fixed value
                        "sticky": 0, # Fixed value
                        "cooldown": 0, # Fixed value
                        "delay": 0, # Fixed value
                        "displayIndex": i # Use index for display order
                    }
                    # Add the entry to the entries dictionary using string index as key
                    entries_dict[str(i)] = entry

                except Exception as e:
                     failed_count += 1
                     # Identify the section by name or index
                     section_identifier = section.get("name", f"index_{i}")
                     error_messages.append(f"Failed to process section '{section_identifier}': {e}")
                     print(f"Error processing section {section_identifier}: {e}")
                     continue # Continue processing other sections

            # Assign the populated entries dictionary to the output structure
            output_json["entries"] = entries_dict

            # --- End Transformation Logic ---

            # Check if any entries were successfully processed
            saved_count = len(entries_dict)
            if saved_count == 0:
                 QMessageBox.information(self, "Info", f"No valid sections were found or processed from the Lorebook JSON.")
                 # Optionally disable the button again if no entries were produced
                 # if self.saveButton: self.saveButton.setEnabled(False)
                 # if self.loadedFileLabel: self.loadedFileLabel.setText("No file loaded") # Or keep loaded file info? Keep file info.
                 return # Exit if nothing to save

            # Convert the output dictionary to JSON and save it
            # Suggest a default filename based on the original input filename or a generic name
            default_save_name = "converted_lorebook.json"
            if self._input_filename:
                 base, ext = os.path.splitext(os.path.basename(self._input_filename))
                 default_save_name = f"{base}_world.json"

            filename, _ = QFileDialog.getSaveFileName(self, "Save Output JSON", default_save_name, 'JSON files (*.json)')
            if not filename:
                # User cancelled save. This is not an error.
                return

            # Ensure filename ends with .json
            if not filename.lower().endswith('.json'):
                filename += '.json'

            # --- Save the transformed JSON to the file ---
            # Use encoding='utf-8' and indent=4
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_json, f, indent=4) # Use indent=4 for readability
            # --- End Fix ---

            # Provide feedback to the user based on the results
            if failed_count == 0:
                 QMessageBox.information(self, "Success!",
                                        f"Successfully transformed and saved {saved_count} lorebook entries to\n{filename}")
            else:
                 QMessageBox.warning(self, "Partial Success",
                                     f"Successfully transformed and saved {saved_count} lorebook entries.\n"
                                     f"Failed to process {failed_count} entries due to errors.")
                 # Optionally show detailed errors
                 detail_msg = "Details:\n" + "\n".join(error_messages[:10]) # Show up to 10 errors
                 if len(error_messages) > 10:
                      detail_msg += "\n..."
                 QMessageBox.information(self, "Processing Details", detail_msg)
                 print("\n--- Processing Errors ---")
                 for msg in error_messages:
                      print(msg)
                 print("-------------------------")


        # Catch specific errors during transformation/saving
        except TypeError as e: # e.g., trying to use [] on a non-dict/list
             QMessageBox.critical(self, "Transformation Error", f"Error during data processing.\nDetails: {e}")
             print(f"Type Error during transformation: {e}")
        except ValueError as e: # e.g., issues with values/types during processing
             QMessageBox.critical(self, "Transformation Error", f"Value error during data processing.\nDetails: {e}")
             print(f"Value Error during transformation: {e}")
        except IOError as e:
             QMessageBox.critical(self, "File Writing Error", f"Failed to write the output file:\n{e}")
             print(f"IO Error saving file {filename}: {e}")
        except Exception as e:
             QMessageBox.critical(self, "General Error", f"An unexpected error occurred during transformation or saving:\n{e}")
             print("General Error transforming/saving:", str(e))


    def run(self):
        self.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    transformer = JSONTransformer()
    transformer.run()
    sys.exit(app.exec_())