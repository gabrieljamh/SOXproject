import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QFileDialog,
                             QVBoxLayout, QMessageBox, QLabel, QSizePolicy, QSpacerItem) # Added QSizePolicy and QSpacerItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon
import json
import os
import re


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
        textDesc = QLabel("Welcome to S.O.X. Project! This tool aims to convert XoulAI JSONs into TavernAI usable JSONs.\nThis one is dedicated to convert MULTI Xoul Chats into TavernAI Group Chats")
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
        self.setWindowTitle("S.O.X. - Multi-Chat Conversion Tool")
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
           "messages" in self.inputJson and \
           isinstance(self.inputJson.get("messages"), list):

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

            # Basic data structure check for Xoul Multi-Chat
            # Expecting a dictionary with 'conversation' dict AND 'messages' list at the top level
            if not isinstance(loaded_data, dict) or \
               "conversation" not in loaded_data or \
               not isinstance(loaded_data.get("conversation"), dict) or \
               "messages" not in loaded_data or \
               not isinstance(loaded_data.get("messages"), list):

                self.inputJson = None
                self._input_filename = None
                if self.loadedFileLabel: self.loadedFileLabel.setText("Invalid file structure")
                QMessageBox.critical(self, "Data Structure Error",
                                     f"The loaded file does not appear to be a valid Xoul Multi-Chat JSON.\n"
                                     f"Missing expected structure (e.g., top-level 'messages' list or 'conversation' dict).")
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
           "messages" not in self.inputJson or \
           not isinstance(self.inputJson.get("messages"), list):
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

            # Safely access lists (personas and xouls are under conversation, messages are top level)
            all_personas = conversation_data.get('personas', [])
            all_xouls = conversation_data.get('xouls', [])
            messages_list = self.inputJson.get('messages', []) # Messages are top level here!

            # Check if messages list is available and not empty
            if not isinstance(messages_list, list) or len(messages_list) == 0:
                 QMessageBox.information(self, "Info", "No 'messages' found in the chat JSON to convert.")
                 # Proceed to save an empty file or just return? Let's return if no messages.
                 return # Exit if no messages to process

            output_messages = []
            failed_message_count = 0

            # Iterate over the 'messages' list and create a new entry for each message
            for i, message in enumerate(messages_list):
                 if not isinstance(message, dict):
                     failed_message_count += 1
                     print(f"Skipping message at index {i}: Item is not a dictionary.")
                     continue # Skip item if not a dict

                 try:
                     author_name = message.get('author_name')
                     author_type = message.get('author_type') # 'user' or 'llm'
                     timestamp = message.get('timestamp')
                     content = message.get('content') # Can be empty string

                     # Skip messages with missing crucial data
                     if not all([author_name, author_type, timestamp is not None]):
                          print(f"Skipping message due to missing author_name, author_type, or timestamp: {message.get('message_id', f'index_{i}')}")
                          failed_message_count += 1 # Count this as a failed message
                          continue
                     if content is None:
                          print(f"Skipping message due to missing content: {message.get('message_id', f'index_{i}')}")
                          failed_message_count += 1 # Count this as a failed message
                          continue


                     # Determine name, is_user based on author_type
                     output_name = author_name # Use the author's name directly
                     is_user = (author_type == 'user')
                     is_system = False # TavernAI jsonl has this field, usually False for user/character msgs

                     # Use the original timestamp string
                     output_timestamp = timestamp

                     # --- Find AVATAR URL based on author_name and author_type ---
                     avatar_url = None
                     if author_type == 'user':
                         # Search in all_personas
                         found_entry = next((p for p in all_personas if isinstance(p, dict) and p.get('name') == author_name), None)
                         if found_entry:
                             avatar_url = found_entry.get('icon_url')
                     elif author_type == 'llm': # Assuming any non-user is an 'llm' in this context
                         # Search in all_xouls
                         found_entry = next((x for x in all_xouls if isinstance(x, dict) and x.get('name') == author_name), None)
                         if found_entry:
                             avatar_url = found_entry.get('icon_url')
                     # If avatar_url is still None, it means the author wasn't found in the lists
                     # or the entry didn't have an 'icon_url'. It will output as null in JSON.
                     # -----------------------------------------------------------


                     # Create the TavernAI chat message object
                     output_message = {
                         "name": output_name,
                         "is_user": is_user,
                         "is_system": is_system,
                         "send_date": output_timestamp, # Use original timestamp string
                         "mes": content,
                         "force_avatar": avatar_url # Add the found URL (or None)
                     }
                     output_messages.append(output_message)

                 except Exception as e:
                     # Catch any errors during processing of a single message
                     failed_message_count += 1
                     print(f"Error processing message at index {i}: {e}")
                     continue # Continue processing other messages

            # Check if any messages were successfully transformed
            successfully_converted_count = len(output_messages)
            if successfully_converted_count == 0 and len(messages_list) > 0:
                 # Only show this if there were *some* messages but none were converted
                 QMessageBox.warning(self, "Conversion Failed", "No messages were successfully processed from the chat JSON.")
                 print("\n--- No messages converted ---")
                 # Optionally disable the button again if no output was produced? No, keep loaded info.
                 # if self.saveButton: self.saveButton.setEnabled(False)
                 # if self.loadedFileLabel: self.loadedFileLabel.setText("No file loaded") # Or keep loaded file info? Keep file info.
                 return # Exit if nothing to save
            elif successfully_converted_count == 0 and len(messages_list) == 0:
                 # This case is handled by the check before the loop
                 return

            # --- Save the output JSON in JSON Lines (jsonl) format ---
            # Suggest a default filename based on the conversation name if available
            default_filename = "converted_group_chat.jsonl"
            try:
                 conv_name = conversation_data.get('name', 'group_chat')
                 # Sanitize filename: replace spaces with underscores, remove special chars
                 sanitized_name = re.sub(r'[^\w\-_\. ]', '', conv_name).replace(' ', '_')
                 if sanitized_name:
                      default_filename = f"{sanitized_name}_converted.jsonl"

            except Exception as e:
                 print(f"Could not create default filename: {e}")
                 pass # Use the generic default

            # Use Save File dialog, default to jsonl extension
            filename, _ = QFileDialog.getSaveFileName(self, "Save Output JSON Lines", default_filename, 'JSON Lines files (*.jsonl);;All files (*)') # Allow saving as other types too if needed
            if not filename:
                # User cancelled save. This is not an error.
                return

            # Ensure filename ends with .jsonl if the user didn't add it and selected the .jsonl filter
            # Note: QFileDialog often adds the extension automatically based on the selected filter
            if _ and 'JSON Lines files' in _ and not filename.lower().endswith('.jsonl'):
                 filename += '.jsonl'


            try:
                 # Use encoding='utf-8' for writing JSON Lines
                 # newline='' prevents Windows from adding extra \r
                 with open(filename, 'w', encoding='utf-8', newline='') as f:
                     for obj in output_messages:
                         # json.dumps default indent is None, which is suitable for jsonl
                         # ensure_ascii=False to keep non-ASCII characters like emojis etc.
                         json.dump(obj, f, ensure_ascii=False)
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
             # This might catch errors if accessing personas/xouls fails unexpectedly
             QMessageBox.critical(self, "General Error", f"An unexpected error occurred during chat transformation setup:\n{e}")
             print("General Error transforming:", str(e))


    def run(self):
        self.show()


if __name__ == '__main__':
    # Optional: Add these lines to handle high-DPI displays if needed on Windows/Linux
    # from PyQt5.QtCore import QT_VERSION_STR
    # print(f"PyQt5 version: {QT_VERSION_STR}")
    # if sys.platform.startswith('win') or sys.platform.startswith('linux'):
    #     QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    #     QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    transformer = JSONTransformer()
    transformer.run()
    sys.exit(app.exec_())