from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# -------------------------
# CONFIGURATION
# -------------------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///optocare.db'
app.config['SECRET_KEY'] = 'secret123'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


app.config['UPLOAD_FOLDER'] = 'uploads'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db = SQLAlchemy(app)

# -------------------------
# DATABASE MODEL
# -------------------------
class Partner(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    full_name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    store_name = db.Column(db.String(100))
    location = db.Column(db.String(200))
    phone = db.Column(db.String(50))
    partner_type = db.Column(db.String(100)) 
    services = db.Column(db.Text)
    document = db.Column(db.String(200))
    is_approved = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Partner {self.email}>'

# -------------------------
# CREATE DATABASE
# -------------------------
with app.app_context():
    db.create_all()

# -------------------------
# HOME PAGE
# -------------------------
@app.route('/')
def home():
    return render_template('index.html')

# -------------------------
# SIGNUP PAGE
# -------------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        store_name = request.form.get('company_name')
        location = request.form.get('location')
        phone = request.form.get('phone')
        services = request.form.get('services')

        partner_types = request.form.getlist('partner_type')  # returns a list
        partner_type_str = ", ".join(partner_types)  # store as string

        # File upload
        document = request.files.get('document')
        filename = document.filename if document else None
        if document and filename:
            document.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Save to database
        new_partner = Partner(
            full_name=full_name,
            email=email,
            store_name=store_name,
            location=location,
            phone=phone,
            partner_type=partner_type_str,
            services=services,
            document=filename
        )

        db.session.add(new_partner)
        db.session.commit()

        return "Application submitted. Wait for admin approval."

    return render_template('signup.html')

# -------------------------
# LOGIN PAGE
# -------------------------
@app.route('/login')
def login():
    return "Login disabled. Admin approves partners first."

# -------------------------
# ADMIN DASHBOARD
# -------------------------
@app.route('/admin')
def admin():
    pending_partners = Partner.query.filter_by(is_approved=False).all()
    return render_template('admin-dashboard.html', partners=pending_partners)

# -------------------------
# APPROVE PARTNER
# -------------------------
@app.route('/approve/<int:id>')
def approve(id):
    partner = Partner.query.get(id)
    partner.is_approved = True
    db.session.commit()
    return redirect(url_for('admin'))

# -------------------------
# PARTNER DASHBOARD
# -------------------------
@app.route('/partner')
def partner():
    return render_template('partner-dashboard.html')

# -------------------------
# RUN SERVER
# -------------------------
if __name__ == '__main__':
    app.run(debug=True)