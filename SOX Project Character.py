import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QFileDialog,
                             QVBoxLayout, QMessageBox, QLabel, QSizePolicy, QSpacerItem)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon
import json
import re
import os # Make sure os is imported for os.path.basename

class JSONTransformer(QWidget):
    def __init__(self):
        super().__init__()
        self.inputJson = None
        # Keep references to widgets that need state changes
        self.saveButton = None
        self.loadedFileLabel = None
        self.initUI()

    def initUI(self):
        # Create GUI components
        textDesc = QLabel("Welcome to S.O.X. Project! This tool aims to convert XoulAI JSONs into TavernAI usable JSONs.\nThis one is dedicated to convert Xouls into Character Cards")
        textCredits = QLabel("<i>by Junji Dragonfox @ Project BomberCraft</i>")
        loadButton = QPushButton("Import Xoul JSON")

        # --- Store reference to saveButton and disable it initially ---
        self.saveButton = QPushButton("Export TavernAI JSON")
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
        textCredits.setOpenExternalLinks(True)
        textInput.setAlignment(Qt.AlignCenter)
        textOutput.setAlignment(Qt.AlignCenter)
        textOutput.setTextFormat(Qt.RichText)
        textOutput.setOpenExternalLinks(True)

        # Set an image - Added error handling
        try:
            pixmap = QPixmap('SOX.png')
            if pixmap.isNull():
                 print("Warning: Could not load SOX.png. Make sure it's in the same directory as the script.")
                 imageLabel.setText("SOX Image Placeholder")
            else:
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

        # Middle section: Input/Load
        layout.addWidget(textInput, alignment=Qt.AlignCenter)
        layout.addWidget(loadButton)

        # --- Add the loaded file label to the layout ---
        layout.addWidget(self.loadedFileLabel, alignment=Qt.AlignCenter)
        # --- End add label ---

        # Add a fixed space between Load and Save sections
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
        loadButton.clicked.connect(self.loadInputFile)
        self.saveButton.clicked.connect(self.transformJSONAndSave) # Connect using self.saveButton
        creditButton.clicked.connect(self.creditsWND)

        # --- Window Setup ---
        self.setLayout(layout)
        self.setWindowTitle("S.O.X. - Xoul/Character Conversion Tool")
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
        info_text = """
        R.I.P. XoulAI, we hope you return someday, thanks for the moments.

        Thanks Zenna for the advice

        Testers:
        TBA

        V0.0.2
        """
        QMessageBox.information(self, "CREDITS", info_text.strip())

    def loadInputFile(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Input JSON", '.', 'JSON files (*.json)')
        if not filename:
            self.inputJson = None
            # --- Reset state on cancel ---
            if self.saveButton: self.saveButton.setEnabled(False)
            if self.loadedFileLabel: self.loadedFileLabel.setText("No file loaded")
            # --- End reset ---
            return

        try:
            # --- Encoding Fix + Better Error Handling ---
            with open(filename, 'r', encoding='utf-8') as f:
                self.inputJson = json.load(f)
            # --- End Fix ---

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
        # Check if inputJson exists and contains data
        if not hasattr(self, 'inputJson') or not isinstance(self.inputJson, dict) or not self.inputJson:
            # This warning should ideally not be needed if the button state is managed correctly,
            # but it's a safe fallback.
            QMessageBox.warning(self, "Warning", "No input JSON data loaded or data is invalid.")
            # Optionally disable the button here too, though loadInputFile manages it.
            # if self.saveButton: self.saveButton.setEnabled(False)
            return

        try:
            # Define the desired output structure and map input fields using .get() for safety
            output_json = {
                "name": self.inputJson.get("name", ""),
                "description": self.inputJson.get("backstory", ""),
                "personality": self.inputJson.get("definition", ""),
                "scenario": self.inputJson.get("default_scenario", ""),
                "first_mes": self.inputJson.get("greeting", ""),
                "mes_example": self.inputJson.get("samples", ""),
                "creator_notes": self.inputJson.get("bio", ""),
                "system_prompt": "",
                "post_history_instructions": "",
                "tags": self.inputJson.get("social_tags", []),
                "creator": self.inputJson.get("slug", ""),
                "character_version": "imported",
                "alternate_greetings": [],
                "extensions": {
                    "talkativeness": str(self.inputJson.get("talkativeness", "0.5")),
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

            # Get a default filename based on the character name or slug
            default_filename_base = self.inputJson.get("name") or self.inputJson.get("slug", "transformed_character")
            # Sanitize filename - kept regex logic
            filename_base = re.sub(r'[^\w\-_\. ]', '', default_filename_base)
            filename_base = filename_base.replace(' ', '_')
            if not filename_base:
                filename_base = "transformed_character"

            # Suggest a default filename in the save dialog
            default_save_name = f"{filename_base}.json"

            filename, _ = QFileDialog.getSaveFileName(self, "Save Output JSON", default_save_name, 'JSON files (*.json)')
            if not filename:
                return # User cancelled

            # Ensure filename ends with .json if user didn't add it
            if not filename.lower().endswith('.json'):
                filename += '.json'

            # --- Encoding Fix + Indent ---
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_json, f, indent=4)
            # --- End Fix ---

            QMessageBox.information(self, "Success!", f"JSON transformed and saved successfully to:\n{filename}")

        except KeyError as e:
             QMessageBox.critical(self, "Transformation Error", f"Missing expected data in input JSON:\nKey '{e}' not found.")
             print(f"Transformation error: Missing key {e}")
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