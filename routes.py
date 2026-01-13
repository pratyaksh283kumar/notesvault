from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file, jsonify, current_app
from flask_login import login_required, current_user
from flask_mail import Message
from werkzeug.utils import secure_filename
from models import db, Note
from config import Config
import requests
import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch

main = Blueprint('main', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def extract_text_from_image_ocrspace(image_path):
    """Extract text from image using OCR.space API"""
    try:
        # Prepare the image file
        with open(image_path, 'rb') as f:
            # OCR.space API endpoint
            payload = {
                'apikey': Config.OCRSPACE_API_KEY,
                'language': 'eng',
                'isOverlayRequired': False,
                'detectOrientation': True,
                'scale': True,
                'OCREngine': 2,  # Engine 2 is better for handwriting
            }
            
            files = {
                'file': f
            }
            
            # Make API request
            response = requests.post(
                Config.OCRSPACE_API_URL,
                files=files,
                data=payload,
                timeout=30
            )
            
            result = response.json()
            
            # Check if request was successful
            if result.get('IsErroredOnProcessing'):
                error_msg = result.get('ErrorMessage', ['Unknown error'])[0]
                print(f"OCR.space API error: {error_msg}")
                return ""
            
            # Extract text from response
            if result.get('ParsedResults'):
                text = result['ParsedResults'][0].get('ParsedText', '')
                return text.strip()
            
            return ""
            
    except requests.exceptions.Timeout:
        print("OCR.space API timeout")
        return ""
    except Exception as e:
        print(f"Error calling OCR.space API: {e}")
        return ""

@main.route('/')
@login_required
def index():
    notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.created_at.desc()).all()
    
    # Get usage stats
    monthly_usage = current_user.get_monthly_usage()
    usage_limit = Config.FREE_MONTHLY_LIMIT
    remaining = usage_limit - monthly_usage
    
    return render_template('index.html', 
                         notes=notes, 
                         monthly_usage=monthly_usage,
                         usage_limit=usage_limit,
                         remaining=remaining)

