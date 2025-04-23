import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QFileDialog, QVBoxLayout, QMessageBox, QLabel
from PyQt5.QtCore import Qt  # Add this line at the top of your code.
from PyQt5.QtGui import QPixmap  # Add this line
from PyQt5.QtGui import QIcon
import json
import os

class JSONTransformer(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        # Create GUI components
        textSpacer = QLabel()
        textDesc = QLabel("Welcome to S.O.X. Project! This tool aims to convert XoulAI JSONs into TavernAI usable JSONs.\nThis one is dedicated to add Xoul Personas into TavernAI's Persona backup file to be reimported.\nCreate a Backup in SillyTavern to use this tool.")
        textCredits = QLabel("<i>by Junji Dragonfox @ Project BomberCraft</i>")
        loadButtonA = QPushButton("Import TavernAI Persona's Backup JSON")
        loadButtonB = QPushButton("Add Xoul Persona from JSON")
        saveButton = QPushButton("Export Modified Backup JSON")
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
        layout.addWidget(loadButtonA)
        layout.addWidget(textSpacer)
        layout.addWidget(loadButtonB)
        layout.addWidget(textSpacer)
        layout.addWidget(textOutput)
        layout.addWidget(saveButton)
        layout.addWidget(textSpacer)
        layout.addWidget(textCredits)
        layout.addWidget(creditButton)
        loadButtonA.clicked.connect(self.loadInputFile)
        loadButtonB.clicked.connect(self.loadDataFile)
        saveButton.clicked.connect(self.transformJSONAndSave)
        creditButton.clicked.connect(self.creditsWND)
        self.setLayout(layout)
    def creditsWND(self):
        QMessageBox.information(self, "CREDITS", "R.I.P. XoulAI, we hope you return someday, thanks for the moments.\n\nTesters:\n\nTBA\n\nV0.0.1")
    def loadInputFile(self):
        # Load input JSON file
        filename = QFileDialog.getOpenFileName()[0]
        if not os.path.isfile(filename):
            QMessageBox.information(self, "Error", "Invalid file selection. Please try again.")
            return
        with open(filename, 'r') as f:
            self.input_data = json.load(f)

    def loadDataFile(self):
        # Load config JSON file
        filename = QFileDialog.getOpenFileName()[0]
        if not os.path.isfile(filename):
            QMessageBox.information(self, "Error", "Invalid file selection. Please try again.")
            return
        with open(filename, 'r') as f:
            self.config_data = json.load(f)

    def transformJSONAndSave(self):
        # Transform the input JSON based on config data
        if not hasattr(self, 'input_data') or not hasattr(self, 'config_data'):
            QMessageBox.information(self, "Error", "Please load both files first.")
            return

        output_data = self.input_data.copy()
        if self.config_data:
            new_persona_name = self.config_data['name']
            new_description = self.config_data['prompt']

            # Add a persona to the 'personas' dictionary
            if 'personas' in output_data and isinstance(output_data.get('personas'), dict):
                output_data['personas'][new_persona_name + ".png"] = new_persona_name
            elif 'personas' in output_data and not 'personas' in output_data:
                output_data[new_persona_name + ".png"] = new_persona_name

            # Add a description to the 'persona_descriptions' dictionary
            if 'persona_descriptions' in output_data and isinstance(output_data.get('persona_descriptions'), dict):
                new_description_entry = {new_persona_name + ".png" : {"description": new_description, "position": 0}}
                output_data['persona_descriptions'].update(new_description_entry)
            elif 'persona_descriptions' in output_data:
                if not 'persona_descriptions':
                    output_data[new_persona_name + ".png"] = {"description": new_description, "position": 0}
                else:
                    output_data['persona_descriptions'][new_persona_name + ".png"] = {"description": new_description, "position": 0}

        # Save the transformed JSON to a file
        filename, _ = QFileDialog.getSaveFileName(self, "Save modified JSON", "", "JSON files (*.json)")
        if not filename:
            QMessageBox.information(self, "Error", "Invalid directory selection. Please try again.")
            return

        with open(filename, 'w') as f:
            json.dump(output_data, f)  
            
    def run(self):
        self.show()
        self.setWindowTitle("S.O.X. - Persona Adding Tool")
        self.setWindowIcon(QIcon('SOXico.png'))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    transformer = JSONTransformer()
    transformer.run()
    sys.exit(app.exec_())