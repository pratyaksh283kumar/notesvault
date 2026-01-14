from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from models import db, User
from config import Config
from auth import auth
from routes import main
import os

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[APP] .env file loaded successfully")
except ImportError:
    print("[APP] python-dotenv not installed, using environment variables")

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
mail = Mail(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register blueprints
app.register_blueprint(auth)
app.register_blueprint(main)

# Initialize app
Config.init_app(app)

# Create database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    print("\n" + "="*60)
    print("Starting OCR Note Searcher Application")
    print("="*60)
    print(f"App running at: http://127.0.0.1:5000")
    print("="*60 + "\n")
    app.run(host = "0.0.0.0",port=5000)