@main.route('/upload', methods=['POST'])
@login_required
def upload():
    # Check monthly limit BEFORE processing
    if not current_user.can_upload(Config.FREE_MONTHLY_LIMIT):
        monthly_usage = current_user.get_monthly_usage()
        flash(f'Monthly limit reached! You have used {monthly_usage}/{Config.FREE_MONTHLY_LIMIT} scans this month. Limit resets next month.', 'error')
        return redirect(url_for('main.index'))
    
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('main.index'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('main.index'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        try:
            # Check API key
            if Config.OCRSPACE_API_KEY == 'YOUR_API_KEY_HERE':
                flash('OCR.space API key not configured. Please add your API key to config.py', 'error')
                os.remove(filepath)
                return redirect(url_for('main.index'))
            
            # Extract text using OCR.space API
            extracted_text = extract_text_from_image_ocrspace(filepath)
            
            # Log API usage IMMEDIATELY after API call (whether successful or not)
            # This prevents users from gaming the system by deleting notes
            current_user.log_api_usage()
            
            if not extracted_text or not extracted_text.strip():
                flash('No text could be extracted. Try an image with clearer text or better lighting. (API usage counted)', 'warning')
                os.remove(filepath)
                return redirect(url_for('main.index'))
            
            # Save to database
            note = Note(
                user_id=current_user.id,
                filename=filename,
                extracted_text=extracted_text
            )
            db.session.add(note)
            db.session.commit()
            
            os.remove(filepath)
            
            # Show remaining scans
            remaining = Config.FREE_MONTHLY_LIMIT - current_user.get_monthly_usage()
            flash(f'Note uploaded successfully! You have {remaining} scans remaining this month.', 'success')
            return redirect(url_for('main.index'))
            
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            flash(f'Error processing image: {str(e)}', 'error')
            return redirect(url_for('main.index'))
    
    flash('Invalid file type. Please upload an image.', 'error')
    return redirect(url_for('main.index'))

@main.route('/search')
@login_required
def search():
    query = request.args.get('q', '')
    
    if query:
        notes = Note.query.filter(
            Note.user_id == current_user.id,
            Note.extracted_text.like(f'%{query}%')
        ).order_by(Note.created_at.desc()).all()
    else:
        notes = []
    
    return render_template('search.html', notes=notes, query=query)

@main.route('/delete/<int:note_id>')
@login_required
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    
    if note.user_id != current_user.id:
        flash('Unauthorized action', 'error')
        return redirect(url_for('main.index'))
    
    db.session.delete(note)
    db.session.commit()
    flash('Note deleted successfully', 'success')
    return redirect(url_for('main.index'))

@main.route('/edit/<int:note_id>', methods=['GET', 'POST'])
@login_required
def edit_note(note_id):
    note = Note.query.get_or_404(note_id)
    
    if note.user_id != current_user.id:
        flash('Unauthorized action', 'error')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        note.extracted_text = request.form.get('text')
        db.session.commit()
        flash('Note updated successfully!', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('edit_note.html', note=note)

@main.route('/feedback', methods=['GET', 'POST'])
@login_required
def feedback():
    if request.method == 'POST':
        subject = request.form.get('subject')
        message_text = request.form.get('message')
        
        print("\n[FEEDBACK] Processing feedback submission...")
        print(f"[FEEDBACK] From user: {current_user.email}")
        print(f"[FEEDBACK] Subject: {subject}")
        
        # Check if mail is configured
        mail_user = current_app.config.get('MAIL_USERNAME')
        mail_pass = current_app.config.get('MAIL_PASSWORD')
        
        print(f"[FEEDBACK] MAIL_USERNAME from config: {mail_user}")
        print(f"[FEEDBACK] MAIL_PASSWORD configured: {'Yes' if mail_pass else 'No'}")
        
        if not mail_user or not mail_pass:
            print("[FEEDBACK] ✗ Email not configured!")
            flash('Email is not configured. Please set MAIL_USERNAME and MAIL_PASSWORD environment variables.', 'error')
            return redirect(url_for('main.feedback'))
        
        try:
            from flask_mail import Mail
            mail = Mail(current_app)
            
            msg = Message(
                subject=f'OCR App Feedback: {subject}',
                sender=mail_user,
                recipients=[current_app.config['FEEDBACK_EMAIL']]
            )
            msg.body = f"""
Feedback from: {current_user.email}

Subject: {subject}

Message:
{message_text}

---
Sent from OCR Note Searcher
            """
            
            print(f"[FEEDBACK] Sending email to: {current_app.config['FEEDBACK_EMAIL']}")
            print(f"[FEEDBACK] From: {mail_user}")
            
            mail.send(msg)
            
            print("[FEEDBACK] ✓ Email sent successfully!")
            flash('Thank you for your feedback! We will get back to you soon.', 'success')
            return redirect(url_for('main.index'))
            
        except Exception as e:
            error_msg = str(e)
            print(f"[FEEDBACK] ✗ Email error: {error_msg}")
            
            if 'Authentication' in error_msg or '535' in error_msg:
                flash('Email authentication failed. Check your Gmail App Password.', 'error')
            elif 'Connection' in error_msg or 'timed out' in error_msg:
                flash('Could not connect to email server. Check your internet.', 'error')
            else:
                flash(f'Failed to send feedback: {error_msg}', 'error')
            
            return redirect(url_for('main.feedback'))
    
    return render_template('feedback.html')

@main.route('/help')
@login_required
def help_page():
    return render_template('help.html')

@main.route('/terms')
def terms():
    return render_template('terms.html')

@main.route('/create-note', methods=['GET', 'POST'])
@login_required
def create_note():
    if request.method == 'POST':
        title = request.form.get('title')
        text_content = request.form.get('text_content')
        
        if not title or not text_content:
            flash('Please provide both title and content', 'error')
            return redirect(url_for('main.create_note'))
        
        # Save as note
        note = Note(
            user_id=current_user.id,
            filename=title,
            extracted_text=text_content
        )
        db.session.add(note)
        db.session.commit()
        
        flash('Note created successfully!', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('create_note.html')

@main.route('/export/html')
@login_required
def export_html():
    notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.created_at.desc()).all()
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>My Study Notes</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; }
            .note { margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
            .note-title { font-size: 18px; font-weight: bold; color: #333; margin-bottom: 10px; }
            .note-date { font-size: 12px; color: #666; margin-bottom: 15px; }
            .note-content { line-height: 1.6; white-space: pre-wrap; }
        </style>
    </head>
    <body>
        <h1>My Study Notes</h1>
    """
    
    for note in notes:
        html_content += f"""
        <div class="note">
            <div class="note-title">{note.filename}</div>
            <div class="note-date">{note.created_at.strftime('%Y-%m-%d %H:%M')}</div>
            <div class="note-content">{note.extracted_text}</div>
        </div>
        """
    
    html_content += """
    </body>
    </html>
    """
    
    return send_file(
        BytesIO(html_content.encode('utf-8')),
        mimetype='text/html',
        as_attachment=True,
        download_name='study_notes.html'
    )

@main.route('/export/pdf')
@login_required
def export_pdf():
    notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.created_at.desc()).all()
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30
    )
    
    note_title_style = ParagraphStyle(
        'NoteTitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=6
    )
    
    story.append(Paragraph("Your Notes", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    for note in notes:
        story.append(Paragraph(note.filename, note_title_style))
        story.append(Paragraph(note.created_at.strftime('%Y-%m-%d %H:%M'), styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
        
        paragraphs = note.extracted_text.split('\n')
        for para in paragraphs:
            if para.strip():
                story.append(Paragraph(para, styles['Normal']))
        
        story.append(Spacer(1, 0.3*inch))
    
    doc.build(story)
    buffer.seek(0)
    
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name='study_notes.pdf'
    )