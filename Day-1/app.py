from flask import Flask

app = Flask(__name__)

# Hardcoded secrets (fake for demo) - to be detected by Gitleaks

API_KEY = "REMOVED"          # Fake Stripe-like API key
DB_PASSWORD = "REMOVED"  # Fake DB password

@app.route('/')
def home():
    return f"Welcome! API Key: {API_KEY} | DB Pass: {DB_PASSWORD}"

if __name__ == '__main__':
    app.run(debug=True)