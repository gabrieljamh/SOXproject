import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QFileDialog,
                             QVBoxLayout, QMessageBox, QLabel, QSizePolicy, QSpacerItem) # Added QSizePolicy and QSpacerItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon
import json
import os
import re # Import re module for filename sanitization

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
        textDesc = QLabel("Welcome to S.O.X. Project! This tool aims to convert XoulAI JSONs into TavernAI usable JSONs.\nThis one is dedicated to extract Scenario from chat backup into TavernAI World Single Entry.\nShould be attached at the chat")
        textCredits = QLabel("<i>by Junji Dragonfox @ Project BomberCraft</i>")
        loadButton = QPushButton("Import Xoul Chat JSON")

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
        self.setWindowTitle("S.O.X. EXTRAS - Scenario Extraction Tool")
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
        """Checks if the input file is loaded and has the minimum expected structure for scenario extraction."""
        # Check if inputJson is a dict and has the nested structure: conversation -> scenario -> prompt (as a list)
        if isinstance(self.inputJson, dict) and \
           "conversation" in self.inputJson and \
           isinstance(self.inputJson.get("conversation"), dict) and \
           "scenario" in self.inputJson["conversation"] and \
           isinstance(self.inputJson["conversation"].get("scenario"), dict) and \
           "prompt" in self.inputJson["conversation"]["scenario"] and \
           isinstance(self.inputJson["conversation"]["scenario"].get("prompt"), list) and \
           len(self.inputJson["conversation"]["scenario"]["prompt"]) > 0 and \
           isinstance(self.inputJson["conversation"]["scenario"]["prompt"][0], str):

            self.saveButton.setEnabled(True)
            print("Input file loaded and expected chat scenario structure found. Save button enabled.")
        else:
            self.saveButton.setEnabled(False)
            print("Waiting for input file to be loaded or structure invalid for scenario extraction.")


    def loadInputFile(self):
        # Load Xoul Chat JSON file
        # Added file filter and default directory
        filename, _ = QFileDialog.getOpenFileName(self, "Load Xoul Chat JSON", '.', 'JSON files (*.json)')
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

            # Basic data structure check for Xoul Chat Scenario
            # Expecting dict -> conversation -> scenario -> prompt [list of strings]
            if not isinstance(loaded_data, dict) or \
               "conversation" not in loaded_data or \
               not isinstance(loaded_data.get("conversation"), dict) or \
               "scenario" not in loaded_data["conversation"] or \
               not isinstance(loaded_data["conversation"].get("scenario"), dict) or \
               "prompt" not in loaded_data["conversation"]["scenario"] or \
               not isinstance(loaded_data["conversation"]["scenario"].get("prompt"), list) or \
               len(loaded_data["conversation"]["scenario"]["prompt"]) == 0 or \
               not isinstance(loaded_data["conversation"]["scenario"]["prompt"][0], str):

                self.inputJson = None
                self._input_filename = None
                if self.loadedFileLabel: self.loadedFileLabel.setText("Invalid file structure")
                QMessageBox.critical(self, "Data Structure Error",
                                     f"The loaded file does not appear to be a valid Xoul Chat JSON for scenario extraction.\n"
                                     f"Missing expected structure (e.g., 'conversation.scenario.prompt').")
                print(f"Data structure error in {filename}: Missing expected keys or wrong types for scenario extraction.")
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
        # Check if inputJson is loaded and has the expected structure
        # This check mirrors the one in _check_enable_save and loadInputFile
        if not isinstance(self.inputJson, dict) or \
           "conversation" not in self.inputJson or \
           not isinstance(self.inputJson.get("conversation"), dict) or \
           "scenario" not in self.inputJson["conversation"] or \
           not isinstance(self.inputJson["conversation"].get("scenario"), dict) or \
           "prompt" not in self.inputJson["conversation"]["scenario"] or \
           not isinstance(self.inputJson["conversation"]["scenario"].get("prompt"), list) or \
           len(self.inputJson["conversation"]["scenario"]["prompt"]) == 0 or \
           not isinstance(self.inputJson["conversation"]["scenario"]["prompt"][0], str):
            # This warning should ideally not be needed if the button state is managed correctly,
            # but it's a safe fallback.
            QMessageBox.warning(self, "Error", "No valid Chat JSON data loaded or structure is invalid for scenario extraction!")
            # Optionally disable the button here too, though loadInputFile manages it.
            # if self.saveButton: self.saveButton.setEnabled(False)
            # if self.loadedFileLabel: self.loadedFileLabel.setText("No file loaded")
            return

        try:
            # Access nested data safely
            conversation_data = self.inputJson.get("conversation", {})
            scenario_data = conversation_data.get("scenario", {}) # Default to empty dict if scenario is null or missing

            # Get the full prompt text from the first item of the prompt list
            # We already validated that prompt is a non-empty list starting with a string
            full_prompt_text = scenario_data.get("prompt", [""])[0] # Default to [""] if prompt is missing/null

            # --- Determine the name for the comment field ---
            # Get the scenario name (can be None if null in JSON or key is missing)
            scenario_name_potential = scenario_data.get("name")

            # Get the conversation name (provide a default if conversation object or name is missing)
            conversation_name = conversation_data.get("name", "Unnamed Conversation")

            # Use scenario name if it exists and is not None, otherwise use conversation name
            scenario_name_for_comment = scenario_name_potential if scenario_name_potential is not None else conversation_name


            # --- Transformation Logic: Parse prompt string ---

            familiarity = None
            location = None
            core_prompt_lines = [] # To store the main prompt text excluding spec lines

            # Parse the full prompt text line by line to find spec details
            lines = full_prompt_text.splitlines()
            for line in lines:
                stripped_line = line.strip()
                # Use lower() for case-insensitive matching
                if stripped_line.lower().startswith("familiarity:"):
                    # Extract value after "familiarity:"
                    familiarity = stripped_line[len("familiarity:"):].strip()
                elif stripped_line.lower().startswith("location:"):
                     # Extract value after "location:"
                     location = stripped_line[len("location:"):].strip()
                # Add more parsing for other potential spec fields here if needed
                # elif stripped_line.lower().startswith("style:"):
                #      style = stripped_line[len("style:"):].strip()
                #      ...
                else:
                    # This line is part of the core prompt
                    core_prompt_lines.append(line)

            # Join the core prompt lines back together
            scenario_prompt = "\n".join(core_prompt_lines)

            # Construct the 'content' string by combining core prompt and parsed spec details
            content_parts = [scenario_prompt]
            spec_lines = []

            # Add specific prompt_spec fields if they were found during parsing and are non-empty strings
            if isinstance(familiarity, str) and familiarity:
                 spec_lines.append(f"{{{{char}}}} are: {familiarity}")

            if isinstance(location, str) and location:
                 spec_lines.append(f"location: {location}")

            # Add other parsed spec_lines here

            if spec_lines:
                # Add a separator only if there are spec lines AND core prompt is not just whitespace
                if scenario_prompt.strip():
                     content_parts.append("\n\n" + "\n".join(spec_lines))
                else:
                     # If no core prompt, just add the spec lines (with one newline between them)
                     content_parts.append("\n".join(spec_lines))

            # Join all parts to form the final content string
            content = "".join(content_parts).strip() # Use strip() to remove leading/trailing whitespace


            # Create the output dictionary structure
            output_json = {"entries": {}}
            entries_dict = {} # Dictionary to hold the single entry


            # Create the single entry dictionary - using fixed values from TavernAI World entries
            entry = {
                "uid": 0,                      # Fixed value
                "key": [],                     # Fixed value (keywords are derived from scenario name in other tools)
                "keysecondary": [],            # Fixed value
                "comment": scenario_name_for_comment, # Use the determined name
                "content": content,            # Constructed content string
                "constant": True,              # Typical for scenario/world entries
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
                "displayIndex": 0              # Fixed value
            }

            # Add the single entry to the entries dictionary with key "0"
            entries_dict["0"] = entry

            # Assign the populated entries dictionary to the output structure
            output_json["entries"] = entries_dict

            # --- End Transformation Logic ---


            # Convert the output dictionary to JSON and save it
            # Suggest a default filename based on the conversation name or scenario name
            default_filename_base = scenario_name_for_comment or "extracted_scenario"
            # Sanitize filename using the re module
            filename_base = re.sub(r'[^\w\-_\. ]', '', default_filename_base)
            filename_base = filename_base.replace(' ', '_')
            if not filename_base:
                 filename_base = "extracted_scenario" # Ensure not empty

            default_save_name = f"{filename_base}.json"

            # Added file filter and default directory
            filename, _ = QFileDialog.getSaveFileName(self, "Save Output JSON", default_save_name, 'JSON files (*.json)')
            if not filename:
                # User cancelled save. This is not an error.
                return

            # Ensure filename ends with .json if user didn't add it
            if not filename.lower().endswith('.json'):
                filename += '.json'

            # --- Save the transformed JSON to the file ---
            # Use encoding='utf-8' and indent=4 for readability
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_json, f, indent=4) # Use indent=4 for readability
            # --- End Fix ---

            QMessageBox.information(self, "Success!", f"JSON transformed and saved successfully to:\n{filename}")

        # Catch specific errors during transformation/saving
        except TypeError as e: # e.g., trying to use [] on a non-dict/list, or isinstance check failed
             QMessageBox.critical(self, "Transformation Error", f"Error during data processing or validation.\nDetails: {e}")
             print(f"Type Error during transformation: {e}")
        except ValueError as e: # e.g., issues with values/types during processing
             QMessageBox.critical(self, "Transformation Error", f"Value error during data processing.\nDetails: {e}")
             print(f"Value Error during transformation: {e}")
        except IndexError as e: # Catch index error if prompt list was empty somehow despite checks
             QMessageBox.critical(self, "Transformation Error", f"Unexpected empty list encountered during prompt parsing.\nDetails: {e}")
             print(f"Index Error during transformation: {e}")
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