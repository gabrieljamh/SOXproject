import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QFileDialog,
                             QVBoxLayout, QMessageBox, QLabel, QSizePolicy, QSpacerItem) # Added QSizePolicy and QSpacerItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon # Imported QIcon
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
        textDesc = QLabel("Welcome to S.O.X. Project! This tool aims to convert XoulAI JSONs into TavernAI usable JSONs.\nThis one is dedicated to convert Scenario into TavernAI World Single Entry.\nShould be attached at the chat")
        textCredits = QLabel("<i>by Junji Dragonfox @ Project BomberCraft</i>")
        loadButton = QPushButton("Import Xoul Scenario JSON")

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
        self.setWindowTitle("S.O.X. - Scenario Conversion Tool")
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
        # Load Xoul Scenario JSON file
        # Added file filter and default directory
        filename, _ = QFileDialog.getOpenFileName(self, "Load Xoul Scenario JSON", '.', 'JSON files (*.json)')
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

            # Basic data structure check for Xoul Scenario
            # Expecting a dictionary with at least 'name' or 'prompt'
            if not isinstance(loaded_data, dict) or ('name' not in loaded_data and 'prompt' not in loaded_data):
                self.inputJson = None
                self._input_filename = None
                if self.loadedFileLabel: self.loadedFileLabel.setText("Invalid file structure")
                QMessageBox.critical(self, "Data Structure Error",
                                     f"The loaded file does not appear to be a valid Xoul Scenario JSON.\n"
                                     f"Missing expected 'name' or 'prompt' keys.")
                print(f"Data structure error in {filename}: Missing expected keys")
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
        if not isinstance(self.inputJson, dict):
            # This warning should ideally not be needed if the button state is managed correctly,
            # but it's a safe fallback.
            QMessageBox.warning(self, "Error", "No valid JSON data loaded! Please load a scenario JSON first.")
            # Optionally disable the button here too, though loadInputFile manages it.
            # if self.saveButton: self.saveButton.setEnabled(False)
            # if self.loadedFileLabel: self.loadedFileLabel.setText("No file loaded")
            return

        try:
            # Use the loaded input dictionary directly
            input_data = self.inputJson

            # Create the output dictionary structure
            output_json = {"entries": {}}
            entries_dict = {} # Dictionary to hold the single entry

            # --- Transformation Logic based on the input/output examples ---

            # Extract necessary data from the single input object using .get() for safety
            scenario_name = input_data.get("name", "")
            scenario_prompt = input_data.get("prompt", "")
            prompt_spec = input_data.get("prompt_spec", {}) # Get the prompt_spec dictionary, default to empty dict

            # Construct the 'content' string by combining prompt and prompt_spec details
            content_parts = [scenario_prompt]
            if isinstance(prompt_spec, dict) and prompt_spec: # Check if prompt_spec is a non-empty dictionary
                spec_lines = []
                # Add specific prompt_spec fields if they exist and are not None strings
                familiarity = prompt_spec.get("familiarity")
                if isinstance(familiarity, str) and familiarity:
                     spec_lines.append(f"{{{{char}}}} are: {familiarity}")

                location = prompt_spec.get("location")
                if isinstance(location, str) and location:
                     spec_lines.append(f"location: {location}")

                # Add other prompt_spec fields here if needed in the future, e.g.:
                # style = prompt_spec.get("style")
                # if isinstance(style, str) and style:
                #      spec_lines.append(f"style: {style}")

                if spec_lines:
                    # Add a separator only if there are spec lines
                    content_parts.append("\n\n" + "\n".join(spec_lines))

            # Join all parts to form the final content string
            content = "".join(content_parts)

            # Create the single entry dictionary
            entry = {
                "uid": 0,                      # Fixed as per output example
                "key": [],                     # Fixed as per output example
                "keysecondary": [],            # Fixed as per output example
                "comment": scenario_name,      # Taken from input "name"
                "content": content,            # Constructed content string
                "constant": True,              # *** Changed from False to True as per output example ***
                "vectorized": False,           # Fixed value
                "selective": True,             # Fixed value
                "selectiveLogic": 0,           # Fixed value
                "addMemo": True,               # Fixed value
                "order": 100,                  # Fixed value
                "position": 0,                 # Fixed value
                "disable": False,              # Fixed value
                "excludeRecursion": False,     # Fixed value
                "preventRecursion": False,     # Fixed value
                "delayUntilRecursion": False,  # Fixed value
                "probability": 100,            # Fixed value
                "useProbability": True,        # Fixed value
                "depth": 4,                    # Fixed value
                "group": "",                   # Fixed value
                "groupOverride": False,        # Fixed value
                "groupWeight": 100,            # Fixed value
                "scanDepth": None,             # Fixed value
                "caseSensitive": None,         # Fixed value
                "matchWholeWords": None,       # Fixed value
                "useGroupScoring": None,       # Fixed value
                "automationId": "",            # Fixed value
                "role": None,                  # Fixed value
                "sticky": 0,                   # Fixed value
                "cooldown": 0,                 # Fixed value
                "delay": 0,                    # Fixed value
                "displayIndex": 0              # Fixed as per output example
            }

            # Add the single entry to the entries dictionary with key "0"
            entries_dict["0"] = entry

            # Assign the populated entries dictionary to the output structure
            output_json["entries"] = entries_dict

            # --- End Transformation Logic ---

            # Convert the output dictionary to JSON and save it
            # Suggest a default filename based on the scenario name
            default_filename_base = scenario_name or "converted_scenario" # Fallback name
            # Sanitize filename using the re module
            filename_base = re.sub(r'[^\w\-_\. ]', '', default_filename_base)
            filename_base = filename_base.replace(' ', '_')
            if not filename_base:
                 filename_base = "converted_scenario" # Ensure not empty

            default_save_name = f"{filename_base}.json"

            # Added file filter and default directory
            filename, _ = QFileDialog.getSaveFileName(self, "Save Output JSON", default_save_name, 'JSON files (*.json)')
            if not filename:
                # User cancelled save. This is not an error.
                return

            # Ensure filename ends with .json if user didn't add it
            if not filename.lower().endswith('.json'):
                filename += '.json'

            # --- Encoding Fix + Indent ---
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_json, f, indent=4) # Use indent=4 for readability
            # --- End Fix ---

            QMessageBox.information(self, "Success!", f"JSON transformed and saved successfully to:\n{filename}")

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