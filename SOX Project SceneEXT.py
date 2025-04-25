import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QFileDialog, QVBoxLayout, QMessageBox, QLabel
from PyQt5.QtCore import Qt  # Add this line at the top of your code.
from PyQt5.QtGui import QPixmap  # Add this line
from PyQt5.QtGui import QIcon
import json

class JSONTransformer(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        
        # Create GUI components
        textSpacer = QLabel()
        textDesc = QLabel("Welcome to S.O.X. Project! This tool aims to convert XoulAI JSONs into TavernAI usable JSONs.\nThis one is dedicated to extract Scenario from chat backup into TavernAI World Single Entry.\nShould be attached at the chat") 
        textCredits = QLabel("<i>by Junji Dragonfox @ Project BomberCraft</i>")
        loadButton = QPushButton("Import Xoul Chat JSON")
        saveButton = QPushButton("Export TavernAI World JSON")
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
        layout.addWidget(saveButton)
        layout.addWidget(textSpacer)
        layout.addWidget(textCredits)
        layout.addWidget(creditButton)

        loadButton.clicked.connect(self.loadInputFile)
        saveButton.clicked.connect(self.transformJSONAndSave)
        creditButton.clicked.connect(self.creditsWND)

        self.setLayout(layout)
        
    def creditsWND(self):
        QMessageBox.information(self, "CREDITS", "R.I.P. XoulAI, we hope you return someday, thanks for the moments.\n\nTesters:\n\nTBA\n\nV0.0.1")

    def loadInputFile(self):
        # Add filter for JSON files and a default directory/caption
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load Input JSON File", '.', 'JSON files (*.json)'
        )
        if not filename:
            # User cancelled the dialog
            self.inputJson = None # Ensure inputJson is reset if loading is cancelled
            return

        try:
            # Explicitly specify encoding='utf-8' for JSON files
            with open(filename, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)

            # Check if the loaded data is the expected top-level dictionary
            if not isinstance(loaded_data, dict):
                self.inputJson = None # Reset to None if it's not the expected type
                QMessageBox.critical(
                    self, "Loading Error",
                    f"The loaded file does not contain a valid JSON dictionary as the top level element. Found {type(loaded_data).__name__}."
                )
                return # Stop processing

            # If validation passes, assign the loaded data
            self.inputJson = loaded_data
            QMessageBox.information(self, "Success!", "JSON loaded successfully!")

        except json.JSONDecodeError as e:
            # Catch specific JSON parsing errors
            self.inputJson = None # Ensure inputJson is None on failure
            QMessageBox.critical(
                self, "JSON Parsing Error",
                f"Failed to parse JSON file:\n{e}"
            )
        except Exception as e:
            # Catch any other potential file reading errors
            self.inputJson = None # Ensure inputJson is None on failure
            QMessageBox.critical(
                self, "File Reading Error",
                f"An unexpected error occurred while reading the file:\n{e}"
            )

    def transformJSONAndSave(self):
        # Check if inputJson is loaded and is a dictionary (expected format)
        if not hasattr(self, 'inputJson') or not isinstance(self.inputJson, dict):
            QMessageBox.warning(self, "Error", "No valid JSON data loaded! Please load a scenario JSON first.")
            return

        # Use the loaded input dictionary directly
        input_data = self.inputJson

        # --- Data Extraction and Validation ---

        # Access the nested 'conversation' dictionary first
        # Provide empty dict default if 'conversation' key is missing or null
        conversation_data = input_data.get("conversation", {})

        # Now, access the 'scenario' dictionary *from* the conversation data
        scenario_data = conversation_data.get("scenario")


        # Validate the 'scenario' object (This check applies to the value obtained via conversation_data.get("scenario"))
        if not isinstance(scenario_data, dict):
             if scenario_data is None:
                 QMessageBox.warning(self, "Error", "Invalid JSON structure! 'scenario' object is missing or null within 'conversation'.")
             else:
                 QMessageBox.warning(self, "Error", f"Invalid JSON structure! 'scenario' object within 'conversation' should be a dictionary, but found {type(scenario_data).__name__}.")
             return

        # Get the raw value for 'prompt' from the scenario data
        raw_prompt_value = scenario_data.get("prompt")

        # Validate the 'prompt' field within the scenario object
        if raw_prompt_value is None:
             QMessageBox.warning(self, "Error", "Invalid JSON structure! 'scenario.prompt' field is missing or null.")
             return
        if not isinstance(raw_prompt_value, list):
             QMessageBox.warning(self, "Error", f"Invalid JSON structure! 'scenario.prompt' should be a list, but found {type(raw_prompt_value).__name__}.")
             return
        if not raw_prompt_value:
             QMessageBox.warning(self, "Error", "Invalid JSON structure! 'scenario.prompt' list is empty.")
             return
        if not isinstance(raw_prompt_value[0], str):
             QMessageBox.warning(self, "Error", f"Invalid JSON structure! The first item in 'scenario.prompt' list should be a string, but found {type(raw_prompt_value[0]).__name__}.")
             return

        # Now we are sure raw_prompt_value is a non-empty list starting with a string
        prompt_list = raw_prompt_value

        # Get the full prompt text from the first list item
        full_prompt_text = prompt_list[0]

        # --- Determine the name for the comment field ---
        # Get the scenario name (can be None if null in JSON or key is missing)
        # This is accessed from the scenario_data dictionary, which we now get correctly
        scenario_name_potential = scenario_data.get("name")

        # Get the conversation name (provide a default if conversation object or name is missing)
        # This is accessed from the conversation_data dictionary
        conversation_name = conversation_data.get("name", "Unnamed Conversation")

        # Use scenario name if it exists and is not None, otherwise use conversation name
        scenario_name_for_comment = scenario_name_potential if scenario_name_potential is not None else conversation_name


        # --- Transformation Logic ---

        # Initialize variables for prompt spec details parsed from the string
        familiarity = None
        location = None
        core_prompt_lines = [] # To store the main prompt text excluding spec lines

        # Parse the full prompt text line by line to find spec details
        lines = full_prompt_text.splitlines()
        for line in lines:
            stripped_line = line.strip()
            if stripped_line.lower().startswith("familiarity:"):
                # Extract value after "Familiarity:"
                familiarity = stripped_line[len("familiarity:"):].strip()
            elif stripped_line.lower().startswith("location:"):
                 # Extract value after "Location:"
                 location = stripped_line[len("location:"):].strip()
            else:
                # This line is part of the core prompt
                core_prompt_lines.append(line)

        # Join the core prompt lines back together
        scenario_prompt = "\n".join(core_prompt_lines)

        # Construct the 'content' string by combining core prompt and parsed spec details
        content_parts = [scenario_prompt]
        spec_lines = []

        # Add specific prompt_spec fields if they were found during parsing
        if familiarity: # Check if familiarity was extracted
             spec_lines.append(f"{{{{char}}}} are: {familiarity}")

        if location: # Check if location was extracted
             spec_lines.append(f"location: {location}")

        # Add other prompt_spec fields here if needed in the future, parsed from lines

        if spec_lines:
            # Add a separator only if there are spec lines
            # Ensure the core prompt is not just whitespace before adding separator
            if scenario_prompt.strip():
                 content_parts.append("\n\n" + "\n".join(spec_lines))
            else:
                 # If there was no core prompt, just add the spec lines without double newline
                 content_parts.append("\n".join(spec_lines))


        # Join all parts to form the final content string
        content = "".join(content_parts).strip() # Use strip() to remove leading/trailing whitespace


        # Create the output dictionary structure
        output_json = {"entries": {}}
        entries_dict = {} # Dictionary to hold the single entry


        # Create the single entry dictionary
        entry = {
            "uid": 0,                      # Fixed as per output example
            "key": [],                     # Fixed as per output example
            "keysecondary": [],            # Fixed as per output example
            "comment": scenario_name_for_comment, # Use the determined name
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
            "matchWholeWords": None,         # Fixed value
            "useGroupScoring": None,         # Fixed value
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
        filename, _ = QFileDialog.getSaveFileName(self, "Save Output JSON", '.', 'JSON files (*.json)')
        if not filename:
            return

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_json, f)
            QMessageBox.information(self, "Success!", "JSON transformed and saved successfully!")
        except Exception as e:
             QMessageBox.critical(self, "Error Saving File", f"An error occurred while saving the file: {e}")

    
    def run(self):
        self.show()
        self.setWindowTitle("S.O.X. EXTRAS - Scenario Extraction Tool")
        self.setWindowIcon(QIcon('SOXico.png'))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    transformer = JSONTransformer()
    transformer.run()
    sys.exit(app.exec_())