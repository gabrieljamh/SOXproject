import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QFileDialog,
                             QVBoxLayout, QMessageBox, QLabel, QSizePolicy, QSpacerItem,
                             QStackedWidget, QHBoxLayout, QProgressBar)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon, QFont
import json
import os
import re
import requests
from urllib.parse import urlparse
import hashlib
from datetime import datetime # Import datetime

# --- Helper function to safely load JSON ---
def safe_json_load(filename):
    """Loads a JSON file with UTF-8 encoding and handles common errors."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        QMessageBox.critical(None, "Error", f"File not found:\n{filename}")
        print(f"Error: File not found: {filename}")
        return None
    except json.JSONDecodeError as e:
        QMessageBox.critical(None, "JSON Parsing Error", f"Failed to parse JSON from file:\n{filename}\n{e}")
        print(f"JSON parsing error details for {filename}: {e}")
        return None
    except UnicodeDecodeError as e:
        QMessageBox.critical(None, "Encoding Error", f"Failed to read file with UTF-8 encoding:\n{filename}\n{e}\n\nTry opening it in a text editor and saving as UTF-8.")
        print(f"Decoding Error details for {filename}: {e}")
        return None
    except Exception as e:
        QMessageBox.critical(None, "File Reading Error", f"An unexpected error occurred while reading the file:\n{filename}\n{e}")
        print(f"General Error loading file {filename}:", str(e))
        return None

# --- Helper function to safely save JSON ---
def safe_json_save(data, filename, indent=4, is_jsonl=False):
    """Saves data to a JSON or JSON Lines file with UTF-8 encoding and handles errors."""
    try:
        with open(filename, 'w', encoding='utf-8', newline='' if is_jsonl else '') as f:
            if is_jsonl:
                if isinstance(data, list):
                    for item in data:
                        json.dump(item, f, ensure_ascii=False)
                        f.write('\n')
                else:
                     # Handle case where a single dict is passed but jsonl is requested (unusual but safe)
                     json.dump(data, f, ensure_ascii=False)
                     f.write('\n')
            else:
                json.dump(data, f, indent=indent, ensure_ascii=False)
        return True # Indicate success
    except IOError as e:
        QMessageBox.critical(None, "File Writing Error", f"Failed to write the output file:\n{filename}\n{e}")
        print(f"IO Error saving file {filename}: {e}")
        return False # Indicate failure
    except Exception as e:
        QMessageBox.critical(None, "General Error", f"An unexpected error occurred while saving:\n{filename}\n{e}")
        print(f"General Error saving file {filename}:", str(e))
        return False # Indicate failure

# --- Helper to load the common SOX image ---
def load_sox_image_label():
    """Creates a QLabel with the SOX image, handling errors."""
    imageLabel = QLabel()
    imageLabel.setAlignment(Qt.AlignCenter)
    try:
        pixmap = QPixmap('SOX.png')
        if pixmap.isNull():
             print("Warning: Could not load SOX.png. Make sure it's in the same directory as the script.")
             imageLabel.setText("SOX Image Placeholder")
        else:
            # Optional: Scale image if too large. Adjust size as needed for tool views.
            # For tool views, maybe a smaller scaled version? E.g., .scaled(150, 100, ...)
            # You can add scaling logic here if needed.
            imageLabel.setPixmap(pixmap)
    except Exception as e:
        print(f"Error loading SOX.png: {e}")
        imageLabel.setText("SOX Image Placeholder")
    return imageLabel


# --- New Credits Window Widget ---
class CreditsWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.setWindowTitle("S.O.X. Project Credits")

        try:
            icon = QIcon('SOXico.png') # Reusing the main icon, or use a different one
            if not icon.isNull():
                 self.setWindowIcon(icon)
        except Exception as e:
            print(f"Error loading icon for credits window: {e}")

        layout = QVBoxLayout()

        # --- Add the Credits Image Header ---
        creditsImageLabel = QLabel()
        creditsImageLabel.setAlignment(Qt.AlignCenter)
        try:
            # Load the specific Credits image
            pixmap = QPixmap('Credits.png')
            if pixmap.isNull():
                 print("Warning: Could not load Credits.png. Make sure it's in the same directory as the script.")
                 creditsImageLabel.setText("Credits Image Placeholder") # Display placeholder if image fails
            else:
                # Optional: Scale the image if needed
                # pixmap = pixmap.scaled(300, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                creditsImageLabel.setPixmap(pixmap)
        except Exception as e:
            print(f"Error loading Credits.png: {e}")
            creditsImageLabel.setText("Credits Image Placeholder") # Display placeholder if image fails

        layout.addWidget(creditsImageLabel, alignment=Qt.AlignCenter)
        # --- End Image Header ---

        layout.addItem(QSpacerItem(20, 15, QSizePolicy.Minimum, QSizePolicy.Fixed)) # Spacer

        # --- Add the Credits Text ---
        credits_text = """
R.I.P. XoulAI, we hope you return someday, thanks for the moments.

Thanks Zenna for the advice
Thanks to IoneArtemis by the support

Testers:
Nikguy

V0.2.0 (Stable Merged build)

