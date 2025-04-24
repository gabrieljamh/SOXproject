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
        textDesc = QLabel("Welcome to S.O.X. Project! This tool aims to convert XoulAI JSONs into TavernAI usable JSONs.\nThis one is dedicated to convert Scenario into TavernAI World Single Entry.\nShould be attached at the chat") 
        textCredits = QLabel("<i>by Junji Dragonfox @ Project BomberCraft</i>")
        loadButton = QPushButton("Import Xoul Scenario JSON")
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
        filename, _ = QFileDialog.getOpenFileName(self, "Load Input JSON")
        if not filename:
            return
        try:
            with open(filename, 'r') as f:
                self.inputJson = json.load(f)
            QMessageBox.information(self, "Success!", "JSON loaded successfully!")
        except Exception as e:
            print("Error loading file:", str(e))

    def transformJSONAndSave(self):
        # Check if inputJson is loaded and is a dictionary (expected format)
        if not hasattr(self, 'inputJson') or not isinstance(self.inputJson, dict):
            # Assuming QMessageBox is available
            QMessageBox.warning(self, "Error", "No valid JSON data loaded! Please load a scenario JSON first.")
            return

        # Use the loaded input dictionary directly
        input_data = self.inputJson

        # Create the output dictionary structure
        output_json = {"entries": {}}
        entries_dict = {} # Dictionary to hold the single entry

        # --- Transformation Logic based on the new input/output examples ---

        # Extract necessary data from the single input object
        scenario_name = input_data.get("name", "")
        scenario_prompt = input_data.get("prompt", "")
        prompt_spec = input_data.get("prompt_spec", {}) # Get the prompt_spec dictionary

        # Construct the 'content' string by combining prompt and prompt_spec details
        content_parts = [scenario_prompt]
        if prompt_spec: # Check if prompt_spec exists and is not empty
            spec_lines = []
            # Add specific prompt_spec fields if they exist and are not None
            familiarity = prompt_spec.get("familiarity")
            if familiarity is not None:
                 spec_lines.append(f"{{{{char}}}} are: {familiarity}")

            location = prompt_spec.get("location")
            if location is not None:
                 spec_lines.append(f"location: {location}")

            # Add other prompt_spec fields here if needed in the future

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
        # Assuming QFileDialog is available
        filename, _ = QFileDialog.getSaveFileName(self, "Save Output JSON", '.', 'JSON files (*.json)')
        if not filename:
            return # User cancelled the dialog

        try:
            with open(filename, 'w') as f:
                # json.dump(output_json, f, indent=4) # Optional: Use indent for readability
                json.dump(output_json, f) # Save in compact format matching example
            # Assuming QMessageBox is available
            QMessageBox.information(self, "Success!", "JSON transformed and saved successfully!")
        except Exception as e:
             # Assuming QMessageBox is available
             QMessageBox.critical(self, "Error Saving File", f"An error occurred while saving the file: {e}")
    
    def run(self):
        self.show()
        self.setWindowTitle("S.O.X. - Scenario Conversion Tool")
        self.setWindowIcon(QIcon('SOXico.png'))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    transformer = JSONTransformer()
    transformer.run()
    sys.exit(app.exec_())