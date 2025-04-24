import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QFileDialog, QVBoxLayout, QMessageBox, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon
import json
import os # Import os module
import re

class JSONTransformer(QWidget):
    def __init__(self):
        super().__init__()
        self.inputJson = None # Initialize inputJson attribute
        self.initUI()

    def initUI(self):
        self.setWindowTitle("S.O.X. - Multi-Chat Conversion Tool") # Update window title
        self.setWindowIcon(QIcon('SOXico.png')) # Use os.path.join for icon path

        # Create GUI components
        textSpacer = QLabel()
        textDesc = QLabel("Welcome to S.O.X. Project! This tool aims to convert XoulAI JSONs into TavernAI usable JSONs.\nThis one is dedicated to convert MULTI Xoul Chats into TavernAI Group Chats") 
        textCredits = QLabel("<i>by Junji Dragonfox @ Project BomberCraft</i>")
        loadButton = QPushButton("Import Xoul Chat JSON")
        saveButton = QPushButton("Export TavernAI Chat JSON")
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
        # Suggest .json files and filter
        filename, _ = QFileDialog.getOpenFileName(self, "Load XoulAI Input JSON", '.', 'JSON files (*.json);;All Files (*)')
        if not filename:
            return # User cancelled

        try:
            with open(filename, 'r', encoding='utf-8') as f: # Added encoding
                self.inputJson = json.load(f)
            QMessageBox.information(self, "Success!", f"JSON loaded successfully from {filename}!")
            #self.saveButton.setEnabled(True) # Enable save button after successful load

        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", f"Failed to decode JSON from {filename}. Please ensure it's a valid JSON file.")
            self.inputJson = None # Clear potential invalid data
            #self.saveButton.setEnabled(False)
        except FileNotFoundError:
             QMessageBox.critical(self, "Error", f"File not found: {filename}")
             self.inputJson = None
             #self.saveButton.setEnabled(False)
        except Exception as e:
            print("Error loading file:", str(e))
            QMessageBox.critical(self, "Error", f"An unexpected error occurred while loading: {str(e)}")
            self.inputJson = None
            #self.saveButton.setEnabled(False)


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

        # --- Fetch personas and xouls from their correct locations ---
        # Personas are under conversation
        all_personas = self.inputJson.get('conversation', {}).get('personas', [])
        # Xouls are at the top level
        all_xouls = self.inputJson.get('conversation', {}).get('xouls', [])
        # -----------------------------------------------------------


        output_json_lines = []

        try:
            # Process messages
            messages = self.inputJson.get('messages', []) # Assuming messages are also at the top level
            if not messages:
                 QMessageBox.warning(self, "Warning", "No messages found in input JSON. Saving an empty file.")
                 # Proceed to save an empty file (the loop won't run, output_json_lines will be empty)

            for message in messages:
                author_name = message.get('author_name')
                author_type = message.get('author_type') # 'user' or 'llm'
                timestamp = message.get('timestamp')
                content = message.get('content')

                # Skip messages with missing crucial data (original logic)
                # content can be empty string, so check if it's not None
                if not all([author_name, author_type, timestamp is not None]): # Check non-optional fields
                     print(f"Skipping message due to missing author_name, author_type, or timestamp: {message.get('message_id', 'N/A')}")
                     continue
                # Check content separately as it can be empty string but not None
                if content is None:
                     print(f"Skipping message due to missing content: {message.get('message_id', 'N/A')}")
                     continue


                # Determine name, is_user based on author_type
                output_name = author_name # Use the author's name directly
                is_user = (author_type == 'user')

                # Use the original timestamp string (original logic)
                output_timestamp = timestamp

                # --- NEW LOGIC TO FIND AVATAR URL ---
                avatar_url = None
                if author_type == 'user':
                    # Search in all_personas for the message's author_name
                    # Use next() with a default of None to avoid StopIteration if not found
                    found_entry = next((p for p in all_personas if p.get('name') == author_name), None)
                    if found_entry:
                        avatar_url = found_entry.get('icon_url')
                elif author_type == 'llm': # Assuming any non-user is an 'llm' in this context
                     # Search in all_xouls for the message's author_name
                     found_entry = next((x for x in all_xouls if x.get('name') == author_name), None)
                     if found_entry:
                         avatar_url = found_entry.get('icon_url')
                # If avatar_url is still None, it means the author wasn't found in the lists
                # or the entry didn't have an 'icon_url'. It will output as null in JSON.
                # -------------------------------------


                # Append the message data to the output list
                output_json_lines.append({
                    "name": output_name,
                    "is_user": is_user,
                    "is_system": False, # Keeping this as requested in the original output format
                    "send_date": output_timestamp,
                    "mes": content,
                    "force_avatar": avatar_url # ADD THE NEW KEY HERE with the found URL (or None)
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
