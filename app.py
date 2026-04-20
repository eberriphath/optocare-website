from flask import Flask, render_template, request, redirect, session, url_for
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

    # ✅ NEW ROLE SYSTEM
    role = db.Column(db.String(20), default="partner")


# -------------------------
# INIT DB + CREATE ADMIN
# -------------------------
with app.app_context():
    db.create_all()

    # ✅ Create admin if not exists
    admin = Partner.query.filter_by(email="admin@optocare.com").first()

    if not admin:
        admin = Partner(
            full_name="System Admin",
            email="admin@optocare.com",
            password=generate_password_hash("admin123"),
            role="admin",
            is_approved=True
        )
        db.session.add(admin)
        db.session.commit()


# -------------------------
# HELPERS
# -------------------------
def current_user():
    user_id = session.get('partner_id')
    if not user_id:
        return None
    return db.session.get(Partner, user_id)


def admin_required():
    user = current_user()
    return user and user.role == "admin"


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
            services=request.form.get('services'),
            role="partner"
        )

        db.session.add(new_partner)
        db.session.commit()

        return redirect(url_for('login'))

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

        if not check_password_hash(partner.password, request.form['password']):
            return "Invalid login details"

        if partner.is_rejected:
            return "Your application was rejected."

        if not partner.is_approved and partner.role != "admin":
            return "Your account is not approved yet."

        session['partner_id'] = partner.id

        if partner.role == "admin":
            return redirect(url_for('admin'))

        return redirect(url_for('partner_dashboard'))

    return render_template('login.html')


# -------------------------
# LOGOUT
# -------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# -------------------------
# ADMIN DASHBOARD
# -------------------------
@app.route('/admin')
def admin():
    if not admin_required():
        return redirect(url_for('login'))

    partners = Partner.query.all()
    pending = Partner.query.filter_by(is_approved=False).all()

    return render_template('admin-dashboard.html', partners=partners, pending=pending)


# -------------------------
# APPROVE
# -------------------------
@app.route('/approve/<int:id>')
def approve(id):
    if not admin_required():
        return "Access denied"

    partner = db.session.get(Partner, id)
    if not partner:
        return "User not found"

    partner.is_approved = True
    partner.is_rejected = False

    db.session.commit()
    return redirect(url_for('admin'))


# -------------------------
# REJECT
# -------------------------
@app.route('/reject/<int:id>')
def reject(id):
    if not admin_required():
        return "Access denied"

    partner = db.session.get(Partner, id)
    if not partner:
        return "User not found"

    partner.is_rejected = True
    partner.is_approved = False

    db.session.commit()
    return redirect(url_for('admin'))


# -------------------------
# PARTNER DASHBOARD
# -------------------------
@app.route('/partner')
def partner_dashboard():
    partner = current_user()

    if not partner:
        return redirect(url_for('login'))

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