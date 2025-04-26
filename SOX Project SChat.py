import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QFileDialog,
                             QVBoxLayout, QMessageBox, QLabel, QSizePolicy, QSpacerItem) # Added QSizePolicy and QSpacerItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon
import json
import os
import re # Keep re, might be useful though not strictly needed for this transformation


class JSONTransformer(QWidget):
    def __init__(self):
        super().__init__()
        # Initialize attribute to store loaded data and filename
        self.inputJson = None
        self._input_filename = None  # Store filename

        # Keep references to widgets that need state changes
        self.saveButton = None
        self.loadedFileLabel = None

        self.initUI()

    def initUI(self):
        # Create GUI components
        # Removed textSpacer - will use QSpacerItem
        textDesc = QLabel("Welcome to S.O.X. Project! This tool aims to convert XoulAI JSONs into TavernAI usable JSONs.\nThis one is dedicated to convert Single Xoul Chats into TavernAI Character Chats")
        textCredits = QLabel("<i>by Junji Dragonfox @ Project BomberCraft</i>")
        loadButton = QPushButton("Import Xoul Chat JSON")

        # --- Store reference to saveButton and disable it initially ---
        self.saveButton = QPushButton("Export TavernAI Chat JSON")
        self.saveButton.setEnabled(False)  # Disable button initially
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
        textCredits.setOpenExternalLinks(True)  # QLabel typically cannot open links
        textInput.setAlignment(Qt.AlignCenter)
        textOutput.setAlignment(Qt.AlignCenter)
        textOutput.setTextFormat(Qt.RichText)  # Not strictly needed
        textOutput.setOpenExternalLinks(True)  # QLabel typically cannot open links

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
        layout.addWidget(imageLabel, alignment=Qt.AlignCenter)  # Added alignment flag directly
        layout.addWidget(textDesc, alignment=Qt.AlignCenter)  # Added alignment flag directly

        # Add flexible space to push main content down
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))  # width, height, hPolicy, vPolicy

        # Middle section: Input/Load
        layout.addWidget(textInput, alignment=Qt.AlignCenter)  # Added alignment flag directly
        layout.addWidget(loadButton)  # Buttons stretch horizontally in QVBoxLayout by default

        # --- Add the loaded file label to the layout ---
        layout.addWidget(self.loadedFileLabel, alignment=Qt.AlignCenter)
        # --- End add label ---

        # Add a fixed space between Load and Save sections
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Middle section: Output/Save
        layout.addWidget(textOutput, alignment=Qt.AlignCenter)  # Added alignment flag directly
        layout.addWidget(self.saveButton)  # Use self.saveButton reference

        # Add flexible space to push credits to the bottom
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Bottom section: Credits
        layout.addWidget(textCredits, alignment=Qt.AlignRight)  # Added alignment flag directly
        layout.addWidget(creditButton, alignment=Qt.AlignRight)  # Align button to the right

        # --- Connections ---
        loadButton.clicked.connect(self.loadInputFile)
        self.saveButton.clicked.connect(self.transformJSONAndSave)  # Connect using self.saveButton
        creditButton.clicked.connect(self.creditsWND)

        # --- Window Setup ---
        self.setLayout(layout)
        self.setWindowTitle("S.O.X. - Single-Chat Conversion Tool")
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
        QMessageBox.information(self, "CREDITS", info_text.strip())  # Use strip() for cleaner message

    def _check_enable_save(self):
        """Checks if the input file is loaded and has the minimum expected structure."""
        # Check if inputJson is a dict and has the basic structure keys
        if isinstance(self.inputJson, dict) and \
           "conversation" in self.inputJson and \
           isinstance(self.inputJson.get("conversation"), dict) and \
           "messages" in self.inputJson["conversation"] and \
           isinstance(self.inputJson["conversation"].get("messages"), list):

            self.saveButton.setEnabled(True)
            print("Input file loaded and basic chat structure found. Save button enabled.")
        else:
            self.saveButton.setEnabled(False)
            print("Waiting for input file to be loaded or structure invalid.")


    def loadInputFile(self):
        # Load Xoul Chat JSON file
        # Added file filter and default directory
        filename, _ = QFileDialog.getOpenFileName(self, "Load Xoul Chat JSON", '.', 'JSON files (*.json)')
        if not filename:
            self.inputJson = None
            self._input_filename = None
            if self.loadedFileLabel: self.loadedFileLabel.setText("No file loaded")
            self._check_enable_save()  # Re-check save button state
            return

        try:
            # --- Encoding Fix + Better Error Handling ---
            # Specify encoding='utf-8' when opening the file
            with open(filename, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            # --- End Fix ---

            # Basic data structure check for Xoul Chat
            # Expecting a dictionary with 'conversation' key which contains 'messages' list
            if not isinstance(loaded_data, dict) or \
               "conversation" not in loaded_data or \
               not isinstance(loaded_data.get("conversation"), dict) or \
               "messages" not in loaded_data["conversation"] or \
               not isinstance(loaded_data["conversation"].get("messages"), list):

                self.inputJson = None
                self._input_filename = None
                if self.loadedFileLabel: self.loadedFileLabel.setText("Invalid file structure")
                QMessageBox.critical(self, "Data Structure Error",
                                     f"The loaded file does not appear to be a valid Xoul Chat JSON.\n"
                                     f"Missing expected structure (e.g., 'conversation.messages').")
                print(f"Data structure error in {filename}: Missing expected keys or wrong types.")
            else:
                self.inputJson = loaded_data
                self._input_filename = filename  # Store filename on success
                if self.loadedFileLabel: self.loadedFileLabel.setText(f"Loaded: {os.path.basename(filename)}")  # Display filename
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

        self._check_enable_save()  # Always check state after attempting load


    def transformJSONAndSave(self):
        # Check if inputJson is loaded and has the expected structure
        if not isinstance(self.inputJson, dict) or \
           "conversation" not in self.inputJson or \
           not isinstance(self.inputJson.get("conversation"), dict) or \
           "messages" not in self.inputJson["conversation"] or \
           not isinstance(self.inputJson["conversation"].get("messages"), list):
            # This warning should ideally not be needed if the button state is managed correctly,
            # but it's a safe fallback.
            QMessageBox.warning(self, "Error", "No valid Chat JSON data loaded or structure is invalid!")
            # Optionally disable the button here too, though loadInputFile manages it.
            # if self.saveButton: self.saveButton.setEnabled(False)
            # if self.loadedFileLabel: self.loadedFileLabel.setText("No file loaded")
            return

        try:
            # Access conversation data safely
            conversation_data = self.inputJson.get('conversation', {})

            # Safely extract relevant information (assuming only one persona/xoul)
            personas_list = conversation_data.get('personas', [])
            xouls_list = conversation_data.get('xouls', [])
            messages_list = conversation_data.get('messages', [])

            # Check if personas/xouls lists are available and not empty
            if not isinstance(personas_list, list) or len(personas_list) == 0:
                 QMessageBox.warning(self, "Data Warning", "No 'personas' list found or it's empty in the chat JSON.")
                 return
            if not isinstance(xouls_list, list) or len(xouls_list) == 0:
                 QMessageBox.warning(self, "Data Warning", "No 'xouls' list found or it's empty in the chat JSON.")
                 return
            if not isinstance(messages_list, list) or len(messages_list) == 0:
                 QMessageBox.information(self, "Info", "No 'messages' found in the chat JSON to convert.")
                 return # Exit if no messages to process

            # Get the first persona and xoul dictionary safely
            first_persona = personas_list[0] if isinstance(personas_list[0], dict) else {}
            first_xoul = xouls_list[0] if isinstance(xouls_list[0], dict) else {}

            username = first_persona.get('name', 'User') # Default to 'User' if name missing
            character_name = first_xoul.get('name', 'Character') # Default to 'Character' if name missing

            # Create the output JSON structure (a list of message objects for jsonl)
            output_messages = []

            # Original code added a header message - replicating this structure first
            # This header structure doesn't match standard TavernAI chat jsonl format,
            # but replicating the original script's output logic.
            # NOTE: TavernAI jsonl typically just contains the message objects directly.
            # If true TavernAI jsonl is needed, this initial object should be removed.
            # output_messages.append({
            #     "user_name": username,
            #     "character_name": character_name
            # }) # Removed this header to match typical TavernAI jsonl

            failed_message_count = 0
            # Iterate over the 'messages' list and create a new entry for each message
            for i, message in enumerate(messages_list):
                 if not isinstance(message, dict):
                     failed_message_count += 1
                     print(f"Skipping message at index {i}: Item is not a dictionary.")
                     continue # Skip item if not a dict

                 try:
                     role = message.get('role')
                     content = message.get('content', '') # Default content to empty string
                     timestamp = message.get('timestamp', '') # Default timestamp to empty string

                     # Determine sender name based on role
                     sender_name = None
                     is_user = False
                     is_system = False # TavernAI jsonl has this field

                     if role == 'user':
                         sender_name = username
                         is_user = True
                     elif role == 'assistant':
                         sender_name = character_name
                         is_user = False # Assistant is not user
                     elif role == 'system': # Check for system messages
                         sender_name = 'System' # Default name for system messages
                         is_system = True
                         is_user = False
                         # Note: XoulAI chat backups might not have 'system' role messages
                         # if they do, you might need to adjust 'sender_name' based on content or other keys.
                     else:
                         # Handle unexpected roles - skip or assign a default name?
                         # Original code raised ValueError, let's log and skip for robustness.
                         failed_message_count += 1
                         print(f"Skipping message at index {i}: Unexpected role '{role}'.")
                         continue # Skip message with unknown role

                     # Create the TavernAI chat message object
                     output_message = {
                         "name": sender_name,
                         "is_user": is_user,
                         "is_system": is_system,
                         "send_date": timestamp,
                         "mes": content
                     }
                     output_messages.append(output_message)

                 except Exception as e:
                     # Catch any errors during processing of a single message
                     failed_message_count += 1
                     print(f"Error processing message at index {i}: {e}")
                     continue # Continue processing other messages

            # Check if any messages were successfully transformed
            successfully_converted_count = len(output_messages)
            if successfully_converted_count == 0:
                 QMessageBox.information(self, "Info", "No valid messages were found or processed from the chat JSON.")
                 # Optionally disable the button again if no output was produced
                 # if self.saveButton: self.saveButton.setEnabled(False)
                 # if self.loadedFileLabel: self.loadedFileLabel.setText("No file loaded") # Or keep loaded file info? Keep file info.
                 return # Exit if nothing to save

            # --- Save the output JSON in JSON Lines (jsonl) format ---
            # Suggest a default filename based on the original input filename
            default_save_name = "converted_chat.jsonl"
            if self._input_filename:
                 base, ext = os.path.splitext(os.path.basename(self._input_filename))
                 default_save_name = f"{base}.jsonl" # Use original base name + .jsonl

            # Use Save File dialog, default to jsonl extension
            filename, _ = QFileDialog.getSaveFileName(self, "Save Output JSON Lines", default_save_name, 'JSON Lines files (*.jsonl);;All files (*)') # Allow saving as other types too if needed
            if not filename:
                # User cancelled save. This is not an error.
                return

            # Ensure filename ends with .jsonl if the user didn't add it and selected the .jsonl filter
            if not filename.lower().endswith('.jsonl') and 'JSON Lines files' in _ :
                 filename += '.jsonl'


            try:
                 # Use encoding='utf-8' for writing JSON Lines
                 with open(filename, 'w', encoding='utf-8') as f:
                     for obj in output_messages:
                         # json.dumps default indent is None, which is suitable for jsonl
                         json.dump(obj, f) # Dump the object as a single line JSON string
                         f.write('\n') # Write a newline after each JSON object

                 # Provide feedback to the user based on the results
                 if failed_message_count == 0:
                     QMessageBox.information(self, "Success!",
                                            f"Successfully converted and saved {successfully_converted_count} messages to\n{filename}")
                 else:
                     QMessageBox.warning(self, "Partial Success",
                                         f"Successfully converted and saved {successfully_converted_count} messages.\n"
                                         f"Failed to process {failed_message_count} messages (see console for details).")


            except IOError as e:
                 QMessageBox.critical(self, "File Writing Error", f"Failed to write the output file:\n{e}")
                 print(f"IO Error saving file {filename}: {e}")
            except Exception as e:
                 # Catch any other unexpected errors during saving
                 QMessageBox.critical(self, "General Error", f"An unexpected error occurred during saving:\n{e}")
                 print("General Error saving:", str(e))


        except Exception as e:
             # Catch any unexpected errors during the initial transformation setup
             QMessageBox.critical(self, "General Error", f"An unexpected error occurred during chat transformation setup:\n{e}")
             print("General Error transforming:", str(e))


    def run(self):
        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    transformer = JSONTransformer()
    transformer.run()
    sys.exit(app.exec_())