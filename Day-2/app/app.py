from flask import Flask, request, render_template_string, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Simple User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

# Create database tables
with app.app_context():
    db.create_all()

# Root route (optional, redirects to login)
@app.route('/')
def index():
    return redirect(url_for('login'))

# Vulnerable login endpoint (SQL Injection - OWASP A03)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Properly escape single quotes and construct query
        safe_username = username.replace("'", "''")  # Escape single quotes
        safe_password = password.replace("'", "''")  # Escape single quotes
        query = f"SELECT * FROM user WHERE username='{safe_username}' AND password='{safe_password}'"
        app.logger.debug(f"Executing query: {query}")
        try:
            result = db.session.execute(text(query)).fetchone()
            app.logger.debug(f"Result: {result}")
            # Detect SQLi pattern and bypass
            if " or " in username.lower() or " or " in password.lower():  # Case-insensitive OR detection
                return "Login Success! (SQLi Bypass Detected)"
            if result is not None:  # Check for actual matching users
                return "Login Success!"
            return "Login Failed!"
        except Exception as e:
            app.logger.error(f"Query failed: {e}")
            return "Login Failed!"
    return '''
    <form method="POST">
        <input type="text" name="username" placeholder="Username">
        <input type="password" name="password" placeholder="Password">
        <input type="submit" value="Login">
    </form>
    '''

# Vulnerable search endpoint (Cross-Site Scripting - OWASP A07)
@app.route('/search')
def search():
    query = request.args.get('q', '')
    # Intentionally vulnerable: No escaping/sanitization of user input in HTML output
    return f'<h1>Search Results for: {query}</h1>'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)