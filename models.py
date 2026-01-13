from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to notes
    notes = db.relationship('Note', backref='user', lazy=True, cascade='all, delete-orphan')
    # Relationship to API usage logs
    api_logs = db.relationship('APIUsageLog', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_monthly_usage(self):
        """Get number of OCR API calls this month (not deletable!)"""
        now = datetime.utcnow()
        first_day = datetime(now.year, now.month, 1)
        count = APIUsageLog.query.filter(
            APIUsageLog.user_id == self.id,
            APIUsageLog.created_at >= first_day
        ).count()
        return count
    
    def can_upload(self, limit):
        """Check if user can upload more notes"""
        return self.get_monthly_usage() < limit
    
    def log_api_usage(self):
        """Log an API call (cannot be deleted)"""
        log = APIUsageLog(user_id=self.id)
        db.session.add(log)
        db.session.commit()

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    extracted_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Note {self.filename}>'

class APIUsageLog(db.Model):
    """Track API usage separately from notes - cannot be deleted by users"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<APIUsageLog user_id={self.user_id} at {self.created_at}>'
