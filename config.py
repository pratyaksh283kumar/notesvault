import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Create instance directory if it doesn't exist
    INSTANCE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    os.makedirs(INSTANCE_PATH, exist_ok=True)
    
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(INSTANCE_PATH, "database.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}
    
    # OCR.space API Configuration
    OCRSPACE_API_KEY = os.getenv('OCRSPACE_API_KEY', 'YOUR_API_KEY_HERE')
    OCRSPACE_API_URL = 'https://api.ocr.space/parse/image'
    
    # Monthly usage limits
    FREE_MONTHLY_LIMIT = 100
    
    # Flask-Mail Configuration - Load from environment
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_USERNAME')
    FEEDBACK_EMAIL = 'krpratyaksh@gmail.com'
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    @staticmethod
    def init_app(app):
        # Create necessary directories
        os.makedirs('instance', exist_ok=True)
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        
        # Print config status for debugging
        print("\n[CONFIG] Checking email configuration...")
        if Config.MAIL_USERNAME:
            print(f"[CONFIG] ✓ MAIL_USERNAME is set: {Config.MAIL_USERNAME}")
        else:
            print("[CONFIG] ✗ MAIL_USERNAME is NOT set!")
            
        if Config.MAIL_PASSWORD:
            print(f"[CONFIG] ✓ MAIL_PASSWORD is set: {'*' * 16}")
        else:
            print("[CONFIG] ✗ MAIL_PASSWORD is NOT set!")
        print()
