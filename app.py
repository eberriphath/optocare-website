from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

# CONFIG
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///optocare.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'secret123'
app.config['UPLOAD_FOLDER'] = 'uploads'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db = SQLAlchemy(app)

# -------------------------
# MODEL
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

    is_admin = db.Column(db.Boolean, default=False)  # ✅ NEW

# -------------------------
# CREATE DB
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
        email = request.form.get('email')

        # Prevent duplicate
        if Partner.query.filter_by(email=email).first():
            return "Email already exists. Please login."

        new_partner = Partner(
            full_name=request.form.get('full_name'),
            email=email,
            password=generate_password_hash(request.form.get('password')),
            store_name=request.form.get('company_name'),
            location=request.form.get('location'),
            phone=request.form.get('phone'),
            partner_type=", ".join(request.form.getlist('partner_type')),
            services=request.form.get('services')
        )

        # 👇 TEMP ADMIN CREATION
        if email == "admin@optocare.com":
            new_partner.is_admin = True
            new_partner.is_approved = True

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
        partner = Partner.query.filter_by(email=request.form['email']).first()

        if not partner:
            return "Invalid login details"

        if partner.is_rejected:
            return "Your application was rejected."

        if not partner.is_approved and not partner.is_admin:
            return "Your account is not approved yet."

        if check_password_hash(partner.password, request.form['password']):
            session['partner_id'] = partner.id

            if partner.is_admin:
                return redirect('/admin')

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
# ADMIN DASHBOARD
# -------------------------
@app.route('/admin')
def admin():
    if not session.get('partner_id'):
        return redirect('/login')

    user = db.session.get(Partner, session['partner_id'])

    if not user or not user.is_admin:
        return "Access denied"

    partners = Partner.query.all()
    pending = Partner.query.filter_by(is_approved=False).all()

    return render_template('admin-dashboard.html', partners=partners, pending=pending)

# -------------------------
# APPROVE
# -------------------------
@app.route('/approve/<int:id>')
def approve(id):
    user = db.session.get(Partner, session.get('partner_id'))

    if not user or not user.is_admin:
        return "Access denied"

    partner = db.session.get(Partner, id)
    partner.is_approved = True
    partner.is_rejected = False

    db.session.commit()
    return redirect('/admin')

# -------------------------
# REJECT
# -------------------------
@app.route('/reject/<int:id>')
def reject(id):
    user = db.session.get(Partner, session.get('partner_id'))

    if not user or not user.is_admin:
        return "Access denied"

    partner = db.session.get(Partner, id)
    partner.is_rejected = True
    partner.is_approved = False

    db.session.commit()
    return redirect('/admin')

# -------------------------
# PARTNER DASHBOARD
# -------------------------
@app.route('/partner')
def partner_dashboard():
    if not session.get('partner_id'):
        return redirect('/login')

    partner = db.session.get(Partner, session['partner_id'])

    if not partner:
        return redirect('/login')

    return render_template('partner-dashboard.html', partner=partner)

# -------------------------
# PUBLIC PARTNERS
# -------------------------
@app.route('/partners')
def partners():
    approved = Partner.query.filter_by(is_approved=True).all()
    return render_template('partners.html', partners=approved)

# -------------------------
# PARTNER PROFILE
# -------------------------
@app.route('/partner/<int:id>')
def partner_profile(id):
    partner = db.session.get(Partner, id)

    if not partner or not partner.is_approved:
        return "This partner is not available."

    return render_template('partner-profile.html', partner=partner)

# -------------------------
# RUN
# -------------------------
if __name__ == '__main__':
    app.run(debug=True)