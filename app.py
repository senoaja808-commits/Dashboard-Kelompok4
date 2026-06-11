import os
import json
import re
import datetime
from flask import Flask, render_template, request, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, ValidationError

app = Flask(__name__)

# Konfigurasi
app.config['SECRET_KEY'] = 'rahasia_super_rahasia_ganti_di_produksi'  # Ganti dengan random string
app.config['MESSAGE_FILE'] = 'messages.json'

# --- Dummy Data ---
PROJECTS = [
    {
        "id": 1,
        "title": "Presentasi ",
        "desc": "Pulp Dryer",
        "tech": ["Control System", "Instrument"],
        "img": "static\\images\\PD2.png",
        "link":"https://canva.link/n979qrxli6cguu8"

    },
    {
        "id": 2,
        "title": "Presentasi",
        "desc": "Recausticising and Lime Kiln",
        "tech": ["Process System", "Instrument"],
        "img": "static\\images\\Recaust.png",
        "link": "https://canva.link/7jy826wquam68d7"
    },

]

SKILLS = {
    "Pulp Mill": ["Wood Handling", "Fiberline", "Pulp Dryer", "Chemical plant"],
    "End Product": ["Paper", "Rayon", "Board", "Tissue"],
    "Other": ["Automation", "Intrumentasi", "Python", "Agentic AI"]
}

ABOUTS = {
    "name": "Goku",
    "role": "Pulp Paper Industry Engineer",
    "bio": "Seorang Engineer yang bersemangat dalam improvement produk dan membantu customer experience.",
    "experience": [
        {"role": "Senior Eng", "company": "Tech Corp", "year": "2026 - Sekarang"},
        {"role": "Junior Eng", "company": "StartUp Inc", "year": "2024 - 2026"}
    ]
}


# --- Form Classes ---
class ContactForm(FlaskForm):
    name = StringField('Nama', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    message = TextAreaField('Pesan', validators=[DataRequired()])
    submit = SubmitField('Kirim Pesan')

    def validate_email(self, email):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email.data):
            raise ValidationError('Format email tidak valid.')

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/abouts')
def about():
    return render_template('abouts.html', data=ABOUTS)

@app.route('/projects')
def projects():
    return render_template('projects.html', projects=PROJECTS)

@app.route('/skills')
def skills():
    return render_template('skills.html', skills=SKILLS)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        # Simpan ke file JSON
        msg_data = {
            "name": form.name.data,
            "email": form.email.data,
            "message": form.message.data,
            "timestamp": str(datetime.datetime.now())
        }
        
        if os.path.exists(app.config['MESSAGE_FILE']):
            with open(app.config['MESSAGE_FILE'], 'r+', encoding='utf-8') as f:
                data = json.load(f)
                data.append(msg_data)
                f.seek(0)
                json.dump(data, f, indent=4)
        else:
            with open(app.config['MESSAGE_FILE'], 'w', encoding='utf-8') as f:
                json.dump([msg_data], f, indent=4)
        
        return jsonify({"status": "success", "message": "Pesan terkirim!"})
    
    return render_template('contact.html', form=form)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=True)
    
