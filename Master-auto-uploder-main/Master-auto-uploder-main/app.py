import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Web App is running on Render!"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Render द्वारा दिया गया पोर्ट
    app.run(host="0.0.0.0", port=port)  # सभी नेटवर्क इंटरफेस पर सुनना ज़रूरी है