-->> Next Station: TavernAI -->>
"""
        # Using QLabel for simple text. If you need rich text (like clickable links),
        # consider using QTextBrowser instead and setting its textFormat to Qt.RichText
        textLabel = QLabel(credits_text.strip())
        textLabel.setAlignment(Qt.AlignCenter) # Center the text
        # textLabel.setTextFormat(Qt.RichText) # Uncomment if using QTextBrowser or if QLabel supports limited rich text
        # textLabel.setOpenExternalLinks(True) # Uncomment if using QTextBrowser and have links

        layout.addWidget(textLabel, alignment=Qt.AlignCenter)
        # --- End Credits Text ---

        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)) # Flexible spacer

        # --- Add a Close Button ---
        closeButton = QPushButton("Close")
        closeButton.clicked.connect(self.close) # Connect to the window's close method
        layout.addWidget(closeButton, alignment=Qt.AlignCenter) # Center the button
        # --- End Close Button ---

        layout.addItem(QSpacerItem(20, 15, QSizePolicy.Minimum, QSizePolicy.Fixed)) # Spacer

        self.setLayout(layout)
        # Set a fixed size or minimum size if desired
        # self.setFixedSize(400, 400)
        # self.setMinimumSize(300, 300)


# --- Renamed Tool Classes ---

# --- 7. EXTRA Tools: Extract Characters (from Chat Backup) --- (Original #1)
class Tool_CharExtract(QWidget):
    def __init__(self, stacked_widget=None):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.inputJson = None
        self._input_filename = None
        self.saveButton = None
        self.loadedFileLabel = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        backButton = QPushButton("<- Back to Main Menu")
        backButton.clicked.connect(self._go_back)
        layout.addWidget(backButton)

        layout.addWidget(load_sox_image_label(), alignment=Qt.AlignCenter)
        textDesc = QLabel("Extract Xouls from Chat Backup and convert to Multiple TavernAI Characters Cards")
        textDesc.setAlignment(Qt.AlignCenter)
        layout.addWidget(textDesc)
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))
        layout.addWidget(QLabel("VV Station XoulAI VV"), alignment=Qt.AlignCenter)
        loadButton = QPushButton("Import Xoul Chat JSON")
        self.saveButton = QPushButton("Export Multiple TavernAI JSON")
        self.saveButton.setEnabled(False) # Disable initially
        self.loadedFileLabel = QLabel("No file loaded")
        self.loadedFileLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(loadButton)
        layout.addWidget(self.loadedFileLabel, alignment=Qt.AlignCenter)
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))
        layout.addWidget(QLabel("<i>-->> Next Station: TavernAI -->></i>"), alignment=Qt.AlignCenter)
        layout.addWidget(self.saveButton)
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        loadButton.clicked.connect(self.loadInputFile)
        self.saveButton.clicked.connect(self.transformJSONAndSave)
        self.setLayout(layout)

    def _go_back(self):
        self.inputJson = None
        self._input_filename = None
        if self.saveButton: self.saveButton.setEnabled(False)
        if self.loadedFileLabel: self.loadedFileLabel.setText("No file loaded")
        if self.stacked_widget: self.stacked_widget.setCurrentIndex(0)

    def _check_enable_save(self):
        if isinstance(self.inputJson, dict) and \
           "conversation" in self.inputJson and isinstance(self.inputJson.get("conversation"), dict) and \
           "xouls" in self.inputJson["conversation"] and isinstance(self.inputJson["conversation"].get("xouls"), list):
            self.saveButton.setEnabled(True)
            print("Input file loaded and expected chat character structure found. Save button enabled.")
        else:
            self.saveButton.setEnabled(False)
            print("Waiting for input file to be loaded or structure invalid for character extraction.")

    def loadInputFile(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Xoul Chat JSON", '.', 'JSON files (*.json)')
        if not filename:
            self.inputJson = None
            self._input_filename = None
            self.loadedFileLabel.setText("No file loaded")
            self._check_enable_save() # FIX: Added self.
            return

        loaded_data = safe_json_load(filename)
        if loaded_data:
            if not isinstance(loaded_data, dict) or \
               "conversation" not in loaded_data or \
               not isinstance(loaded_data.get("conversation"), dict) or \
               "xouls" not in loaded_data["conversation"] or \
               not isinstance(loaded_data["conversation"].get("xouls"), list):
                self.inputJson = None
                self._input_filename = None
                self.loadedFileLabel.setText("Invalid file structure")
                QMessageBox.critical(self, "Data Structure Error",
                                     f"The loaded file does not appear to be a valid Xoul Chat JSON for character extraction.\n"
                                     f"Missing expected structure (e.g., 'conversation.xouls').")
                print(f"Data structure error in {filename}: Missing expected keys or wrong types for character extraction.")
            else:
                self.inputJson = loaded_data
                self._input_filename = filename
                self.loadedFileLabel.setText(f"Loaded: {os.path.basename(filename)}")
                QMessageBox.information(self, "Success!", "JSON loaded successfully!")
        else: # loaded_data is None
            self.inputJson = None
            self._input_filename = None
            self.loadedFileLabel.setText("Load failed")

        self._check_enable_save() # FIX: Added self.

    def transformJSONAndSave(self):
        if not isinstance(self.inputJson, dict) or \
           "conversation" not in self.inputJson or \
           not isinstance(self.inputJson.get("conversation"), dict) or \
           "xouls" not in self.inputJson["conversation"] or \
           not isinstance(self.inputJson["conversation"].get("xouls"), list):
            QMessageBox.warning(self, "Error", "No valid JSON data loaded or structure is invalid!")
            self._check_enable_save()
            return

        conversation_data = self.inputJson.get("conversation", {})
        xouls_list = conversation_data.get("xouls", [])

        if not xouls_list:
            QMessageBox.information(self, "Info", "No 'xouls' characters list found or list is empty in the loaded JSON.")
            return

        directory = QFileDialog.getExistingDirectory(self, "Select Directory to Save Character JSONs")

        if not directory:
            return

        try:
             os.makedirs(directory, exist_ok=True)
        except Exception as e:
             QMessageBox.critical(self, "Directory Error", f"Failed to create or access output directory:\n{directory}\n{e}")
             return

        saved_count = 0
        failed_count = 0
        error_messages = []

        for index, character_data in enumerate(xouls_list):
            if not isinstance(character_data, dict):
                 failed_count += 1
                 error_messages.append(f"Skipping item at index {index}: Data is not a dictionary.")
                 print(f"Error processing item at index {index}: Expected dictionary, got {type(character_data)}")
                 continue

            try:
                output_json = {
                    "name": character_data.get("name", ""), "description": character_data.get("backstory", ""),
                    "personality": "", "scenario": "", "first_mes": "", "mes_example": character_data.get("samples", ""),
                    "creator_notes": character_data.get("bio", ""), "system_prompt": "", "post_history_instructions": "",
                    "tags": [], "creator": character_data.get("slug", ""), "character_version": "imported",
                    "alternate_greetings": [],
                    "extensions": {
                        "talkativeness": str(character_data.get("talkativeness", "0.5")), "fav": False, "world": "",
                        "depth_prompt": {"prompt": "", "depth": 4, "role": "system"}
                    },
                    "group_only_greetings": []
                }
                character_name_slug = character_data.get("name") or character_data.get("slug")
                if not character_name_slug: character_name_slug = f"unknown_character_{index}"
                filename_base = re.sub(r'[^\w\-_\. ]', '_', character_name_slug).replace(' ', '_')
                if not filename_base: filename_base = f"character_{index}"
                filename = f"{filename_base}.json"
                full_path = os.path.join(directory, filename)

                if safe_json_save(output_json, full_path, indent=4): saved_count += 1
                else: # Corrected semicolon usage
                     failed_count += 1
                     char_identifier = character_data.get("slug", character_data.get("name", f"index_{index}"))
                     error_messages.append(f"Failed to save file for '{char_identifier}'. See previous error message.")

            except Exception as e:
                failed_count += 1
                char_identifier = character_data.get("slug", character_data.get("name", f"index_{index}"))
                error_messages.append(f"Failed to process '{char_identifier}': {e}")
                print(f"Error processing character {char_identifier}: {e}")

        if saved_count > 0 and failed_count == 0:
            QMessageBox.information(self, "Success!", f"Successfully transformed and saved {saved_count} character JSON files to\n{directory}")
        elif saved_count > 0 and failed_count > 0:
            QMessageBox.warning(self, "Partial Success", f"Successfully transformed and saved {saved_count} character files.\nFailed to save {failed_count} files.")
            detail_msg = "Processing Details:\n" + "\n".join(error_messages[:10])
            if len(error_messages) > 10: detail_msg += "\n..."
            QMessageBox.information(self, "Processing Details", detail_msg)
            print("\n--- Processing Errors ---")
            for msg in error_messages: print(msg)
            print("-------------------------")
        elif failed_count > 0:
            QMessageBox.critical(self, "Failure", f"Failed to save any of the {failed_count} character files.")
            detail_msg = "Processing Details:\n" + "\n".join(error_messages[:10])
            if len(error_messages) > 10: detail_msg += "\n..."
            QMessageBox.information(self, "Processing Details", detail_msg)
            print("\n--- Processing Errors ---")
            for msg in error_messages: print(msg)
            print("-------------------------")
        else:
            QMessageBox.information(self, "Info", "No characters were processed or saved.")


# --- 1. Main Tools: Character Converter (Single JSON) --- (Original #2)
class Tool_CharacterSingle(QWidget):
    def __init__(self, stacked_widget=None):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.inputJson = None
        self._input_filename = None
        self.saveButton = None
        self.loadedFileLabel = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        backButton = QPushButton("<- Back to Main Menu")
        backButton.clicked.connect(self._go_back)
        layout.addWidget(backButton)

        layout.addWidget(load_sox_image_label(), alignment=Qt.AlignCenter)
        textDesc = QLabel("Convert Xoul JSON to TavernAI Character Card")
        textDesc.setAlignment(Qt.AlignCenter)
        layout.addWidget(textDesc)
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))
        layout.addWidget(QLabel("VV Station XoulAI VV"), alignment=Qt.AlignCenter)
        loadButton = QPushButton("Import Xoul JSON")
        self.saveButton = QPushButton("Export TavernAI JSON")
        self.saveButton.setEnabled(False)
        self.loadedFileLabel = QLabel("No file loaded")
        self.loadedFileLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(loadButton)
        layout.addWidget(self.loadedFileLabel, alignment=Qt.AlignCenter)
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))
        layout.addWidget(QLabel("<i>-->> Next Station: TavernAI -->></i>"), alignment=Qt.AlignCenter)
        layout.addWidget(self.saveButton)
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        loadButton.clicked.connect(self.loadInputFile)
        self.saveButton.clicked.connect(self.transformJSONAndSave)
        self.setLayout(layout)

    def _go_back(self):
        self.inputJson = None
        self._input_filename = None
        if self.saveButton: self.saveButton.setEnabled(False)
        if self.loadedFileLabel: self.loadedFileLabel.setText("No file loaded")
        if self.stacked_widget: self.stacked_widget.setCurrentIndex(0)

    def _check_enable_save(self):
        # Corrected structure check for Single Character file
        if isinstance(self.inputJson, dict) and "name" in self.inputJson:
            self.saveButton.setEnabled(True)
            print("Input file loaded and basic character structure found. Save button enabled.")
        else:
            self.saveButton.setEnabled(False)
            print("Waiting for input file to be loaded or structure invalid for single character conversion.")

    def loadInputFile(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Input JSON", '.', 'JSON files (*.json)')
        if not filename:
            self.inputJson = None
            self._input_filename = None # FIX: Added self.
            self.loadedFileLabel.setText("No file loaded")
            self._check_enable_save() # FIX: Added self.
            return

        loaded_data = safe_json_load(filename)
        if loaded_data:
             # Corrected structure check for Single Character file
             if not isinstance(loaded_data, dict) or "name" not in loaded_data:
                  self.inputJson = None
                  self._input_filename = None # FIX: Added self.
                  self.loadedFileLabel.setText("Invalid file structure")
                  QMessageBox.critical(self, "Data Structure Error",
                                       f"The loaded file does not appear to be a valid Single Xoul Character JSON.\n"
                                       f"Missing expected 'name' key.")
                  print(f"Data structure error in {filename}: Missing expected 'name' key for single character.")
             else:
                  self.inputJson = loaded_data
                  self._input_filename = filename
                  self.loadedFileLabel.setText(f"Loaded: {os.path.basename(filename)}")
                  QMessageBox.information(self, "Success!", "JSON loaded successfully!")
        else:
             self.inputJson = None
             self._input_filename = None # FIX: Added self.
             self.loadedFileLabel.setText("Load failed")

        self._check_enable_save() # FIX: Added self.

    def transformJSONAndSave(self):
        # Corrected initial check for Single Character file
        if not isinstance(self.inputJson, dict) or "name" not in self.inputJson:
            QMessageBox.warning(self, "Warning", "No valid input JSON data loaded.")
            self._check_enable_save()
            return

        try:
            output_json = {
                "name": self.inputJson.get("name", ""), "description": self.inputJson.get("backstory", ""),
                "personality": self.inputJson.get("definition", ""), "scenario": self.inputJson.get("default_scenario", ""),
                "first_mes": self.inputJson.get("greeting", ""), "mes_example": self.inputJson.get("samples", ""),
                "creator_notes": self.inputJson.get("bio", ""), "system_prompt": "", "post_history_instructions": "",
                "tags": self.inputJson.get("social_tags", []), "creator": self.inputJson.get("slug", ""),
                "character_version": "imported", "alternate_greetings": [],
                "extensions": {
                    "talkativeness": str(self.inputJson.get("talkativeness", "0.5")), "fav": False, "world": "",
                    "depth_prompt": {"prompt": "", "depth": 4, "role": "system"}
                },
                "group_only_greetings": []
            }
            default_filename_base = self.inputJson.get("name") or self.inputJson.get("slug", "transformed_character")
            filename_base = re.sub(r'[^\w\-_\. ]', '_', default_filename_base).replace(' ', '_')
            if not filename_base: filename_base = "transformed_character"
            default_save_name = f"{filename_base}.json"
            filename, _ = QFileDialog.getSaveFileName(self, "Save Output JSON", default_save_name, 'JSON files (*.json)')
            if not filename:
                return

            if not filename.lower().endswith('.json'): filename += '.json'

            # Save using the helper function
            if safe_json_save(output_json, filename, indent=4):
                QMessageBox.information(self, "Success!", f"JSON transformed and saved successfully to:\n{filename}")

        except Exception as e:
             QMessageBox.critical(self, "Transformation Error", f"An unexpected error occurred during transformation or saving:\n{e}")
             print("General Error transforming/saving:", str(e))


# --- 2. Main Tools: Persona Adding (to TavernAI Backup) --- (Original #3)
class Tool_PersonaAdd(QWidget):
    def __init__(self, stacked_widget=None):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.input_data = None      # TavernAI backup data
        self._input_filename = None # Store filename for the TavernAI backup
        self.config_data = None     # Xoul Persona data
        self._config_filename = None # Store filename for the Xoul Persona JSON
        self.saveButton = None
        self.loadedFileLabelA = None
        self.loadedFileLabelB = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        backButton = QPushButton("<- Back to Main Menu")
        backButton.clicked.connect(self._go_back)
        layout.addWidget(backButton)

        layout.addWidget(load_sox_image_label(), alignment=Qt.AlignCenter)
        textDesc = QLabel("Add Xoul Persona to TavernAI Persona Backup File")
        textDesc.setAlignment(Qt.AlignCenter)
        layout.addWidget(textDesc)
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        loadButtonA = QPushButton("Import TavernAI Persona's Backup JSON")
        loadButtonB = QPushButton("Add Xoul Persona from JSON")
        self.saveButton = QPushButton("Export Modified Backup JSON")
        self.saveButton.setEnabled(False)
        self.loadedFileLabelA = QLabel("TavernAI Backup: No file loaded")
        self.loadedFileLabelA.setAlignment(Qt.AlignCenter)
        self.loadedFileLabelB = QLabel("Xoul Persona: No file loaded")
        self.loadedFileLabelB.setAlignment(Qt.AlignCenter)

        layout.addWidget(loadButtonA)
        layout.addWidget(self.loadedFileLabelA, alignment=Qt.AlignCenter)
        layout.addItem(QSpacerItem(20, 15, QSizePolicy.Minimum, QSizePolicy.Fixed))

        layout.addWidget(loadButtonB)
        layout.addWidget(self.loadedFileLabelB, alignment=Qt.AlignCenter)
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        layout.addWidget(QLabel("<i>-->> Next Station: TavernAI -->></i>"), alignment=Qt.AlignCenter)
        layout.addWidget(self.saveButton)
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        loadButtonA.clicked.connect(self.loadInputFile)
        loadButtonB.clicked.connect(self.loadDataFile)
        self.saveButton.clicked.connect(self.transformJSONAndSave)

        self.setLayout(layout)

    def _go_back(self):
        self.input_data = None
        self._input_filename = None
        self.config_data = None
        self._config_filename = None
        if self.saveButton: self.saveButton.setEnabled(False)
        if self.loadedFileLabelA: self.loadedFileLabelA.setText("TavernAI Backup: No file loaded")
        if self.loadedFileLabelB: self.loadedFileLabelB.setText("Xoul Persona: No file loaded")
        if self.stacked_widget: self.stacked_widget.setCurrentIndex(0)

    def _check_enable_save(self):
        """Checks if both necessary files are loaded and enables/disables save button."""
        input_ok = isinstance(self.input_data, dict) and 'personas' in self.input_data and 'persona_descriptions' in self.input_data
        config_ok = isinstance(self.config_data, dict) and 'name' in self.config_data and 'prompt' in self.config_data

        if input_ok and config_ok:
            self.saveButton.setEnabled(True)
            print("Both required files loaded and look correct. Save button enabled.")
        else:
            self.saveButton.setEnabled(False)
            print("Waiting for both required files to be loaded correctly.")


    def loadInputFile(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load TavernAI Persona's Backup JSON", '.', 'JSON files (*.json)')
        if not filename:
            self.input_data = None
            self._input_filename = None # FIX: Added self.
            self.loadedFileLabelA.setText("TavernAI Backup: No file loaded")
            self._check_enable_save() # FIX: Added self.
            return

        loaded_data = safe_json_load(filename)
        if loaded_data:
            if not isinstance(loaded_data, dict) or 'personas' not in loaded_data or 'persona_descriptions' not in loaded_data:
                 self.input_data = None
                 self._input_filename = None # FIX: Added self.
                 self.loadedFileLabelA.setText("TavernAI Backup: Invalid structure")
                 QMessageBox.critical(self, "Data Structure Error",
                                      f"The loaded file does not appear to be a valid TavernAI Persona backup.\n"
                                      f"Missing 'personas' or 'persona_descriptions' keys.") # Corrected f-string typo
                 print(f"Data structure error in {filename}: Missing expected keys for TavernAI backup")
            else:
                self.input_data = loaded_data
                self._input_filename = filename
                self.loadedFileLabelA.setText(f"TavernAI Backup: {os.path.basename(filename)}")
                QMessageBox.information(self, "Success!", "TavernAI Backup loaded successfully!")
        else:
            self.input_data = None
            self._input_filename = None # FIX: Added self.
            self.loadedFileLabelA.setText("TavernAI Backup: Load failed")

        self._check_enable_save() # FIX: Added self.


    def loadDataFile(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Add Xoul Persona from JSON", '.', 'JSON files (*.json)')
        if not filename:
            self.config_data = None
            self._config_filename = None # FIX: Added self.
            self.loadedFileLabelB.setText("Xoul Persona: No file loaded")
            self._check_enable_save() # FIX: Added self.
            return

        loaded_data = safe_json_load(filename)
        if loaded_data:
            if not isinstance(loaded_data, dict) or 'name' not in loaded_data or 'prompt' not in loaded_data:
                self.config_data = None
                self._config_filename = None # FIX: Added self.
                self.loadedFileLabelB.setText("Xoul Persona: Invalid structure")
                QMessageBox.critical(self, "Data Structure Error",
                                     f"The loaded file does not appear to be a valid Xoul Persona JSON.\n"
                                                                    f"Missing 'name' or 'prompt' keys.") # Corrected f-string typo
                print(f"Data structure error in {filename}: Missing expected keys for Xoul Persona")
            else:
                self.config_data = loaded_data
                self._config_filename = filename
                self.loadedFileLabelB.setText(f"Xoul Persona: {os.path.basename(filename)}")
                QMessageBox.information(self, "Success!", "Xoul Persona loaded successfully!")

        else:
            self.config_data = None
            self._config_filename = None # FIX: Added self.
            self.loadedFileLabelB.setText("Xoul Persona: Load failed")

        self._check_enable_save() # FIX: Added self.


    def transformJSONAndSave(self):
        input_ok = isinstance(self.input_data, dict) and 'personas' in self.input_data and 'persona_descriptions' in self.input_data
        config_ok = isinstance(self.config_data, dict) and 'name' in self.config_data and 'prompt' in self.config_data
        if not (input_ok and config_ok):
            QMessageBox.warning(self, "Warning", "Please load both valid JSON files first.")
            self._check_enable_save() # FIX: Added self.
            return

        try:
            new_persona_name = self.config_data.get('name')
            new_description = self.config_data.get('prompt')

            if not isinstance(new_persona_name, str) or not new_persona_name or not isinstance(new_description, str):
                 QMessageBox.warning(self, "Warning", "Xoul Persona JSON must contain 'name' and 'prompt' string keys with values.")
                 print("Xoul Persona JSON missing 'name' or 'prompt' or they are not non-empty strings.")
                 return

            output_data = self.input_data.copy()

            if 'personas' not in output_data or not isinstance(output_data['personas'], dict):
                 print("Warning: 'personas' key not found or not a dictionary in backup. Creating/replacing.")
                 output_data['personas'] = {}

            filename_base = re.sub(r'[^\w\-_\. ]', '_', new_persona_name)
            filename_base = filename_base.replace(' ', '_')
            if not filename_base or filename_base.startswith('.'):
                 hash_object = hashlib.md5(new_persona_name.encode()).hexdigest()
                 filename_base = f"persona_{hash_object[:8]}"

            persona_dict_key = f"{filename_base}.png"

            output_data['personas'][persona_dict_key] = new_persona_name

            if 'persona_descriptions' not in output_data or not isinstance(output_data['persona_descriptions'], dict):
                 print("Warning: 'persona_descriptions' key not found or not a dictionary in backup. Creating/replacing.")
                 output_data['persona_descriptions'] = {}

            new_description_entry = {"description": new_description, "position": 0}
            output_data['persona_descriptions'][persona_dict_key] = new_description_entry

            default_save_name = "modified_persona_backup.json"
            if self._input_filename:
                 base, ext = os.path.splitext(os.path.basename(self._input_filename))
                 default_save_name = f"{base}_modified.json"

            filename, _ = QFileDialog.getSaveFileName(self, "Save Modified Backup JSON", default_save_name, "JSON files (*.json)")
            if not filename:
                return

            if not filename.lower().endswith('.json'): filename += '.json'

            if safe_json_save(output_data, filename, indent=4):
                QMessageBox.information(self, "Success!", f"Persona added and modified backup saved successfully to:\n{filename}")

        except Exception as e:
             QMessageBox.critical(self, "Transformation Error", f"An unexpected error occurred during transformation or saving:\n{e}")
             print("General Error transforming/saving:", str(e))


# --- 4. Main Tools: Scenario Converter (Single JSON) --- (Original #4)
class Tool_ScenarioConvert(QWidget):
    def __init__(self, stacked_widget=None):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.inputJson = None
        self._input_filename = None
        self.saveButton = None
        self.loadedFileLabel = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        backButton = QPushButton("<- Back to Main Menu")
        backButton.clicked.connect(self._go_back)

        layout.addWidget(backButton)
        layout.addWidget(load_sox_image_label(), alignment=Qt.AlignCenter) # <-- ADDED IMAGE HEADER
        textDesc = QLabel("Convert a Xoul Scenario JSON to TavernAI World Single Entry")
        textDesc.setAlignment(Qt.AlignCenter)
        layout.addWidget(textDesc)
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        layout.addWidget(QLabel("VV Station XoulAI VV"), alignment=Qt.AlignCenter)
        loadButton = QPushButton("Import Xoul Scenario JSON")
        self.saveButton = QPushButton("Export TavernAI World JSON")
        self.saveButton.setEnabled(False)
        self.loadedFileLabel = QLabel("No file loaded")
        self.loadedFileLabel.setAlignment(Qt.AlignCenter)

        layout.addWidget(loadButton)
        layout.addWidget(self.loadedFileLabel, alignment=Qt.AlignCenter)
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        layout.addWidget(QLabel("<i>-->> Next Station: TavernAI -->></i>"), alignment=Qt.AlignCenter)
        layout.addWidget(self.saveButton)
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        loadButton.clicked.connect(self.loadInputFile)
        self.saveButton.clicked.connect(self.transformJSONAndSave)

        self.setLayout(layout)

    def _go_back(self):
        self.inputJson = None
        self._input_filename = None
        if self.saveButton: self.saveButton.setEnabled(False)
        if self.loadedFileLabel: self.loadedFileLabel.setText("No file loaded")
        if self.stacked_widget: self.stacked_widget.setCurrentIndex(0)

    def _check_enable_save(self):
        if isinstance(self.inputJson, dict) and ("name" in self.inputJson or "prompt" in self.inputJson):
            self.saveButton.setEnabled(True)
            print("Input file loaded and basic scenario structure found. Save button enabled.")
        else:
            self.saveButton.setEnabled(False)
            print("Waiting for input file to be loaded or structure invalid for scenario conversion.")


    def loadInputFile(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Xoul Scenario JSON", '.', 'JSON files (*.json)')
        if not filename:
            self.inputJson = None
            self._input_filename = None # FIX: Added self.
            self.loadedFileLabel.setText("No file loaded")
            self._check_enable_save() # FIX: Added self.
            return

        loaded_data = safe_json_load(filename)
        if loaded_data:
            if not isinstance(loaded_data, dict) or ('name' not in loaded_data and 'prompt' not in loaded_data):
                  self.inputJson = None
                  self._input_filename = None # FIX: Added self.
                  self.loadedFileLabel.setText("Invalid file structure")
                  QMessageBox.critical(self, "Data Structure Error",
                                       f"The loaded file does not appear to be a valid Xoul Scenario JSON.\n"
                                                                     f"Missing expected 'name' or 'prompt' keys.") # Corrected f-string typo
                  print(f"Data structure error in {filename}: Missing expected keys or wrong types for scenario.")
            else:
                  self.inputJson = loaded_data
                  self._input_filename = filename
                  self.loadedFileLabel.setText(f"Loaded: {os.path.basename(filename)}")
                  QMessageBox.information(self, "Success!", "JSON loaded successfully!")

        else: # loaded_data is None
             self.inputJson = None
             self._input_filename = None # FIX: Added self.
             self.loadedFileLabel.setText("Load failed")

        self._check_enable_save() # FIX: Added self.


    def transformJSONAndSave(self):
        if not isinstance(self.inputJson, dict) or ('name' not in self.inputJson and 'prompt' not in self.inputJson):
            QMessageBox.warning(self, "Error", "No valid JSON data loaded! Please load a scenario JSON first.")
            self._check_enable_save() # FIX: Added self.
            return

        try:
            input_data = self.inputJson

            scenario_name = input_data.get("name", "")
            scenario_prompt = input_data.get("prompt", "")
            prompt_spec = input_data.get("prompt_spec", {})

            content_parts = [scenario_prompt]
            if isinstance(prompt_spec, dict) and prompt_spec:
                spec_lines = []
                familiarity = prompt_spec.get("familiarity")
                if isinstance(familiarity, str) and familiarity: spec_lines.append(f"{{{{char}}}} are: {familiarity}")
                location = prompt_spec.get("location")
                if isinstance(location, str) and location: spec_lines.append(f"location: {location}")

                if spec_lines:
                    if scenario_prompt.strip(): content_parts.append("\n\n" + "\n".join(spec_lines))
                    else: content_parts.append("\n".join(spec_lines))

            content = "".join(content_parts).strip()

            entry = {
                "uid": 0, "key": [], "keysecondary": [],
                "comment": scenario_name, "content": content,
                "constant": True, "vectorized": False, "selective": True,
                "selectiveLogic": 0, "addMemo": True, "order": 100,
                "position": 0, "disable": False, "excludeRecursion": False,
                "preventRecursion": False, "delayUntilRecursion": False,
                "probability": 100, "useProbability": True, "depth": 4,
                "group": "", "groupOverride": False, "groupWeight": 100,
                "scanDepth": None, "caseSensitive": None, "matchWholeWords": None,
                "useGroupScoring": None, "automationId": "", "role": None,
                "sticky": 0, "cooldown": 0, "delay": 0, "displayIndex": 0
            }

            output_json = {"entries": {"0": entry}}


            default_filename_base = scenario_name or "converted_scenario"
            filename_base = re.sub(r'[^\w\-_\. ]', '_', default_filename_base).replace(' ', '_')
            if not filename_base: filename_base = "converted_scenario"
            default_save_name = f"{filename_base}.json"

            filename, _ = QFileDialog.getSaveFileName(self, "Save Output JSON", default_save_name, 'JSON files (*.json)')
            if not filename: return

            if not filename.lower().endswith('.json'): filename += '.json'

            # Save using the helper function
            if safe_json_save(output_json, filename, indent=4):
                 QMessageBox.information(self, "Success!", f"JSON transformed and saved successfully to:\n{filename}")

        except Exception as e:
             QMessageBox.critical(self, "Transformation Error", f"An unexpected error occurred during transformation or saving:\n{e}")
             print("General Error transforming/saving:", str(e))


# --- 5. Main Tools: Lorebook Converter --- (Original #5)
class Tool_LorebookConvert(QWidget):
    def __init__(self, stacked_widget=None):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.inputJson = None
        self._input_filename = None
        self.saveButton = None
        self.loadedFileLabel = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        backButton = QPushButton("<- Back to Main Menu")
        backButton.clicked.connect(self._go_back)
        layout.addWidget(backButton)

        layout.addWidget(load_sox_image_label(), alignment=Qt.AlignCenter) # <-- ADDED IMAGE HEADER
        textDesc = QLabel("Convert Xoul Lorebook JSON to TavernAI World Entries")
        textDesc.setAlignment(Qt.AlignCenter)
        layout.addWidget(textDesc)
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        layout.addWidget(QLabel("VV Station XoulAI VV"), alignment=Qt.AlignCenter)
        loadButton = QPushButton("Import Xoul Lorebook JSON")
        self.saveButton = QPushButton("Export TavernAI World JSON")
        self.saveButton.setEnabled(False)
        self.loadedFileLabel = QLabel("No file loaded")
        self.loadedFileLabel.setAlignment(Qt.AlignCenter)

        layout.addWidget(loadButton)
        layout.addWidget(self.loadedFileLabel, alignment=Qt.AlignCenter)
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        layout.addWidget(QLabel("<i>-->> Next Station: TavernAI -->></i>"), alignment=Qt.AlignCenter)
        layout.addWidget(self.saveButton)
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        loadButton.clicked.connect(self.loadInputFile)
        self.saveButton.clicked.connect(self.transformJSONAndSave)

        self.setLayout(layout)

    def _go_back(self):
        self.inputJson = None
        self._input_filename = None
        if self.saveButton: self.saveButton.setEnabled(False)
        if self.loadedFileLabel: self.loadedFileLabel.setText("No file loaded")
        if self.stacked_widget:
            self.stacked_widget.setCurrentIndex(0)

    def _check_enable_save(self):
        if isinstance(self.inputJson, dict) and \
           "embedded" in self.inputJson and isinstance(self.inputJson.get("embedded"), dict) and \
           "sections" in self.inputJson["embedded"] and isinstance(self.inputJson["embedded"].get("sections"), list):

            self.saveButton.setEnabled(True)
            print("Input file loaded and expected lorebook structure found. Save button enabled.")
        else:
            self.saveButton.setEnabled(False)
            print("Waiting for input file to be loaded or structure invalid for lorebook conversion.")


    def loadInputFile(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Xoul Lorebook JSON", '.', 'JSON files (*.json)')
        if not filename:
            self.inputJson = None
            self._input_filename = None # FIX: Added self.
            self.loadedFileLabel.setText("No file loaded")
            self._check_enable_save() # FIX: Added self.
            return

        loaded_data = safe_json_load(filename)
        if loaded_data:
            if not isinstance(loaded_data, dict) or \
               "embedded" not in loaded_data or \
               not isinstance(loaded_data.get("embedded"), dict) or \
               "sections" not in loaded_data["embedded"] or \
               not isinstance(loaded_data["embedded"].get("sections"), list):

                self.inputJson = None
                self._input_filename = None # FIX: Added self.
                self.loadedFileLabel.setText("Invalid file structure")
                QMessageBox.critical(self, "Data Structure Error",
                                     f"The loaded file does not appear to be a valid Xoul Lorebook JSON.\n"
                                                                   f"Missing expected structure (e.g., 'embedded.sections').") # Corrected f-string typo
                print(f"Data structure error in {filename}: Missing expected keys or wrong types for lorebook.")
            else:
                self.inputJson = loaded_data
                self._input_filename = filename
                self.loadedFileLabel.setText(f"Loaded: {os.path.basename(filename)}")
                QMessageBox.information(self, "Success!", "JSON loaded successfully!")

        else: # loaded_data is None
             self.inputJson = None
             self._input_filename = None # FIX: Added self.
             self.loadedFileLabel.setText("Load failed")

        self._check_enable_save() # FIX: Added self.


    def transformJSONAndSave(self):
        if not isinstance(self.inputJson, dict) or \
           "embedded" not in self.inputJson or \
           not isinstance(self.inputJson.get("embedded"), dict) or \
           "sections" not in self.inputJson["embedded"] or \
           not isinstance(self.inputJson["embedded"].get("sections"), list):
            QMessageBox.warning(self, "Error", "No valid Lorebook JSON data loaded or structure is invalid!")
            self._check_enable_save() # FIX: Added self.
            return

        try:
            input_data = self.inputJson
            sections_list = input_data.get("embedded", {}).get("sections", [])

            if not sections_list:
                 QMessageBox.information(self, "Info", "No 'sections' found in the loaded Lorebook JSON to convert.")
                 return

            entries_dict = {}
            failed_count = 0
            error_messages = []

            for i, section in enumerate(sections_list):
                if not isinstance(section, dict):
                    failed_count += 1
                    error_messages.append(f"Skipping item at index {i}: Data is not a dictionary.")
                    print(f"Error processing item at index {i}: Expected dictionary, got {type(section)}")
                    continue
                try:
                    entry = {
                        "uid": i, "key": section.get("keywords", []), "keysecondary": [],
                        "comment": section.get("name", ""), "content": section.get("text", ""),
                        "constant": False, "vectorized": False, "selective": True,
                        "selectiveLogic": 0, "addMemo": True, "order": 100,
                        "position": 0, "disable": False, "excludeRecursion": False,
                        "preventRecursion": False, "delayUntilRecursion": False,
                        "probability": 100, "useProbability": True, "depth": 4,
                        "group": "", "groupOverride": False, "groupWeight": 100,
                        "scanDepth": None, "caseSensitive": None, "matchWholeWords": None,
                        "useGroupScoring": None, "automationId": "", "role": None,
                        "sticky": 0, "cooldown": 0, "delay": 0, "displayIndex": i
                    }
                    entries_dict[str(i)] = entry
                except Exception as e:
                     failed_count += 1
                     section_identifier = section.get("name", f"index_{i}")
                     error_messages.append(f"Failed to process section '{section_identifier}': {e}")
                     print(f"Error processing section {section_identifier}: {e}")
                     continue

            # output_json was missing. It should be the `entries_dict` wrapped in an "entries" key.
            output_json = {"entries": entries_dict} # FIX: Defined output_json here

            saved_count = len(entries_dict)
            if saved_count == 0 and len(sections_list) > 0: # Check if there were sections but none saved
                 QMessageBox.information(self, "Info", f"No valid sections were successfully processed from the Lorebook JSON.")
                 return
            elif saved_count == 0 and len(sections_list) == 0: # Check if input list was empty
                 QMessageBox.information(self, "Info", "No 'sections' found in the loaded Lorebook JSON to convert.")
                 return


            default_save_name = "converted_lorebook.json"
            if self._input_filename:
                 base, ext = os.path.splitext(os.path.basename(self._input_filename))
                 default_save_name = f"{base}_world.json"

            filename, _ = QFileDialog.getSaveFileName(self, "Save Output JSON", default_save_name, 'JSON files (*.json)')
            if not filename: return
            if not filename.lower().endswith('.json'): filename += '.json'

            # Save using the helper function
            if safe_json_save(output_json, filename, indent=4):
                 if failed_count == 0:
                      QMessageBox.information(self, "Success!", f"Successfully transformed and saved {saved_count} lorebook entries to\n{filename}")
                 else:
                      QMessageBox.warning(self, "Partial Success", f"Successfully transformed and saved {saved_count} lorebook entries.\nFailed to process {failed_count} entries (see console for details).")
                      detail_msg = "Processing Details:\n" + "\n".join(error_messages[:10])
                      if len(error_messages) > 10: detail_msg += "\n..."
                      QMessageBox.information(self, "Processing Details", detail_msg)
                      print("\n--- Processing Errors ---")
                      for msg in error_messages: print(msg)
                      print("-------------------------")
            # If save failed, safe_json_save already showed a message

        except Exception as e:
             QMessageBox.critical(self, "Transformation Error", f"An unexpected error occurred during transformation or saving:\n{e}")
             print("General Error transforming/saving:", str(e))

# --- 5. Chat Tools: Single Chat Converter (to JSON Lines) --- (Original #6)
class Tool_ChatSingle(QWidget):
    def __init__(self, stacked_widget=None):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.inputJson = None
        self._input_filename = None
        self.saveButton = None
        self.loadedFileLabel = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        backButton = QPushButton("<- Back to Main Menu")
        backButton.clicked.connect(self._go_back)
        layout.addWidget(backButton)

        layout.addWidget(load_sox_image_label(), alignment=Qt.AlignCenter) # <-- ADDED IMAGE HEADER
        textDesc = QLabel("Convert Single Xoul Chat JSON to TavernAI Character Chat JSON Lines")
        textDesc.setAlignment(Qt.AlignCenter)
        layout.addWidget(textDesc)
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        layout.addWidget(QLabel("VV Station XoulAI VV"), alignment=Qt.AlignCenter)
        loadButton = QPushButton("Import Xoul Chat JSON")
        self.saveButton = QPushButton("Export TavernAI Chat JSON")
        self.saveButton.setEnabled(False)
        self.loadedFileLabel = QLabel("No file loaded")
        self.loadedFileLabel.setAlignment(Qt.AlignCenter)

        layout.addWidget(loadButton)
        layout.addWidget(self.loadedFileLabel, alignment=Qt.AlignCenter)
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        layout.addWidget(QLabel("<i>-->> Next Station: TavernAI -->></i>"), alignment=Qt.AlignCenter)
        layout.addWidget(self.saveButton)
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        loadButton.clicked.connect(self.loadInputFile)
        self.saveButton.clicked.connect(self.transformJSONAndSave)

        self.setLayout(layout)

    def _go_back(self):
        self.inputJson = None
        self._input_filename = None
        if self.saveButton: self.saveButton.setEnabled(False)
        if self.loadedFileLabel: self.loadedFileLabel.setText("No file loaded")
        if self.stacked_widget: self.stacked_widget.setCurrentIndex(0)

    def _check_enable_save(self):
        # Corrected structure check for Single Chat file
        if isinstance(self.inputJson, dict) and \
           "messages" in self.inputJson and isinstance(self.inputJson.get("messages"), list) and \
           "conversation" in self.inputJson and isinstance(self.inputJson.get("conversation"), dict) and \
           "personas" in self.inputJson.get("conversation", {}) and isinstance(self.inputJson["conversation"].get("personas"), list) and \
           "xouls" in self.inputJson.get("conversation", {}) and isinstance(self.inputJson["conversation"].get("xouls"), list):
            self.saveButton.setEnabled(True)
            print("Input file loaded and expected single chat structure found. Save button enabled.")
        else:
            self.saveButton.setEnabled(False)
            print("Waiting for input file to be loaded or structure invalid for single chat conversion.")

    def loadInputFile(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Xoul Chat JSON", '.', 'JSON files (*.json)')
        if not filename:
            self.inputJson = None
            self._input_filename = None # FIX: Added self.
            self.loadedFileLabel.setText("No file loaded")
            self._check_enable_save() # FIX: Added self.
            return

        loaded_data = safe_json_load(filename)
        if loaded_data:
            # Corrected structure check for Single Chat file
            if not (isinstance(loaded_data, dict) and \
               "messages" in loaded_data and isinstance(loaded_data.get("messages"), list) and \
               "conversation" in loaded_data and isinstance(loaded_data.get("conversation"), dict) and \
               "personas" in loaded_data.get("conversation", {}) and isinstance(loaded_data["conversation"].get("personas"), list) and \
               "xouls" in loaded_data.get("conversation", {}) and isinstance(loaded_data["conversation"].get("xouls"), list)):

                self.inputJson = None
                self._input_filename = None # FIX: Added self.
                self.loadedFileLabel.setText("Invalid file structure")
                QMessageBox.critical(self, "Data Structure Error",
                                     f"The loaded file does not appear to be a valid Single Xoul Chat JSON.\n"
                                     f"Missing expected structure (Expected top-level 'messages' list, and 'personas'/'xouls' lists inside a top-level 'conversation' dict).") # Updated message
                print(f"Data structure error in {filename}: Missing expected keys or wrong types for single chat.")
            else:
                self.inputJson = loaded_data
                self._input_filename = filename
                self.loadedFileLabel.setText(f"Loaded: {os.path.basename(filename)}")
                QMessageBox.information(self, "Success!", "JSON loaded successfully!")
        else:
            self.inputJson = None
            self._input_filename = None # FIX: Added self.
            self.loadedFileLabel.setText("Load failed")

        self._check_enable_save() # FIX: Added self.

    def transformJSONAndSave(self):
        # Corrected initial check for Single Chat file
        if not (isinstance(self.inputJson, dict) and \
           "messages" in self.inputJson and isinstance(self.inputJson.get("messages"), list) and \
           "conversation" in self.inputJson and isinstance(self.inputJson.get("conversation"), dict) and \
           "personas" in self.inputJson.get("conversation", {}) and isinstance(self.inputJson["conversation"].get("personas"), list) and \
           "xouls" in self.inputJson.get("conversation", {}) and isinstance(self.inputJson["conversation"].get("xouls"), list)):
            QMessageBox.warning(self, "Error", "No valid Chat JSON data loaded or structure is invalid!")
            self._check_enable_save() # FIX: Added self.
            return

        try:
            conversation_data = self.inputJson.get('conversation', {})
            personas_list = conversation_data.get('personas', [])
            xouls_list = conversation_data.get('xouls', [])
            messages_list = self.inputJson.get('messages', []) # Access messages from top level inputJson

            if not isinstance(personas_list, list) or len(personas_list) == 0:
                 QMessageBox.warning(self, "Data Warning", "No 'personas' list found or it's empty in the chat JSON.")
                 # Decide if you want to continue without a persona (defaults to "User")
                 # For now, we'll let it continue as it will default username later
                 print("Warning: No 'personas' list found or it's empty in the chat JSON.")
                 # return # Don't return here
            if not isinstance(xouls_list, list) or len(xouls_list) == 0:
                 QMessageBox.warning(self, "Data Warning", "No 'xouls' list found or it's empty in the chat JSON.")
                 # Decide if you want to continue without a xoul (defaults to "Character")
                 # For now, we'll let it continue as it will default charactername later
                 print("Warning: No 'xouls' list found or it's empty in the chat JSON.")
                 # return # Don't return here

            if not isinstance(messages_list, list) or len(messages_list) == 0:
                 QMessageBox.information(self, "Info", "No 'messages' found in the chat JSON to convert.")
                 return

            first_persona = personas_list[0] if len(personas_list) > 0 and isinstance(personas_list[0], dict) else {} # Check list length
            first_xoul = xouls_list[0] if len(xouls_list) > 0 and isinstance(xouls_list[0], dict) else {} # Check list length

            username = first_persona.get('name', 'User')
            character_name = first_xoul.get('name', 'Character')

            output_messages = []
            failed_message_count = 0

            for i, message in enumerate(messages_list):
                 if not isinstance(message, dict):
                     failed_message_count += 1
                     print(f"Skipping message at index {i}: Item is not a dictionary.")
                     continue
                 try:
                     role = message.get('role')
                     content = message.get('content', '')
                     raw_timestamp = message.get('timestamp') # Get the raw timestamp string

                     sender_name = None
                     is_user = False
                     is_system = False

                     if role == 'user':
                         sender_name = username
                         is_user = True
                     elif role == 'assistant':
                         sender_name = character_name
                         is_user = False
                     elif role == 'system':
                         sender_name = 'System'
                         is_system = True
                         is_user = False
                     else:
                         # Message roles might differ, or unexpected values
                         print(f"Warning: Unexpected role '{role}' for message at index {i}.")
                         # Attempt to infer sender if role is missing/unknown based on name?
                         # Or just skip? Skipping for now to match previous logic.
                         failed_message_count += 1
                         continue # Skip message with unhandled role

                     # --- Timestamp Conversion ---
                     formatted_timestamp = "" # Default if conversion fails
                     if isinstance(raw_timestamp, (int, float)): # Handle numeric timestamps if they occur
                         try:
                              # Assuming integer/float timestamps are Unix timestamps (seconds since epoch)
                              dt_object = datetime.fromtimestamp(raw_timestamp)
                              formatted_timestamp = dt_object.strftime("%B %d, %Y %I:%M%p").replace('AM', 'am').replace('PM', 'pm')
                         except Exception as e:
                              print(f"Warning: Failed to parse numeric timestamp '{raw_timestamp}' for message at index {i}: {e}")
                     elif isinstance(raw_timestamp, str) and raw_timestamp: # Handle string timestamps
                         try:
                             # Handle potential 'Z' timezone indicator by replacing with +00:00
                             # This is generally safer for fromisoformat
                             if raw_timestamp.endswith('Z'):
                                 iso_timestamp_str = raw_timestamp[:-1] + '+00:00'
                             else:
                                 iso_timestamp_str = raw_timestamp

                             # Handle timestamps without microseconds but ending with +HH:MM or -HH:MM
                             if '.' not in iso_timestamp_str and ('+' in iso_timestamp_str or '-' in iso_timestamp_str):
                                 # Append .000000 to make it compatible with fromisoformat if it lacks micros but has timezone offset
                                 parts = re.split(r'([+-]\d{2}:\d{2})', iso_timestamp_str)
                                 if len(parts) == 3: # Should be [datetime_part, timezone_offset, '']
                                     iso_timestamp_str = parts[0] + '.000000' + parts[1]
                                 # If no timezone offset, just lacks micros, add .000000
                                 elif '+' not in iso_timestamp_str and '-' not in iso_timestamp_str:
                                      iso_timestamp_str += '.000000'


                             dt_object = datetime.fromisoformat(iso_timestamp_str)
                             # Format to "Month Day, Year Hour:MinuteAM/PM"
                             formatted_timestamp = dt_object.strftime("%B %d, %Y %I:%M%p").replace('AM', 'am').replace('PM', 'pm') # lowercase am/pm
                         except ValueError as e:
                             print(f"Warning: Failed to parse string timestamp '{raw_timestamp}' (processed as '{iso_timestamp_str}') for message at index {i}: {e}")
                             # Keep formatted_timestamp as "" or use raw_timestamp? Using "" as per format requirement.
                         except Exception as e:
                             print(f"Warning: Unexpected error parsing timestamp '{raw_timestamp}' (processed as '{iso_timestamp_str}') for message at index {i}: {e}")
                             # Keep formatted_timestamp as ""
                     # Else: raw_timestamp is None or empty string, formatted_timestamp remains ""


                     # TavernAI jsonl message object structure
                     output_message = {
                         "name": sender_name,
                         "is_user": is_user,
                         "is_system": is_system,
                         "send_date": formatted_timestamp, # Use the formatted timestamp
                         "mes": content
                         # Note: force_avatar is not typically in *single* character chat jsonl
                     }
                     output_messages.append(output_message)

                 except Exception as e:
                     failed_message_count += 1
                     print(f"Error processing message at index {i}: {e}")
                     continue

            successfully_converted_count = len(output_messages)
            if successfully_converted_count == 0 and len(messages_list) > 0:
                 QMessageBox.warning(self, "Conversion Failed", "No messages were successfully processed from the chat JSON.")
                 print("\n--- No messages converted ---")
                 return
            elif successfully_converted_count == 0 and len(messages_list) == 0:
                 QMessageBox.information(self, "Info", "No 'messages' found in the chat JSON to convert.")
                 return

            default_save_name = "converted_chat.jsonl"
            if self._input_filename:
                 base, ext = os.path.splitext(os.path.basename(self._input_filename))
                 default_save_name = f"{base}.jsonl"

            filename, selected_filter = QFileDialog.getSaveFileName(self, "Save Output JSON Lines", default_save_name, 'JSON Lines files (*.jsonl);;All files (*)') # Capture selected filter
            if not filename: return

            # Ensure .jsonl extension if the filter was JSON Lines and no extension was provided
            # Check both selected_filter and if the saved filename has an extension
            if (selected_filter and 'JSON Lines files' in selected_filter and not filename.lower().endswith('.jsonl')) or \
               (not selected_filter and not os.path.splitext(filename)[1]): # If 'All files' is selected, check if user typed an extension
                 filename += '.jsonl'


            # Save using the helper function (jsonl)
            if safe_json_save(output_messages, filename, is_jsonl=True):
                 if failed_message_count == 0:
                     QMessageBox.information(self, "Success!", f"Successfully converted and saved {successfully_converted_count} messages to\n{filename}")
                 else:
                     QMessageBox.warning(self, "Partial Success", f"Successfully converted and saved {successfully_converted_count} messages.\nFailed to process {failed_message_count} messages (see console for details).")

        except Exception as e:
             QMessageBox.critical(self, "General Error", f"An unexpected error occurred during chat transformation setup:\n{e}")
             print("General Error transforming:", str(e))

# --- 7. Chat Tools: Multi-Chat Converter (to JSON Lines) --- (Original #7)
class Tool_ChatMulti(QWidget):
    def __init__(self, stacked_widget=None):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.inputJson = None
        self._input_filename = None
        self.saveButton = None
        self.loadedFileLabel = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        backButton = QPushButton("<- Back to Main Menu")
        backButton.clicked.connect(self._go_back)
        layout.addWidget(backButton)

        layout.addWidget(load_sox_image_label(), alignment=Qt.AlignCenter) # <-- ADDED IMAGE HEADER
        textDesc = QLabel("Convert MULTI Xoul Chats JSON to TavernAI Group Chat JSON Lines")
        textDesc.setAlignment(Qt.AlignCenter)
        layout.addWidget(textDesc)
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        loadButton = QPushButton("Import Xoul Chat JSON")
        self.saveButton = QPushButton("Export TavernAI Chat JSON")
        self.saveButton.setEnabled(False)
        self.loadedFileLabel = QLabel("No file loaded")
        self.loadedFileLabel.setAlignment(Qt.AlignCenter)

        layout.addWidget(loadButton)
        layout.addWidget(self.loadedFileLabel, alignment=Qt.AlignCenter)
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        layout.addWidget(QLabel("<i>-->> Next Station: TavernAI -->></i>"), alignment=Qt.AlignCenter)
        layout.addWidget(self.saveButton)
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        loadButton.clicked.connect(self.loadInputFile)
        self.saveButton.clicked.connect(self.transformJSONAndSave)

        self.setLayout(layout)

    def _go_back(self):
        self.inputJson = None
        self._input_filename = None
        if self.saveButton: self.saveButton.setEnabled(False)
        if self.loadedFileLabel: self.loadedFileLabel.setText("No file loaded")
        if self.stacked_widget:
            self.stacked_widget.setCurrentIndex(0)


    def _check_enable_save(self):
        # Multi-chat JSON seems to have messages at the top level, not under "conversation"
        # Add checks for conversation, personas, xouls as they are needed for avatars
        if isinstance(self.inputJson, dict) and \
           "messages" in self.inputJson and isinstance(self.inputJson.get("messages"), list) and \
           "conversation" in self.inputJson and isinstance(self.inputJson.get("conversation"), dict) and \
           "personas" in self.inputJson.get("conversation", {}) and isinstance(self.inputJson["conversation"].get("personas"), list) and \
           "xouls" in self.inputJson.get("conversation", {}) and isinstance(self.inputJson["conversation"].get("xouls"), list):
            self.saveButton.setEnabled(True)
            print("Input file loaded and expected multi-chat structure found. Save button enabled.")
        else:
            self.saveButton.setEnabled(False)
            print("Waiting for input file to be loaded or structure invalid for multi-chat conversion.")


    def loadInputFile(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Xoul Chat JSON", '.', 'JSON files (*.json)')
        if not filename:
            self.inputJson = None
            self._input_filename = None # FIX: Added self.
            self.loadedFileLabel.setText("No file loaded")
            self._check_enable_save() # FIX: Added self.
            return

        loaded_data = safe_json_load(filename)

        if loaded_data:
             # Corrected structure check for Multi-chat file
            if not (isinstance(loaded_data, dict) and \
               "messages" in loaded_data and isinstance(loaded_data.get("messages"), list) and \
               "conversation" in loaded_data and isinstance(loaded_data.get("conversation"), dict) and \
               "personas" in loaded_data.get("conversation", {}) and isinstance(loaded_data["conversation"].get("personas"), list) and \
               "xouls" in loaded_data.get("conversation", {}) and isinstance(loaded_data["conversation"].get("xouls"), list)):

                self.inputJson = None
                self._input_filename = None # FIX: Added self.
                self.loadedFileLabel.setText("Invalid file structure")
                QMessageBox.critical(self, "Data Structure Error",
                                     f"The loaded file does not appear to be a valid Xoul Multi-Chat JSON.\n"
                                     f"Missing expected structure (Expected top-level 'messages' list, and 'personas'/'xouls' lists inside a top-level 'conversation' dict).") # Updated message
                print(f"Data structure error in {filename}: Missing expected keys or wrong types for multi-chat.")
            else:
                self.inputJson = loaded_data
                self._input_filename = filename
                self.loadedFileLabel.setText(f"Loaded: {os.path.basename(filename)}")
                QMessageBox.information(self, "Success!", "JSON loaded successfully!")

        else: # loaded_data is None
            self.inputJson = None
            self._input_filename = None # FIX: Added self.
            self.loadedFileLabel.setText("Load failed")

        self._check_enable_save() # FIX: Added self.


    def transformJSONAndSave(self):
         # Corrected initial check for Multi-chat file
        if not (isinstance(self.inputJson, dict) and \
           "messages" in self.inputJson and isinstance(self.inputJson.get("messages"), list) and \
           "conversation" in self.inputJson and isinstance(self.inputJson.get("conversation"), dict) and \
           "personas" in self.inputJson.get("conversation", {}) and isinstance(self.inputJson["conversation"].get("personas"), list) and \
           "xouls" in self.inputJson.get("conversation", {}) and isinstance(self.inputJson["conversation"].get("xouls"), list)):
            QMessageBox.warning(self, "Error", "No valid Chat JSON data loaded or structure is invalid!")
            self._check_enable_save() # FIX: Added self.
            return

        try:
            # Access conversation data, personas, and xouls from the 'conversation' object (top level)
            conversation_data = self.inputJson.get('conversation', {})
            all_personas = conversation_data.get('personas', [])
            all_xouls = conversation_data.get('xouls', [])
            # Access messages from the top level
            messages_list = self.inputJson.get('messages', [])

            if not isinstance(messages_list, list) or len(messages_list) == 0:
                 QMessageBox.information(self, "Info", "No 'messages' found in the chat JSON to convert.")
                 return

            # Add warnings if personas/xouls lists are empty, as avatars might not be resolved
            if not isinstance(all_personas, list) or len(all_personas) == 0:
                 print("Warning: No 'personas' list found or it's empty in the 'conversation' object. User avatars may not be displayed.")
            if not isinstance(all_xouls, list) or len(all_xouls) == 0:
                 print("Warning: No 'xouls' list found or it's empty in the 'conversation' object. LLM avatars may not be displayed.")


            output_messages = []
            failed_message_count = 0

            for i, message in enumerate(messages_list):
                 if not isinstance(message, dict):
                     failed_message_count += 1
                     print(f"Skipping message at index {i}: Item is not a dictionary.")
                     continue
                 try:
                     author_name = message.get('author_name')
                     author_type = message.get('author_type') # 'user' or 'llm'
                     raw_timestamp = message.get('timestamp') # Get the raw timestamp string
                     content = message.get('content')

                     # Check for essential fields
                     if not all([author_name, author_type]) or raw_timestamp is None or content is None: # raw_timestamp can be 0, check for None
                          print(f"Skipping message due to missing essential data (author_name, author_type, timestamp, or content): {message.get('message_id', f'index_{i}')}")
                          failed_message_count += 1
                          continue


                     output_name = author_name
                     is_user = (author_type == 'user')
                     is_system = (author_type == 'system') # Explicitly check for system type if it exists
                     if not is_user and not is_system: # Assume anything else is LLM/assistant
                         # Double-check if the message has a valid author_type we understand
                         if author_type not in ['user', 'llm', 'system']:
                             print(f"Warning: Unknown author_type '{author_type}' for message at index {i}. Treating as non-user/non-system.")
                         pass # Keep is_user=False, is_system=False

                     # --- Timestamp Conversion ---
                     formatted_timestamp = "" # Default if conversion fails
                     if isinstance(raw_timestamp, (int, float)): # Handle numeric timestamps if they occur
                         try:
                              # Assuming integer/float timestamps are Unix timestamps (seconds since epoch)
                              dt_object = datetime.fromtimestamp(raw_timestamp)
                              formatted_timestamp = dt_object.strftime("%B %d, %Y %I:%M%p").replace('AM', 'am').replace('PM', 'pm')
                         except Exception as e:
                              print(f"Warning: Failed to parse numeric timestamp '{raw_timestamp}' for message at index {i}: {e}")
                     elif isinstance(raw_timestamp, str) and raw_timestamp: # Handle string timestamps
                         try:
                             # Handle potential 'Z' timezone indicator by replacing with +00:00
                             # This is generally safer for fromisoformat
                             if raw_timestamp.endswith('Z'):
                                 iso_timestamp_str = raw_timestamp[:-1] + '+00:00'
                             else:
                                 iso_timestamp_str = raw_timestamp

                             # Handle timestamps without microseconds but ending with +HH:MM or -HH:MM
                             if '.' not in iso_timestamp_str and ('+' in iso_timestamp_str or '-' in iso_timestamp_str):
                                 # Append .000000 to make it compatible with fromisoformat if it lacks micros but has timezone offset
                                 parts = re.split(r'([+-]\d{2}:\d{2})', iso_timestamp_str)
                                 if len(parts) == 3: # Should be [datetime_part, timezone_offset, '']
                                     iso_timestamp_str = parts[0] + '.000000' + parts[1]
                                 # If no timezone offset, just lacks micros, add .000000
                                 elif '+' not in iso_timestamp_str and '-' not in iso_timestamp_str:
                                      iso_timestamp_str += '.000000'


                             dt_object = datetime.fromisoformat(iso_timestamp_str)
                             # Format to "Month Day, Year Hour:MinuteAM/PM"
                             formatted_timestamp = dt_object.strftime("%B %d, %Y %I:%M%p").replace('AM', 'am').replace('PM', 'pm') # lowercase am/pm
                         except ValueError as e:
                             print(f"Warning: Failed to parse string timestamp '{raw_timestamp}' (processed as '{iso_timestamp_str}') for message at index {i}: {e}")
                             # Keep formatted_timestamp as "" or use raw_timestamp? Using "" as per format requirement.
                         except Exception as e:
                             print(f"Warning: Unexpected error parsing timestamp '{raw_timestamp}' (processed as '{iso_timestamp_str}') for message at index {i}: {e}")
                             # Keep formatted_timestamp as ""
                     # Else: raw_timestamp is None or empty string, formatted_timestamp remains ""


                     # --- Find AVATAR URL based on author_name and author_type ---
                     avatar_url = None
                     if author_type == 'user':
                         found_entry = next((p for p in all_personas if isinstance(p, dict) and p.get('name') == author_name), None)
                         if found_entry: avatar_url = found_entry.get('icon_url')
                     elif author_type == 'llm':
                         found_entry = next((x for x in all_xouls if isinstance(x, dict) and x.get('name') == author_name), None)
                         if found_entry: avatar_url = found_entry.get('icon_url') # <-- FIX APPLIED HERE (was p)
                     # Note: System messages usually don't have avatars

                     output_message = {
                         "name": output_name, "is_user": is_user, "is_system": is_system,
                         "send_date": formatted_timestamp, # Use the formatted timestamp
                         "mes": content, "force_avatar": avatar_url
                     }
                     output_messages.append(output_message)

                 except Exception as e:
                     failed_message_count += 1
                     print(f"Error processing message at index {i}: {e}")
                     continue

            successfully_converted_count = len(output_messages)
            if successfully_converted_count == 0 and len(messages_list) > 0:
                 QMessageBox.warning(self, "Conversion Failed", "No messages were successfully processed from the chat JSON.")
                 print("\n--- No messages converted ---")
                 return
            elif successfully_converted_count == 0 and len(messages_list) == 0:
                 QMessageBox.information(self, "Info", "No 'messages' found in the chat JSON to convert.")
                 return


            default_save_name = "converted_group_chat.jsonl"
            try:
                 # Try to get conversation name from the 'conversation' object if it exists
                 conv_name = self.inputJson.get('conversation', {}).get('name', 'group_chat')
                 sanitized_name = re.sub(r'[^\w\-_\. ]', '_', conv_name).replace(' ', '_')
                 if sanitized_name: default_save_name = f"{sanitized_name}_converted.jsonl"
            except Exception as e:
                 print(f"Could not create default filename: {e}")
                 pass

            filename, selected_filter = QFileDialog.getSaveFileName(self, "Save Output JSON Lines", default_save_name, 'JSON Lines files (*.jsonl);;All files (*)') # Capture selected filter
            if not filename: return

            # Ensure .jsonl extension if the filter was JSON Lines and no extension was provided
            # Check both selected_filter and if the saved filename has an extension
            if (selected_filter and 'JSON Lines files' in selected_filter and not filename.lower().endswith('.jsonl')) or \
               (not selected_filter and not os.path.splitext(filename)[1]): # If 'All files' is selected, check if user typed an extension
                 filename += '.jsonl'


            if safe_json_save(output_messages, filename, is_jsonl=True):
                 if failed_message_count == 0:
                     QMessageBox.information(self, "Success!", f"Successfully converted and saved {successfully_converted_count} messages to\n{filename}")
                 else:
                     QMessageBox.warning(self, "Partial Success", f"Successfully converted and saved {successfully_converted_count} messages.\nFailed to process {failed_message_count} messages (see console for details).")

        except Exception as e:
             QMessageBox.critical(self, "General Error", f"An unexpected error occurred during chat transformation setup:\n{e}")
             print("General Error transforming:", str(e))


# --- 8. EXTRA Tools: Chat Scenario Extraction (from Chat Backup) --- (Original #8)
class Tool_ChatScenarioExtract(QWidget):
    def __init__(self, stacked_widget=None):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.inputJson = None
        self._input_filename = None
        self.saveButton = None
        self.loadedFileLabel = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        backButton = QPushButton("<- Back to Main Menu")
        backButton.clicked.connect(self._go_back)
        layout.addWidget(backButton)

        layout.addWidget(load_sox_image_label(), alignment=Qt.AlignCenter) # <-- ADDED IMAGE HEADER
        textDesc = QLabel("Extract Scenario from Chat Backup into TavernAI World Single Entry")
        textDesc.setAlignment(Qt.AlignCenter)
        layout.addWidget(textDesc)
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        loadButton = QPushButton("Import Xoul Chat JSON")
        self.saveButton = QPushButton("Export TavernAI World JSON")
        self.saveButton.setEnabled(False)
        self.loadedFileLabel = QLabel("No file loaded")
        self.loadedFileLabel.setAlignment(Qt.AlignCenter)

        layout.addWidget(loadButton)
        layout.addWidget(self.loadedFileLabel, alignment=Qt.AlignCenter)
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        layout.addWidget(QLabel("<i>-->> Next Station: TavernAI -->></i>"), alignment=Qt.AlignCenter)
        layout.addWidget(self.saveButton)
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        loadButton.clicked.connect(self.loadInputFile)
        self.saveButton.clicked.connect(self.transformJSONAndSave)

        self.setLayout(layout)

    def _go_back(self):
        self.inputJson = None
        self._input_filename = None
        if self.saveButton: self.saveButton.setEnabled(False)
        if self.loadedFileLabel: self.loadedFileLabel.setText("No file loaded")
        if self.stacked_widget:
            self.stacked_widget.setCurrentIndex(0)

    def _check_enable_save(self):
         # Relaxed the check slightly to allow extraction even if 'prompt' list is empty initially
         # Transformation will handle if prompt list is empty or contains non-strings
        if isinstance(self.inputJson, dict) and \
           "conversation" in self.inputJson and isinstance(self.inputJson.get("conversation"), dict) and \
           "scenario" in self.inputJson["conversation"] and isinstance(self.inputJson["conversation"].get("scenario"), dict) and \
           "prompt" in self.inputJson["conversation"]["scenario"] and isinstance(self.inputJson["conversation"]["scenario"].get("prompt"), list):
            self.saveButton.setEnabled(True)
            print("Input file loaded and expected chat scenario structure found. Save button enabled.")
        else:
            self.saveButton.setEnabled(False)
            print("Waiting for input file to be loaded or structure invalid for chat scenario extraction.")


    def loadInputFile(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Xoul Chat JSON", '.', 'JSON files (*.json)')
        if not filename:
            self.inputJson = None
            self._input_filename = None # FIX: Added self.
            self.loadedFileLabel.setText("No file loaded")
            self._check_enable_save() # FIX: Added self.
            return

        loaded_data = safe_json_load(filename)
        if loaded_data:
             # Relaxed the check slightly to allow extraction even if 'prompt' list is empty initially
             # Transformation will handle if prompt list is empty or contains non-strings
            if not (isinstance(loaded_data, dict) and \
               "conversation" in loaded_data and isinstance(loaded_data.get("conversation"), dict) and \
               "scenario" in loaded_data["conversation"] and isinstance(loaded_data["conversation"].get("scenario"), dict) and \
               "prompt" in loaded_data["conversation"]["scenario"] and isinstance(loaded_data["conversation"]["scenario"].get("prompt"), list)):

                self.inputJson = None
                self._input_filename = None # FIX: Added self.
                self.loadedFileLabel.setText("Invalid file structure")
                QMessageBox.critical(self, "Data Structure Error",
                                     f"The loaded file does not appear to be a valid Xoul Chat JSON for scenario extraction.\n"
                                                                   f"Missing expected structure (e.g., 'conversation.scenario.prompt').") # Corrected f-string typo
                print(f"Data structure error in {filename}: Missing expected keys or wrong types for scenario extraction.")
            else:
                self.inputJson = loaded_data
                self._input_filename = filename
                self.loadedFileLabel.setText(f"Loaded: {os.path.basename(filename)}")
                QMessageBox.information(self, "Success!", "JSON loaded successfully!")
        else:
             self.inputJson = None
             self._input_filename = None # FIX: Added self.
             self.loadedFileLabel.setText("Load failed")

        self._check_enable_save() # FIX: Added self.

    def transformJSONAndSave(self):
        # Relaxed the check slightly to allow transformation logic to handle edge cases
        if not isinstance(self.inputJson, dict) or \
           "conversation" not in self.inputJson or not isinstance(self.inputJson.get("conversation"), dict) or \
           "scenario" not in self.inputJson["conversation"] or not isinstance(self.inputJson["conversation"].get("scenario"), dict) or \
           "prompt" not in self.inputJson["conversation"]["scenario"] or not isinstance(self.inputJson["conversation"]["scenario"].get("prompt"), list):
            QMessageBox.warning(self, "Error", "No valid Chat JSON data loaded or structure is invalid for scenario extraction!")
            self._check_enable_save() # FIX: Added self.
            return

        try:
            conversation_data = self.inputJson.get("conversation", {})
            scenario_data = conversation_data.get("scenario", {})

            # Safely get the first item from the prompt list if it exists and is a string
            prompt_list = scenario_data.get("prompt", [])
            full_prompt_text = prompt_list[0] if len(prompt_list) > 0 and isinstance(prompt_list[0], str) else ""


            scenario_name_potential = scenario_data.get("name")
            conversation_name = conversation_data.get("name", "Unnamed Conversation")
            scenario_name_for_comment = scenario_name_potential if scenario_name_potential is not None else conversation_name

            familiarity = None
            location = None
            core_prompt_lines = []

            lines = full_prompt_text.splitlines()
            for line in lines:
                stripped_line = line.strip()
                if stripped_line.lower().startswith("familiarity:"):
                    familiarity = stripped_line[len("familiarity:"):].strip()
                elif stripped_line.lower().startswith("location:"):
                     location = stripped_line[len("location:"):].strip()
                else:
                    core_prompt_lines.append(line)

            scenario_prompt = "\n".join(core_prompt_lines)
            content_parts = [scenario_prompt]
            spec_lines = []

            if isinstance(familiarity, str) and familiarity: spec_lines.append(f"{{{{char}}}} are: {familiarity}")
            if isinstance(location, str) and location: spec_lines.append(f"location: {location}")

            if spec_lines:
                if scenario_prompt.strip(): content_parts.append("\n\n" + "\n".join(spec_lines))
                else: content_parts.append("\n".join(spec_lines))

            content = "".join(content_parts).strip()

            if not content:
                 QMessageBox.information(self, "Info", "No significant scenario content found to extract.")
                 return

            entry = {
                "uid": 0, "key": [], "keysecondary": [],
                "comment": scenario_name_for_comment, "content": content,
                "constant": True, "vectorized": False, "selective": True,
                "selectiveLogic": 0, "addMemo": True, "order": 100,
                "position": 0, "disable": False, "excludeRecursion": False,
                "preventRecursion": False, "delayUntilRecursion": False,
                "probability": 100, "useProbability": True, "depth": 4,
                "group": "", "groupOverride": False, "groupWeight": 100,
                "scanDepth": None, "caseSensitive": None, "matchWholeWords": None,
                "useGroupScoring": None, "automationId": "", "role": None,
                "sticky": 0, "cooldown": 0, "delay": 0, "displayIndex": 0
            }

            output_json = {"entries": {"0": entry}}

            default_filename_base = scenario_name_for_comment or "extracted_scenario"
            filename_base = re.sub(r'[^\w\-_\. ]', '_', default_filename_base).replace(' ', '_')
            if not filename_base: filename_base = "extracted_scenario"
            default_save_name = f"{filename_base}.json"

            filename, _ = QFileDialog.getSaveFileName(self, "Save Output JSON", default_save_name, 'JSON files (*.json)')
            if not filename: return
            if not filename.lower().endswith('.json'): filename += '.json'

            if safe_json_save(output_json, filename, indent=4):
                 QMessageBox.information(self, "Success!", f"JSON transformed and saved successfully to:\n{filename}")

        except Exception as e:
             QMessageBox.critical(self, "Transformation Error", f"An unexpected error occurred during transformation or saving:\n{e}")
             print("General Error transforming/saving:", str(e))


# --- 9. EXTRA Tools: Avatar/Icon Downloader --- (Original #9)
class Tool_AvatarDownloader(QWidget):
    def __init__(self, stacked_widget=None):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.inputJson = None # Data not stored long-term
        self._input_filename = None
        self.loadButton = None
        self.loadedFileLabel = None
        self.progressBar = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        backButton = QPushButton("<- Back to Main Menu")
        backButton.clicked.connect(self._go_back)
        layout.addWidget(backButton)

        layout.addWidget(load_sox_image_label(), alignment=Qt.AlignCenter)
        textDesc = QLabel("Download Avatars/Icons from XoulAI JSON")
        textDesc.setAlignment(Qt.AlignCenter)
        layout.addWidget(textDesc)
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        self.loadButton = QPushButton("Get XoulAI JSON & Download Avatars")
        self.loadedFileLabel = QLabel("No file selected")
        self.loadedFileLabel.setAlignment(Qt.AlignCenter)
        self.progressBar = QProgressBar()
        self.progressBar.setAlignment(Qt.AlignCenter)
        self.progressBar.setRange(0, 0)

        layout.addWidget(self.loadButton)
        layout.addWidget(self.loadedFileLabel, alignment=Qt.AlignCenter)
        layout.addWidget(self.progressBar)
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.loadButton.clicked.connect(self.getAvatars)
        self.setLayout(layout)

    def _go_back(self):
         self.inputJson = None
         self._input_filename = None
         if self.loadedFileLabel:
            self.loadedFileLabel.setText("No file selected")
         if self.progressBar:
              self.progressBar.setRange(0, 0)
              self.progressBar.setValue(0)
         if self.stacked_widget:
              self.stacked_widget.setCurrentIndex(0)

    def getAvatars(self):
        self.loadedFileLabel.setText("No file selected")
        self.progressBar.setRange(0, 0)
        self.progressBar.setValue(0)

        json_path, _ = QFileDialog.getOpenFileName(
            self, "Select XoulAI JSON File", '', 'JSON files (*.json);;All Files (*)'
        )
        if not json_path:
            self.loadedFileLabel.setText("File selection cancelled")
            return

        self._input_filename = json_path
        self.loadedFileLabel.setText(f"Selected: {os.path.basename(json_path)}")

        output_dir = QFileDialog.getExistingDirectory(
            self, f"Select Directory to Save Avatars from {os.path.basename(json_path)}"
        )
        if not output_dir:
            self.loadedFileLabel.setText(f"Selected: {os.path.basename(json_path)}")
            return

        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
             QMessageBox.critical(self, "Directory Error", f"Failed to create or access output directory:\n{output_dir}\n{e}")
             self.loadedFileLabel.setText("Error accessing directory")
             return

        json_data = safe_json_load(json_path)

        if json_data is None:
             self.loadedFileLabel.setText("Loading failed")
             return

        if not isinstance(json_data, (dict, list)):
            QMessageBox.warning(self, "JSON Structure Warning", f"Top level element in '{os.path.basename(json_path)}' is not a dictionary or list. Found {type(json_data).__name__}.\nAttempting to search anyway, but results may be limited.")
            # Don't return, try to search whatever structure it is

        def is_potential_image_url(url_string):
            if not isinstance(url_string, str): return False
            url_string_lower = url_string.lower()
            # Basic check for common image extensions in the path or query string
            if url_string_lower.startswith(('http://', 'https://')):
                 parsed_url = urlparse(url_string_lower)
                 path = parsed_url.path
                 query = parsed_url.query # Also check query string as some URLs include extensions there
                 combined_part = path + query
                 _, ext = os.path.splitext(combined_part) # Check extension in path+query
                 image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg')
                 if ext in image_extensions: return True
                 # Less reliable check: look for extension patterns anywhere in the URL
                 if re.search(r'\.(png|jpg|jpeg|gif|bmp|webp|svg)(\?|$)', url_string_lower): return True # Check for extension followed by end or ?
            return False


        def find_image_urls_recursive(data, found_urls, depth=0, max_depth=20):
            if depth > max_depth: return # Prevent infinite recursion on deeply nested or circular references
            if isinstance(data, dict):
                for key, value in data.items():
                    if is_potential_image_url(value):
                        found_urls.add(value)
                    find_image_urls_recursive(value, found_urls, depth + 1, max_depth)
            elif isinstance(data, list):
                for item in data:
                    if is_potential_image_url(item):
                         found_urls.add(item)
                    find_image_urls_recursive(item, found_urls, depth + 1, max_depth)
            elif isinstance(data, str):
                if is_potential_image_url(data):
                     found_urls.add(data)

        def get_safe_filename_from_url(url, directory):
            try:
                parsed_url = urlparse(url)
                path = parsed_url.path
                query = parsed_url.query

                # Try to get filename from path first
                original_filename = os.path.basename(path)

                # If path basename is generic or missing extension, look in query string
                if not original_filename or not os.path.splitext(original_filename)[1]:
                     query_params = urlparse(f"?{query}").path # Simple way to parse query string as path
                     if query_params:
                          query_filename = os.path.basename(query_params)
                          if query_filename and os.path.splitext(query_filename)[1]:
                               original_filename = query_filename


                if not original_filename or original_filename == "/": original_filename = "downloaded_image"

                safe_filename = re.sub(r'[^\w\-_\.]', '_', original_filename)
                # Ensure filename is not empty or starts with a dot after sanitization
                if not safe_filename or safe_filename.startswith('.'):
                    hash_object = hashlib.md5(url.encode()).hexdigest()
                    safe_filename = f"hashed_image_{hash_object[:8]}"
                # Re-add extension if lost during sanitization and wasn't a hash name
                if '.' not in safe_filename and '.' in original_filename:
                     _, original_ext = os.path.splitext(original_filename)
                     safe_filename += original_ext # Add original extension back

                # Fallback: If still no extension or generic, add .png
                if '.' not in safe_filename:
                     safe_filename += ".png" # Default to png if no extension found

                output_path = os.path.join(directory, safe_filename)
                counter = 1
                base_name, file_ext = os.path.splitext(output_path)
                while os.path.exists(output_path):
                    output_path = f"{base_name}_{counter}{file_ext}"
                    counter += 1
                return output_path
            except Exception as e:
                print(f"Error generating safe filename for URL '{url}': {e}")
                # Fallback to a simple hashed name if parsing fails badly
                hash_object = hashlib.md5(url.encode()).hexdigest()
                safe_filename = f"error_hashed_image_{hash_object[:8]}.png"
                output_path = os.path.join(directory, safe_filename)
                counter = 1
                base_name, file_ext = os.path.splitext(output_path)
                while os.path.exists(output_path):
                    output_path = f"{base_name}_{counter}{file_ext}"
                    counter += 1
                return output_path


        found_urls = set()
        find_image_urls_recursive(json_data, found_urls)
        total_urls = len(found_urls)

        if total_urls == 0:
            QMessageBox.information(self, "Info", "No potential image URLs found in the JSON file.")
            self.loadedFileLabel.setText(f"Processed: {os.path.basename(json_path)} (No URLs found)")
            self.progressBar.setRange(0, 0)
            self.progressBar.setValue(0)
            return

        self.progressBar.setRange(0, total_urls)
        self.progressBar.setValue(0)

        download_count = 0
        processed_urls_count = 0
        failed_downloads = {}

        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.loadButton.setEnabled(False)

        try:
            for url in found_urls:
                output_path = None
                try:
                    # Skip if URL is clearly not http/https
                    if not url.lower().startswith(('http://', 'https://')):
                         failed_downloads[url] = "Skipped: Does not appear to be a standard web URL (missing http/https)."
                         print(f"Skipping {url}: Not a web URL.")
                         continue # Skip this URL

                    output_path = get_safe_filename_from_url(url, output_dir)
                    response = requests.get(url, stream=True, timeout=20) # Increased timeout slightly
                    response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

                    # Optional: Check Content-Type if needed, but rely on extension check mostly
                    # content_type = response.headers.get('Content-Type', '')
                    # if not content_type.lower().startswith('image/'):
                    #     failed_downloads[url] = f"Downloaded content is not an image (Content-Type: {content_type})."
                    #     print(f"Downloaded content for {url} is not an image.")
                    #     # Consider deleting the partially downloaded file if any
                    #     if os.path.exists(output_path):
                    #         try: os.remove(output_path)
                    #         except: pass
                    #     continue


                    with open(output_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                             if chunk: # Filter out keep-alive chunks
                                 f.write(chunk)

                    download_count += 1
                    print(f"Successfully downloaded: {url} -> {os.path.basename(output_path)}")

                except requests.exceptions.Timeout:
                     failed_downloads[url] = f"Timeout occurred after 20 seconds."
                     print(f"Failed to download {url}: Timeout")
                except requests.exceptions.ConnectionError as e:
                    failed_downloads[url] = f"Connection error: {e}"
                    print(f"Failed to download {url}: Connection error: {e}")
                except requests.exceptions.HTTPError as e:
                     failed_downloads[url] = f"HTTP error: {e.response.status_code} {e.response.reason}"
                     print(f"Failed to download {url}: HTTP error: {e.response.status_code}")
                except requests.exceptions.RequestException as e:
                    failed_downloads[url] = f"Request error: {e}"
                    print(f"Failed to download {url}: Request error: {e}")
                except IOError as e:
                    failed_downloads[url] = f"File writing error: {e} (Path: {output_path})"
                    print(f"Failed to write file for {url}: {e} (Path: {output_path})")
                except Exception as e:
                    failed_downloads[url] = f"An unexpected error occurred during download: {e}"
                    print(f"An unexpected error occurred while processing {url}: {e}")

                finally:
                    processed_urls_count += 1
                    self.progressBar.setValue(processed_urls_count)
                    QApplication.processEvents() # Keep the GUI responsive

        finally:
             QApplication.restoreOverrideCursor()
             self.loadButton.setEnabled(True)

        # 4. Provide Feedback
        failed_count = len(failed_downloads)
        success_count = download_count

        message = f"Avatar/Icon Download Process Finished.\n"
        message += f"Total potential URLs found in JSON: {total_urls}\n"
        message += f"Successfully downloaded: {success_count}\n"
        message += f"Failed downloads: {failed_count}"

        if failed_count > 0:
            message += "\n\nDetails of failures have been printed to the console."

        QMessageBox.information(self, "Download Complete", message)
        self.loadedFileLabel.setText(f"Processed: {os.path.basename(json_path)} ({success_count}/{total_urls} downloaded)")


# --- Main Hub Application ---
class SOXHub(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("S.O.X. Project - Migration Tools - XoulAI -> TavernAI")
        # Set Window Icon - Added error handling
        try:
            icon = QIcon('SOXico.png')
            if icon.isNull():
                 print("Warning: Could not load SOXico.png for window icon.")
            else:
                self.setWindowIcon(icon)
        except Exception as e:
             print(f"Error loading icon: {e}")

        main_layout = QVBoxLayout(self)

        # --- Create the Main Menu Widget ---
        main_menu_widget = QWidget()
        main_menu_layout = QVBoxLayout(main_menu_widget)

        # Add common top section to main menu widget
        main_menu_layout.addWidget(load_sox_image_label(), alignment=Qt.AlignCenter) # Use helper function
        textDesc = QLabel("Welcome to S.O.X. Project! This tool aims to convert XoulAI JSONs into TavernAI usable JSONs.\nSelect a tool below to get started.")
        textDesc.setAlignment(Qt.AlignCenter)
        main_menu_layout.addWidget(textDesc, alignment=Qt.AlignCenter)
        main_menu_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)) # Flexible spacer

        # --- Tool Selection Buttons ---
        tool_button_layout = QVBoxLayout()
        tool_button_layout.setAlignment(Qt.AlignCenter) # Center the buttons group

        self.btn_single_char = QPushButton("1. Character Converter") # Corresponds to Tool_CharacterSingle
        self.btn_persona_add = QPushButton("2. Persona Adding (to TavernAI Backup)") # Corresponds to Tool_PersonaAdd
        self.btn_scenario_conv = QPushButton("3. Scenario Converter") # Corresponds to Tool_ScenarioConvert
        self.btn_lorebook_conv = QPushButton("4. Lorebook Converter") # Corresponds to Tool_LorebookConvert
        self.btn_single_chat_conv = QPushButton("5. Single Chat Converter (to JSONL)") # Corresponds to Tool_ChatSingle
        self.btn_multi_chat_conv = QPushButton("6. Group Chat Converter (to JSONL)") # Corresponds to Tool_ChatMulti
        self.btn_char_extract = QPushButton("7. Extract Characters (from Chat Backup)") # Corresponds to Tool_CharExtract
        self.btn_chat_scenario_extract = QPushButton("8. Extract Scenario (from Chat Backup)") # Corresponds to Tool_ChatScenarioExtract
        self.btn_avatar_downloader = QPushButton("9. Avatar/Icon Downloader") # Corresponds to Tool_AvatarDownloader

        # --- Reordered Buttons and Labels ---
        tool_button_layout.addWidget(QLabel("<b>Main Tools:</b>"), alignment=Qt.AlignCenter)
        tool_button_layout.addWidget(self.btn_single_char)
        tool_button_layout.addWidget(self.btn_persona_add)
        tool_button_layout.addWidget(self.btn_scenario_conv) # Added the new button
        tool_button_layout.addWidget(self.btn_lorebook_conv)
        tool_button_layout.addItem(QSpacerItem(20, 15, QSizePolicy.Minimum, QSizePolicy.Fixed))

        tool_button_layout.addWidget(QLabel("<b>Chat Tools:</b>"), alignment=Qt.AlignCenter)
        tool_button_layout.addWidget(self.btn_single_chat_conv)
        tool_button_layout.addWidget(self.btn_multi_chat_conv)
        tool_button_layout.addItem(QSpacerItem(20, 15, QSizePolicy.Minimum, QSizePolicy.Fixed))

        tool_button_layout.addWidget(QLabel("<b>EXTRA Tools:</b>"), alignment=Qt.AlignCenter)
        tool_button_layout.addWidget(self.btn_char_extract)
        tool_button_layout.addWidget(self.btn_chat_scenario_extract)
        tool_button_layout.addWidget(self.btn_avatar_downloader)
        # --- End Reordered Buttons ---


        main_menu_layout.addLayout(tool_button_layout)
        main_menu_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # --- Credits Section ---
        textCredits = QLabel("<i>by Junji Dragonfox @ Project BomberCraft</i>")
        textCredits.setAlignment(Qt.AlignRight)
        textCredits.setTextFormat(Qt.RichText)
        # textCredits.setOpenExternalLinks(True) # No actual links, keep this off

        creditButton = QPushButton("SEE CREDITS")
        creditButton.clicked.connect(self.showCreditsWindow) # Renamed connection

        credits_layout = QHBoxLayout()
        credits_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        credits_layout.addWidget(textCredits, alignment=Qt.AlignRight)
        credits_layout.addWidget(creditButton, alignment=Qt.AlignRight)

        main_menu_layout.addLayout(credits_layout)


        # --- Stacked Widget ---
        self.stacked_widget = QStackedWidget()

        # Add the Main Menu Widget as the first page (index 0)
        main_menu_index = self.stacked_widget.addWidget(main_menu_widget)
        self.tool_indices = {}


        # --- Instantiate Tool Widgets and add them to the Stack ---
        # Order of instantiation matters for indices! Match button order in the main menu.
        self.tool_single_char = Tool_CharacterSingle(stacked_widget=self.stacked_widget)
        self.tool_indices['single_char'] = self.stacked_widget.addWidget(self.tool_single_char)

        self.tool_persona_add = Tool_PersonaAdd(stacked_widget=self.stacked_widget)
        self.tool_indices['persona_add'] = self.stacked_widget.addWidget(self.tool_persona_add)

        self.tool_scenario_conv = Tool_ScenarioConvert(stacked_widget=self.stacked_widget) # Instantiate the ADDED tool
        self.tool_indices['scenario_conv'] = self.stacked_widget.addWidget(self.tool_scenario_conv) # Add it to the stack

        self.tool_lorebook_conv = Tool_LorebookConvert(stacked_widget=self.stacked_widget)
        self.tool_indices['lorebook_conv'] = self.stacked_widget.addWidget(self.tool_lorebook_conv)

        self.tool_chat_single = Tool_ChatSingle(stacked_widget=self.stacked_widget) # Renamed
        self.tool_indices['single_chat_conv'] = self.stacked_widget.addWidget(self.tool_chat_single)

        self.tool_chat_multi = Tool_ChatMulti(stacked_widget=self.stacked_widget) # Renamed
        self.tool_indices['multi_chat_conv'] = self.stacked_widget.addWidget(self.tool_chat_multi)

        self.tool_char_extract = Tool_CharExtract(stacked_widget=self.stacked_widget)
        self.tool_indices['char_extract'] = self.stacked_widget.addWidget(self.tool_char_extract)

        self.tool_chat_scenario_extract = Tool_ChatScenarioExtract(stacked_widget=self.stacked_widget)
        self.tool_indices['chat_scenario_extract'] = self.stacked_widget.addWidget(self.tool_chat_scenario_extract)

        self.tool_avatar_downloader = Tool_AvatarDownloader(stacked_widget=self.stacked_widget)
        self.tool_indices['avatar_downloader'] = self.stacked_widget.addWidget(self.tool_avatar_downloader)


        # Add the stacked widget to the main SOXHub layout
        main_layout.addWidget(self.stacked_widget)

        # --- Connect Tool Buttons to Stack Switching ---
        self.btn_single_char.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(self.tool_indices['single_char']))
        self.btn_persona_add.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(self.tool_indices['persona_add']))
        self.btn_scenario_conv.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(self.tool_indices['scenario_conv'])) # Connect the new button
        self.btn_lorebook_conv.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(self.tool_indices['lorebook_conv']))
        self.btn_single_chat_conv.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(self.tool_indices['single_chat_conv']))
        self.btn_multi_chat_conv.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(self.tool_indices['multi_chat_conv']))
        self.btn_char_extract.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(self.tool_indices['char_extract']))
        self.btn_chat_scenario_extract.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(self.tool_indices['chat_scenario_extract']))
        self.btn_avatar_downloader.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(self.tool_indices['avatar_downloader']))


        # Set the initial view to the main menu
        self.stacked_widget.setCurrentIndex(main_menu_index)


    # --- Modified Credits Method ---
    def showCreditsWindow(self): # Renamed from creditsWND
        # Create and show the custom credits window
        # Create as a top-level window (no parent)
        self._credits_window = CreditsWindow()
        self._credits_window.show()
    # --- End Modified Credits Method ---


# --- Main Application Entry Point ---
if __name__ == '__main__':
    # --- Apply Stylesheet ---
    # Define the stylesheet string
    stylesheet = """
        QWidget {
            background-color: #000000; /* Dark background */
            color: #ffffff; /* White font */
            font-family: Consolas, Monaco, 'Courier New', monospace; /* Consolas font, fallbacks */
            font-size: 10pt; /* Adjust font size if needed */
        }

        QLabel {
            color: #ffffff; /* White font for all labels */
            background-color: transparent; /* Ensure labels don't block background */
        }

        QPushButton {
            background-color: #ffffff; /* White background for buttons */
            color: #000000; /* Black font for buttons */
            border: 1px solid #505050; /* Slight border */
            padding: 5px 10px; /* Padding */
            border-radius: 3px; /* Rounded corners */
        }

        QPushButton:hover {
            background-color: #e0e0e0; /* Slightly darker white on hover */
        }

        QPushButton:pressed {
            background-color: #c0c0c0; /* Even darker white when pressed */
        }

        QPushButton:disabled {
            background-color: #3a3a3a; /* Dark background for disabled buttons */
            color: #7a7a7a; /* Grey font for disabled buttons */
        }

        QMessageBox {
             background-color: #000000; /* Dark background for message boxes */
             color: #ffffff; /* White font */
             font-family: Consolas, Monaco, 'Courier New', monospace; /* Consolas font */
             font-size: 10pt;
        }
        /* Style buttons within message boxes specifically */
        QMessageBox QPushButton {
             background-color: #ffffff; /* White background */
             color: #000000; /* Black font */
             border: 1px solid #505050; /* Slight border */
             padding: 5px 10px; /* Padding */
             border-radius: 3px; /* Rounded corners */
        }
        QMessageBox QPushButton:hover {
             background-color: #e0e0e0;
        }
         QMessageBox QPushButton:pressed {
             background-color: #c0c0c0;
        }


        QFileDialog {
            background-color: #000000; /* Dark background for file dialogs */
            color: #ffffff; /* White font */
            font-family: Consolas, Monaco, 'Courier New', monospace; /* Consolas font */
            font-size: 10pt;
        }
         QFileDialog QPushButton {
             background-color: #ffffff; /* White background */
             color: #000000; /* Black font */
             border: 1px solid #505050; /* Slight border */
             padding: 5px 10px; /* Padding */
             border-radius: 3px; /* Rounded corners */
        }
        QFileDialog QPushButton:hover {
             background-color: #e0e0e0;
        }
         QFileDialog QPushButton:pressed {
             background-color: #c0c0c0;
        }


        QProgressBar {
            border: 1px solid #505050; /* Border matching general theme */
            border-radius: 5px; /* Rounded corners */
            background-color: #000000; /* Dark background for the bar */
            text-align: center; /* Center the percentage text */
            color: #2a2a2a; /* White text for percentage */
        }

        QProgressBar::chunk {
            background-color: #FFFFFF; /* Green color for the filled part */
            border-radius: 4px; /* Slightly smaller radius for the chunk */
            margin: 0px; /* Remove space between border and chunk */
        }
    """

    app = QApplication(sys.argv)
    app.setFont(QFont("Consolas")) # Set Consolas as the default font for the application
    app.setStyleSheet(stylesheet) # Apply the stylesheet

    # Optional: High-DPI scaling setup
    # from PyQt5.QtCore import QT_VERSION_STR
    # print(f"PyQt5 version: {QT_VERSION_STR}")
    # if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    #     QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    # if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
    #      QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    hub = SOXHub()
    hub.show()
    sys.exit(app.exec_())
