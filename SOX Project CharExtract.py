import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QFileDialog, QVBoxLayout, QMessageBox, QLabel
from PyQt5.QtCore import Qt  # Add this line at the top of your code.
from PyQt5.QtGui import QPixmap  # Add this line
from PyQt5.QtGui import QIcon
import json
import re
import os

class JSONTransformer(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        
        # Create GUI components
        textSpacer = QLabel()
        textDesc = QLabel("Welcome to S.O.X. Project! This tool aims to convert XoulAI JSONs into TavernAI usable JSONs.\nThis one is dedicated to extract Xouls from chat backups and into Character Cards") 
        textCredits = QLabel("<i>by Junji Dragonfox @ Project BomberCraft</i>")
        loadButton = QPushButton("Import Xoul Chat JSON")
        saveButton = QPushButton("Export Multiple TavernAI JSON")
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
        QMessageBox.information(self, "CREDITS", "R.I.P. XoulAI, we hope you return someday, thanks for the moments.\n\nThanks Zenna for the advice\n\nTesters:\n\nTBA\n\nV0.0.2")

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
        """
        Transforms multiple character entries from a specific input JSON
        format and saves each character as a separate JSON file in a
        user-selected directory.
        """
        if not hasattr(self, 'inputJson') or not self.inputJson:
            QMessageBox.warning(self, "Warning", "No input JSON data available.")
            return

        # Access the 'conversation' and 'xouls' list
        conversation_data = self.inputJson.get("conversation")
        if not conversation_data:
            QMessageBox.warning(self, "Warning", "Input JSON does not contain 'conversation' data.")
            return

        xouls_list = conversation_data.get("xouls")
        if not xouls_list or not isinstance(xouls_list, list):
            QMessageBox.information(self, "Info", "No 'xouls' characters list found in the input JSON.")
            return

        # Get the overall conversation scenario, if any
        overall_scenario_prompt = conversation_data.get("scenario", {}).get("prompt")
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
            try:
                # Transformation logic based on the new input structure
                output_json = {
                    "name": character_data.get("name", ""),
                    "description": character_data.get("backstory", ""), # Backstory fits description
                    "personality": "",
                    "scenario": "", 
                    "first_mes": "",                                     # No clear equivalent in input character data
                    "mes_example": character_data.get("samples", ""),   # Use samples from character data
                    "creator_notes": character_data.get("bio", ""),     # Use bio from character data
                    "system_prompt": "",                                 # No equivalent
                    "post_history_instructions": "",                     # No equivalent
                    "tags": [],                                          # No 'social_tags' in input character data list
                    "creator": character_data.get("slug", ""),
                    "character_version": "imported",
                    "alternate_greetings": [],
                    "extensions": {
                        # Ensure talkativeness is a string as per example output
                        "talkativeness": str(character_data.get("talkativeness", "0.5")),
                        "fav": False,
                        "world": "",
                        "depth_prompt": {
                            "prompt": "",
                            "depth": 4,
                            "role": "system"
                        }
                    },
                    "group_only_greetings": []
                }

                # Determine filename based on name or slug, fallback to index
                character_name_slug = character_data.get("name") or character_data.get("slug")
                if not character_name_slug:
                     character_name_slug = f"unknown_character_{index}" # Fallback name if name/slug missing

                # Sanitize filename: remove invalid characters and replace spaces
                # Keep letters, numbers, hyphen, underscore, dot, space temporarily
                filename_base = re.sub(r'[^\w\-_\. ]', '', character_name_slug)
                # Replace spaces with underscores
                filename_base = filename_base.replace(' ', '_')

                # Ensure filename is not empty after sanitization
                if not filename_base:
                    filename_base = f"character_{index}"

                filename = f"{filename_base}.json"
                full_path = os.path.join(directory, filename)

                # Ensure the target directory exists
                os.makedirs(directory, exist_ok=True)

                # Save the transformed JSON to the file
                with open(full_path, 'w', encoding='utf-8') as f:
                    json.dump(output_json, f, indent=4) # Use indent for readability

                saved_count += 1

            except Exception as e:
                failed_count += 1
                # Identify the character that failed
                char_identifier = character_data.get("slug", character_data.get("name", f"index_{index}"))
                error_messages.append(f"Failed to process '{char_identifier}': {e}")
                # Optionally print the error to console for debugging
                print(f"Error processing character {char_identifier}: {e}")


        # Provide feedback to the user based on the results
        if saved_count > 0 and failed_count == 0:
            QMessageBox.information(self, "Success!",
                                   f"Successfully transformed and saved {saved_count} character JSON files to\n{directory}")
        elif saved_count > 0 and failed_count > 0:
            QMessageBox.warning(self, "Partial Success",
                                f"Successfully transformed and saved {saved_count} character files.\nFailed to save {failed_count} files.")
            # You could optionally show the error_messages list in a detailed dialog
            # or print them to the console for debugging.
            print("\n--- Processing Errors ---")
            for msg in error_messages:
                print(msg)
            print("-------------------------")
        elif failed_count > 0:
            QMessageBox.critical(self, "Failure",
                                 f"Failed to save all {failed_count} character files.")
            print("\n--- Processing Errors ---")
            for msg in error_messages:
                print(msg)
            print("-------------------------")
        else:
            # This case should ideally not happen if xouls_list was not empty
            QMessageBox.information(self, "Info", "No characters were processed or saved.")
        
    def run(self):
        self.show()
        self.setWindowTitle("S.O.X. EXTRAS - Xoul/Character Extraction Tool")
        self.setWindowIcon(QIcon('SOXico.png'))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    transformer = JSONTransformer()
    transformer.run()
    sys.exit(app.exec_())