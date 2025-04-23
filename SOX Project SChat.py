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
        textDesc = QLabel("Welcome to S.O.X. Project! This tool aims to convert XoulAI JSONs into TavernAI usable JSONs.\nThis one is dedicated to convert Single Xoul Chats into TavernAI Character Chats") 
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
        filename, _ = QFileDialog.getSaveFileName(self, "Save Output JSON Lines", '.', 'JSON files (*.jsonl)')
        if not filename:
            return

        # Extract relevant information from input JSON
        personas = self.inputJson['conversation']['personas'][0]  # Assuming there is only one persona
        xouls = self.inputJson['conversation']['xouls'][0]  # Assuming there is only one xoul
        username = personas.get('name')
        character_name = xouls.get('name')

        # Create output JSON
        output_json = []
        output_json.append({
            "user_name": f"{username}", 
            "character_name": f"{character_name}"
        })
        for message in self.inputJson['messages']:
            if message['role'] == 'user':
                name = username  # Use the persona's name for user messages
            elif message['role'] == 'assistant':
                name = character_name  # Use the xoul's name for assistant messages
            else:
                raise ValueError("Invalid role")

            output_json.append({
                "name": f"{name}",
                "is_user": True if message["role"] == "user" else False,
                "send_date": message['timestamp'],
                "mes": message['content']
            })
        # Save the output JSON in JSON Lines (jsonl) format with line breaks
        with open(filename, 'w') as f:
            for obj in output_json:
                f.write(json.dumps(obj) + '\n')
        QMessageBox.information(self, "Success!", "JSON transformed and saved successfully!")
    
    def run(self):
        self.show()
        self.setWindowTitle("S.O.X. - Single-Chat Conversion Tool")
        self.setWindowIcon(QIcon('SOXico.png'))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    transformer = JSONTransformer()
    transformer.run()
    sys.exit(app.exec_())