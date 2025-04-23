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
        textDesc = QLabel("Welcome to S.O.X. Project! This tool aims to convert XoulAI JSONs into TavernAI usable JSONs.\nThis one is dedicated to convert Lorebooks into TavernAI World Entries") 
        textCredits = QLabel("<i>by Junji Dragonfox @ Project BomberCraft</i>")
        loadButton = QPushButton("Import Xoul Lorebook JSON")
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
        if not hasattr(self, 'inputJson'):
            QMessageBox.warning(self, "Error", "No JSON loaded!")
            return
        # Convert the input dictionary to a string
        self.inputJson = json.dumps(self.inputJson)

        # Get the input JSON (now it's a string)
        input_data = json.loads(self.inputJson)
        # Create a new dictionary to hold the output
        output_json = {"entries": {}}
        # Iterate over the 'sections' array and create a new entry for each item
        if "embedded" in input_data and "sections" in input_data["embedded"]:
            entries_dict = {}
            for i, section in enumerate(input_data["embedded"]["sections"]):
                key = str(i)
                entry = {
                    "uid": i,
                    "key": section.get("keywords", []),
                    "keysecondary": [],
                    "comment": section.get("name", ""),
                    "content": section.get("text", ""),
                    "constant": False,
                    "vectorized": False,
                    "selective": True,
                    "selectiveLogic": 0,
                    "addMemo": True,
                    "order": 100,
                    "position": 0,
                    "disable": False,
                    "excludeRecursion": False,
                    "preventRecursion": False,
                    "delayUntilRecursion": False,
                    "probability": 100,
                    "useProbability": True,
                    "depth": 4,
                    "group": "",
                    "groupOverride": False,
                    "groupWeight": 100,
                    "scanDepth": None,
                    "caseSensitive": None,
                    "matchWholeWords": None,
                    "useGroupScoring": None,
                    "automationId": "",
                    "role": None,
                    "sticky": 0,
                    "cooldown": 0,
                    "delay": 0,
                    "displayIndex": i
                }
                entries_dict[key] = entry

            output_json["entries"] = entries_dict

        # Convert the output dictionary to JSON and save it
        filename, _ = QFileDialog.getSaveFileName(self, "Save Output JSON", '.', 'JSON files (*.json)')
        if not filename:
            return
        with open(filename, 'w') as f:
            json.dump(output_json, f)
        QMessageBox.information(self, "Success!", "JSON transformed and saved successfully!")
    
    def run(self):
        self.show()
        self.setWindowTitle("S.O.X. - Lorebook Conversion Tool")
        self.setWindowIcon(QIcon('SOXico.png'))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    transformer = JSONTransformer()
    transformer.run()
    sys.exit(app.exec_())