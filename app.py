from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

# -------------------------
# CONFIGURATION
# -------------------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///optocare.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'secret123'

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
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    store_name = db.Column(db.String(100))
    location = db.Column(db.String(200))
    phone = db.Column(db.String(50))
    partner_type = db.Column(db.String(100))
    services = db.Column(db.Text)

    document = db.Column(db.String(200))

    is_approved = db.Column(db.Boolean, default=False)
    is_rejected = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Partner {self.email}>'

# -------------------------
# CREATE DATABASE
# -------------------------
with app.app_context():
    db.create_all()

# -------------------------
# HOME
# -------------------------
@app.route('/')
def home():
    return render_template('index.html')

# -------------------------
# SIGNUP
# -------------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        store_name = request.form.get('company_name')
        location = request.form.get('location')
        phone = request.form.get('phone')
        services = request.form.get('services')

        partner_types = request.form.getlist('partner_type')
        partner_type_str = ", ".join(partner_types)

        # Hash password
        hashed_password = generate_password_hash(password)

        # File upload
        document = request.files.get('document')
        filename = None
        if document and document.filename != '':
            filename = document.filename
            document.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        new_partner = Partner(
            full_name=full_name,
            email=email,
            password=hashed_password,
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
# LOGIN
# -------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        partner = Partner.query.filter_by(email=email).first()

        if partner:
            if partner.is_rejected:
                return "Your application was rejected."

            if not partner.is_approved:
                return "Your account is not approved yet."

            if check_password_hash(partner.password, password):
                session['partner_id'] = partner.id
                return redirect('/partner')

        return "Invalid login details"

    return render_template('login.html')

# -------------------------
# LOGOUT
# -------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# -------------------------
# ADMIN DASHBOARD (PROTECTED)
# -------------------------
@app.route('/admin')
def admin():
    if 'partner_id' not in session:
        return redirect('/login')

    partners = Partner.query.all()
    pending = Partner.query.filter_by(is_approved=False).all()

    return render_template('admin-dashboard.html', partners=partners, pending=pending)

# -------------------------
# APPROVE PARTNER
# -------------------------
@app.route('/approve/<int:id>')
def approve(id):
    partner = Partner.query.get_or_404(id)
    partner.is_approved = True
    partner.is_rejected = False
    db.session.commit()
    return redirect('/admin')

# -------------------------
# REJECT PARTNER
# -------------------------
@app.route('/reject/<int:id>')
def reject(id):
    partner = Partner.query.get_or_404(id)
    partner.is_rejected = True
    partner.is_approved = False
    db.session.commit()
    return redirect('/admin')

# -------------------------
# PARTNER DASHBOARD (PROTECTED)
# -------------------------
@app.route('/partner')
def partner_dashboard():
    if 'partner_id' not in session:
        return redirect('/login')

    partner = Partner.query.get(session['partner_id'])
    return render_template('partner-dashboard.html', partner=partner)

# -------------------------
# 🌍 PUBLIC PARTNERS DIRECTORY
# -------------------------
@app.route('/partners')
def partners():
    approved_partners = Partner.query.filter_by(is_approved=True).all()
    return render_template('partners.html', partners=approved_partners)

# -------------------------
# 👤 SINGLE PARTNER PROFILE
# -------------------------
@app.route('/partner/<int:id>')
def partner_profile(id):
    partner = Partner.query.get_or_404(id)

    if not partner.is_approved:
        return "This partner is not available."

    return render_template('partner-profile.html', partner=partner)

# -------------------------
# RUN APP
# -------------------------
if __name__ == '__main__':
    app.run(debug=True)