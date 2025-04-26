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
        # Initialize attributes to store loaded data and filenames
        self.input_data = None      # TavernAI backup data
        self._input_filename = None # Store filename for the TavernAI backup

        self.config_data = None     # Xoul Persona data
        self._config_filename = None # Store filename for the Xoul Persona JSON

        # Keep references to widgets that need state changes
        self.saveButton = None
        self.loadedFileLabelA = None
        self.loadedFileLabelB = None

        self.initUI()

    def initUI(self):
        # Create GUI components
        # Removed textSpacer - will use QSpacerItem
        textDesc = QLabel("Welcome to S.O.X. Project! This tool aims to convert XoulAI JSONs into TavernAI usable JSONs.\nThis one is dedicated to add Xoul Personas into TavernAI's Persona backup file to be reimported.\nCreate a Backup in SillyTavern to use this tool.")
        textCredits = QLabel("<i>by Junji Dragonfox @ Project BomberCraft</i>")
        loadButtonA = QPushButton("Import TavernAI Persona's Backup JSON")
        loadButtonB = QPushButton("Add Xoul Persona from JSON")

        # --- Store reference to saveButton and disable it initially ---
        self.saveButton = QPushButton("Export Modified Backup JSON")
        self.saveButton.setEnabled(False) # Disable button initially
        # --- End saveButton changes ---

        creditButton = QPushButton("SEE CREDITS")
        textInput = QLabel("VV Station XoulAI VV")
        textOutput = QLabel("<i>-->> Next Station: TavernAI -->></i>")

        # --- Create labels to display loaded files ---
        self.loadedFileLabelA = QLabel("TavernAI Backup: No file loaded")
        self.loadedFileLabelA.setAlignment(Qt.AlignCenter)
        self.loadedFileLabelB = QLabel("Xoul Persona: No file loaded")
        self.loadedFileLabelB.setAlignment(Qt.AlignCenter)
        # --- End loaded file labels ---

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
        layout.addWidget(imageLabel, alignment=Qt.AlignCenter)
        layout.addWidget(textDesc, alignment=Qt.AlignCenter)

        # Add flexible space
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Middle section: Input/Load A (TavernAI Backup)
        layout.addWidget(textInput, alignment=Qt.AlignCenter)
        layout.addWidget(loadButtonA)
        layout.addWidget(self.loadedFileLabelA, alignment=Qt.AlignCenter) # Add label for file A

        # Add fixed space between Load A and Load B
        layout.addItem(QSpacerItem(20, 15, QSizePolicy.Minimum, QSizePolicy.Fixed))


        # Middle section: Input/Load B (Xoul Persona)
        layout.addWidget(loadButtonB)
        layout.addWidget(self.loadedFileLabelB, alignment=Qt.AlignCenter) # Add label for file B

        # Add a fixed space between Load B and Save
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Middle section: Output/Save
        layout.addWidget(textOutput, alignment=Qt.AlignCenter)
        layout.addWidget(self.saveButton) # Use self.saveButton reference

        # Add flexible space
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Bottom section: Credits
        layout.addWidget(textCredits, alignment=Qt.AlignRight)
        layout.addWidget(creditButton, alignment=Qt.AlignRight)

        # --- Connections ---
        loadButtonA.clicked.connect(self.loadInputFile)
        loadButtonB.clicked.connect(self.loadDataFile)
        self.saveButton.clicked.connect(self.transformJSONAndSave) # Connect using self.saveButton
        creditButton.clicked.connect(self.creditsWND)

        # --- Window Setup ---
        self.setLayout(layout)
        self.setWindowTitle("S.O.X. - Persona Adding Tool")
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
        QMessageBox.information(self, "CREDITS", info_text.strip()) # Use strip() for cleaner message

    def _check_enable_save(self):
        """Checks if both necessary files are loaded and enables/disables save button."""
        if self.input_data is not None and self.config_data is not None:
            self.saveButton.setEnabled(True)
            print("Both files loaded. Save button enabled.")
        else:
            self.saveButton.setEnabled(False)
            print("Waiting for both files to be loaded.")


    def loadInputFile(self):
        # Load TavernAI persona backup JSON file
        filename, _ = QFileDialog.getOpenFileName(self, "Load TavernAI Persona's Backup JSON", '.', 'JSON files (*.json)') # Added filter
        if not filename:
            self.input_data = None
            self._input_filename = None
            if self.loadedFileLabelA: self.loadedFileLabelA.setText("TavernAI Backup: No file loaded")
            self._check_enable_save() # Re-check save button state
            return

        try:
            # --- Encoding Fix + Better Error Handling ---
            with open(filename, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            # --- End Fix ---

            # Basic data structure check for TavernAI backup
            if not isinstance(loaded_data, dict) or 'personas' not in loaded_data or 'persona_descriptions' not in loaded_data:
                 self.input_data = None
                 self._input_filename = None
                 if self.loadedFileLabelA: self.loadedFileLabelA.setText("TavernAI Backup: Invalid structure")
                 QMessageBox.critical(self, "Data Structure Error",
                                      f"The loaded file does not appear to be a valid TavernAI Persona backup.\n"
                                      f"Missing 'personas' or 'persona_descriptions' keys.")
                 print(f"Data structure error in {filename}: Missing expected keys")
            else:
                self.input_data = loaded_data
                self._input_filename = filename # Store filename on success
                if self.loadedFileLabelA: self.loadedFileLabelA.setText(f"TavernAI Backup: {os.path.basename(filename)}")
                QMessageBox.information(self, "Success!", "TavernAI Backup loaded successfully!")

        except FileNotFoundError:
            self.input_data = None
            self._input_filename = None
            if self.loadedFileLabelA: self.loadedFileLabelA.setText("TavernAI Backup: File not found")
            QMessageBox.critical(self, "Error", f"File not found:\n{filename}")
            print(f"Error: File not found: {filename}")
        except json.JSONDecodeError as e:
            self.input_data = None
            self._input_filename = None
            if self.loadedFileLabelA: self.loadedFileLabelA.setText("TavernAI Backup: JSON Error")
            QMessageBox.critical(self, "JSON Error", f"Failed to parse JSON data.\nFile might not be valid JSON or is corrupted:\n{e}")
            print(f"JSON parsing error details for {filename}: {e}")
        except UnicodeDecodeError as e:
            self.input_data = None
            self._input_filename = None
            if self.loadedFileLabelA: self.loadedFileLabelA.setText("TavernAI Backup: Encoding Error")
            QMessageBox.critical(self, "Encoding Error", f"Failed to read the file with UTF-8 encoding.\nFile might be saved in a different encoding or is corrupted:\n{e}\n\nTry opening it in a text editor and saving it with UTF-8.")
            print(f"Decoding Error details for {filename}: {e}")
        except Exception as e:
            self.input_data = None
            self._input_filename = None
            if self.loadedFileLabelA: self.loadedFileLabelA.setText("TavernAI Backup: Load failed")
            QMessageBox.critical(self, "General Error", f"An unexpected error occurred while loading TavernAI Backup:\n{e}")
            print(f"General Error loading file {filename}:", str(e))

        self._check_enable_save() # Always check state after attempting load

    def loadDataFile(self):
        # Load Xoul Persona JSON file
        filename, _ = QFileDialog.getOpenFileName(self, "Add Xoul Persona from JSON", '.', 'JSON files (*.json)') # Added filter
        if not filename:
            self.config_data = None
            self._config_filename = None
            if self.loadedFileLabelB: self.loadedFileLabelB.setText("Xoul Persona: No file loaded")
            self._check_enable_save() # Re-check save button state
            return

        try:
            # --- Encoding Fix + Better Error Handling ---
            with open(filename, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            # --- End Fix ---

            # Basic data structure check for Xoul Persona
            if not isinstance(loaded_data, dict) or 'name' not in loaded_data or 'prompt' not in loaded_data:
                self.config_data = None
                self._config_filename = None
                if self.loadedFileLabelB: self.loadedFileLabelB.setText("Xoul Persona: Invalid structure")
                QMessageBox.critical(self, "Data Structure Error",
                                     f"The loaded file does not appear to be a valid Xoul Persona JSON.\n"
                                     f"Missing 'name' or 'prompt' keys.")
                print(f"Data structure error in {filename}: Missing expected keys")
            else:
                self.config_data = loaded_data
                self._config_filename = filename # Store filename on success
                if self.loadedFileLabelB: self.loadedFileLabelB.setText(f"Xoul Persona: {os.path.basename(filename)}")
                QMessageBox.information(self, "Success!", "Xoul Persona loaded successfully!")

        except FileNotFoundError:
            self.config_data = None
            self._config_filename = None
            if self.loadedFileLabelB: self.loadedFileLabelB.setText("Xoul Persona: File not found")
            QMessageBox.critical(self, "Error", f"File not found:\n{filename}")
            print(f"Error: File not found: {filename}")
        except json.JSONDecodeError as e:
            self.config_data = None
            self._config_filename = None
            if self.loadedFileLabelB: self.loadedFileLabelB.setText("Xoul Persona: JSON Error")
            QMessageBox.critical(self, "JSON Error", f"Failed to parse JSON data.\nFile might not be valid JSON or is corrupted:\n{e}")
            print(f"JSON parsing error details for {filename}: {e}")
        except UnicodeDecodeError as e:
            self.config_data = None
            self._config_filename = None
            if self.loadedFileLabelB: self.loadedFileLabelB.setText("Xoul Persona: Encoding Error")
            QMessageBox.critical(self, "Encoding Error", f"Failed to read the file with UTF-8 encoding.\nFile might be saved in a different encoding or is corrupted:\n{e}\n\nTry opening it in a text editor and saving it with UTF-8.")
            print(f"Decoding Error details for {filename}: {e}")
        except Exception as e:
            self.config_data = None
            self._config_filename = None
            if self.loadedFileLabelB: self.loadedFileLabelB.setText("Xoul Persona: Load failed")
            QMessageBox.critical(self, "General Error", f"An unexpected error occurred while loading Xoul Persona:\n{e}")
            print(f"General Error loading file {filename}:", str(e))

        self._check_enable_save() # Always check state after attempting load


    def transformJSONAndSave(self):
        # Check if both files are loaded and are valid dictionaries
        if not isinstance(self.input_data, dict) or not isinstance(self.config_data, dict):
            # This check is partly handled by _check_enable_save disabling the button,
            # but kept for safety.
            QMessageBox.warning(self, "Warning", "Please load both valid JSON files first.")
            return

        try:
            # Safely get data from config_data (the Xoul Persona JSON)
            new_persona_name = self.config_data.get('name')
            new_description = self.config_data.get('prompt')

            # Additional check for the required fields
            if not isinstance(new_persona_name, str) or not new_persona_name or not isinstance(new_description, str):
                 QMessageBox.warning(self, "Warning", "Xoul Persona JSON must contain 'name' and 'prompt' string keys.")
                 print("Xoul Persona JSON missing 'name' or 'prompt' or they are not strings.")
                 return

            # Make a copy of the input data (TavernAI backup) to modify
            # Deep copy might be safer depending on nested structures, but shallow copy is likely fine here.
            output_data = self.input_data.copy()

            # --- Safely add/update the persona entry ---
            # Ensure 'personas' key exists and is a dictionary
            if 'personas' not in output_data or not isinstance(output_data['personas'], dict):
                 print("Warning: 'personas' key not found or not a dictionary in backup. Creating/replacing.")
                 output_data['personas'] = {} # Create or replace if it's not a dict

            # Sanitize the persona name for use as a dictionary key/filename base
            filename_base = re.sub(r'[^\w\-_\. ]', '', new_persona_name)
            filename_base = filename_base.replace(' ', '_')
            if not filename_base:
                 filename_base = "new_persona" # Fallback if name sanitizes to empty

            persona_dict_key = f"{filename_base}.png" # Use the sanitized name + .png as the key convention

            output_data['personas'][persona_dict_key] = new_persona_name # Add/update the name mapping

            # --- Safely add/update the persona description entry ---
            # Ensure 'persona_descriptions' key exists and is a dictionary
            if 'persona_descriptions' not in output_data or not isinstance(output_data['persona_descriptions'], dict):
                 print("Warning: 'persona_descriptions' key not found or not a dictionary in backup. Creating/replacing.")
                 output_data['persona_descriptions'] = {} # Create or replace if it's not a dict

            # Add or update the description entry
            new_description_entry = {
                "description": new_description,
                # Position logic: Could increment from max existing position + 1,
                # but original code used 0, so sticking to that for consistency.
                "position": 0
            }
            output_data['persona_descriptions'][persona_dict_key] = new_description_entry # Add/update the description details

            # --- Save the transformed JSON to a file ---
            # Suggest a default filename based on the original backup name if possible
            default_save_name = "modified_persona_backup.json"
            if self._input_filename:
                 base, ext = os.path.splitext(os.path.basename(self._input_filename))
                 default_save_name = f"{base}_modified.json"

            filename, _ = QFileDialog.getSaveFileName(self, "Save Modified Backup JSON", default_save_name, "JSON files (*.json)")
            if not filename:
                # User cancelled save. This is not an error.
                return

            # Ensure filename ends with .json
            if not filename.lower().endswith('.json'):
                filename += '.json'

            # --- Save the transformed JSON to the file ---
            # Use encoding='utf-8' and indent=4
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=4)

            QMessageBox.information(self, "Success!", f"Persona added and modified backup saved successfully to:\n{filename}")

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