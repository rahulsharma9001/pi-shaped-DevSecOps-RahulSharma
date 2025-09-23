from flask import Flask
import os

app = Flask(__name__)

# Importing .env file for using secrets instead of hardcoding them

API_KEY = os.getenv('API_KEY', 'default-key')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'default-pass')

@app.route('/')
def home():
    return f"Hello, This is a demo message for the Security compliance workshop !!!!!"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')