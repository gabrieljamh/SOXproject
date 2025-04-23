import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QFileDialog, QVBoxLayout, QMessageBox, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon
import json
import os # Import os module

class JSONTransformer(QWidget):
    def __init__(self):
        super().__init__()
        self.inputJson = None # Initialize inputJson attribute
        self.initUI()

    def initUI(self):
        self.setWindowTitle("S.O.X. - Multi-Chat Conversion Tool") # Update window title
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), 'SOXico.png'))) # Use os.path.join for icon path

        # Create GUI components
        textSpacer = QLabel()
        textDesc = QLabel("Welcome to S.O.X. Project! This tool aims to convert XoulAI JSONs into TavernAI usable JSONs.\nThis version converts **Multi-Xoul Chats** into a compatible JSON Lines format.")
        textCredits = QLabel("<i>by Junji Dragonfox @ Project BomberCraft</i>")
        loadButton = QPushButton("Import Xoul Multi-Chat JSON") # Update button text
        saveButton = QPushButton("Export TavernAI Chat JSONL") # Update button text and format
        creditButton = QPushButton("SEE CREDITS")
        textInput = QLabel("VV Station XoulAI VV")
        textOutput = QLabel("<i>-->> Next Station: TavernAI JSON Lines -->></i>") # Update output text
        imageLabel = QLabel()

        # Set an image - Check if the file exists before setting
        image_path = os.path.join(os.path.dirname(__file__), 'SOX.png')
        if os.path.exists(image_path):
             imageLabel.setPixmap(QPixmap(image_path))
        else:
             imageLabel.setText("Image not found: SOX.png") # Display message if image is missing
             imageLabel.setStyleSheet("color: red;") # Optional: make text red

        # --- Styles and Alignment ---
        imageLabel.setAlignment(Qt.AlignCenter)
        textDesc.setAlignment(Qt.AlignCenter)
        textDesc.setWordWrap(True) # Allow text to wrap
        textDesc.setTextFormat(Qt.RichText) # Allow rich text like **bold**
        textCredits.setAlignment(Qt.AlignRight)
        textCredits.setTextFormat(Qt.RichText)
        # textCredits.setOpenExternalLinks(True) # Removed - QLabel doesn't typically open links directly
        textInput.setAlignment(Qt.AlignCenter)
        textOutput.setAlignment(Qt.AlignCenter)
        textOutput.setTextFormat(Qt.RichText) # Allow rich text

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

        # Connect signals to slots
        loadButton.clicked.connect(self.loadInputFile)
        # Ensure saveButton is disabled initially until a file is loaded
        saveButton.setEnabled(False)
        saveButton.clicked.connect(self.transformJSONAndSave)
        creditButton.clicked.connect(self.creditsWND)

        self.saveButton = saveButton # Keep a reference to the save button
        self.setLayout(layout)


    def creditsWND(self):
        QMessageBox.information(self, "CREDITS", "R.I.P. XoulAI, we hope you return someday, thanks for the moments.\n\nTesters:\n\nTBA\n\nV0.0.1\n\n<i>Icon and Banner Art: BombshellFX</i>")

    def loadInputFile(self):
        # Suggest .json files and filter
        filename, _ = QFileDialog.getOpenFileName(self, "Load XoulAI Input JSON", '.', 'JSON files (*.json);;All Files (*)')
        if not filename:
            return # User cancelled

        try:
            with open(filename, 'r', encoding='utf-8') as f: # Added encoding
                self.inputJson = json.load(f)
            QMessageBox.information(self, "Success!", f"JSON loaded successfully from {filename}!")
            self.saveButton.setEnabled(True) # Enable save button after successful load

        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", f"Failed to decode JSON from {filename}. Please ensure it's a valid JSON file.")
            self.inputJson = None # Clear potential invalid data
            self.saveButton.setEnabled(False)
        except FileNotFoundError:
             QMessageBox.critical(self, "Error", f"File not found: {filename}")
             self.inputJson = None
             self.saveButton.setEnabled(False)
        except Exception as e:
            print("Error loading file:", str(e))
            QMessageBox.critical(self, "Error", f"An unexpected error occurred while loading: {str(e)}")
            self.inputJson = None
            self.saveButton.setEnabled(False)


    def transformJSONAndSave(self):
        # Check if input JSON is loaded
        if not hasattr(self, 'inputJson') or self.inputJson is None:
            QMessageBox.warning(self, "Error", "No input JSON loaded yet.")
            return

        # Suggest a default filename based on the conversation name, append .jsonl
        default_filename = "converted_chat.jsonl"
        try:
            conv_name = self.inputJson.get('conversation', {}).get('name', 'chat')
            # Sanitize filename: replace spaces with underscores, remove special chars
            import re
            sanitized_name = re.sub(r'[^\w\-_\. ]', '', conv_name).replace(' ', '_')
            if sanitized_name:
                 default_filename = f"{sanitized_name}_converted.jsonl"

        except Exception as e:
            print(f"Could not create default filename: {e}")
            pass # Use the generic default

        filename, _ = QFileDialog.getSaveFileName(self, "Save Output JSON Lines", default_filename, 'JSON Lines files (*.jsonl);;All Files (*)')
        if not filename:
            return # User cancelled

        # Ensure filename ends with .jsonl if no extension was given
        if not filename.lower().endswith('.jsonl'):
             filename += '.jsonl'


        try:
            # Extract user name for comparison
            # Assuming the first persona is the user
            user_name = self.inputJson.get('conversation', {}).get('personas', [{}])[0].get('name', 'User') # Default to 'User' if name not found

            output_json_lines = []

            # Process messages
            messages = self.inputJson.get('messages', [])
            if not messages:
                 QMessageBox.warning(self, "Warning", "No messages found in input JSON. Saving an empty file.")
                 # Proceed to save an empty file

            for message in messages:
                author_name = message.get('author_name')
                author_type = message.get('author_type') # 'user' or 'llm'
                timestamp = message.get('timestamp')
                content = message.get('content')

                # Skip messages with missing crucial data
                if not all([author_name, author_type, timestamp, content is not None]): # content can be empty string
                    print(f"Skipping message due to missing data: {message.get('message_id', 'N/A')}")
                    continue

                # Determine name, is_user, is_system based on author_type
                output_name = author_name # Use the author's name directly

                is_user = (author_type == 'user')
                is_system = (author_type == 'llm') # This covers both standard Xouls and the Narrator

                # Use the original timestamp string
                output_timestamp = timestamp

                output_json_lines.append({
                    "name": output_name,
                    "is_user": is_user,
                    "is_system": is_system, # Add the is_system flag as requested
                    "send_date": output_timestamp, # Keep the original timestamp format
                    "mes": content
                })

            # Save the output JSON in JSON Lines (jsonl) format
            # Added newline='' to prevent extra newlines on some systems
            with open(filename, 'w', encoding='utf-8', newline='') as f:
                for obj in output_json_lines:
                    f.write(json.dumps(obj, ensure_ascii=False) + '\n') # ensure_ascii=False to keep non-ASCII chars

            QMessageBox.information(self, "Success!", f"JSON transformed and saved successfully to {filename}!")

        except Exception as e:
            print("Error transforming and saving file:", str(e))
            QMessageBox.critical(self, "Error", f"An error occurred during transformation: {str(e)}")


    def run(self):
        self.show()
        # Window title and icon set in initUI now
        # self.setWindowTitle("S.O.X. - Single-Chat Conversion Tool") # Removed
        # self.setWindowIcon(QIcon('SOXico.png')) # Removed


if __name__ == '__main__':
    # Add the following lines to handle high-DPI displays if needed
    # QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    # QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    transformer = JSONTransformer()
    transformer.run()
    sys.exit(app.exec_())