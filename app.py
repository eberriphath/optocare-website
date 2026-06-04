from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime
import os
import re

app = Flask(__name__)

# -------------------------
# CONFIG
# -------------------------
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL

else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///optocare.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

SECRET_KEY = os.environ.get(
    "SECRET_KEY"
)

if not SECRET_KEY:
    raise Exception(
        "SECRET_KEY missing"
    )

app.config['SECRET_KEY'] = SECRET_KEY

app.config.update(

    SESSION_COOKIE_HTTPONLY=True,

    SESSION_COOKIE_SECURE=True,

    SESSION_COOKIE_SAMESITE='Lax'

)

app.config['UPLOAD_FOLDER'] = 'uploads'

os.makedirs(
    app.config['UPLOAD_FOLDER'],
    exist_ok=True
)

db = SQLAlchemy(app)

serializer = URLSafeTimedSerializer(
    app.config['SECRET_KEY']
)

# -------------------------
# MODELS
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

    role = db.Column(db.String(20), default="partner")

    # Relationship
    orders = db.relationship('Order', backref='partner', lazy=True)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    partner_id = db.Column(
        db.Integer,
        db.ForeignKey('partner.id'),
        nullable=False
    )

    # Customer
    order_number = db.Column(db.String(50))
    date = db.Column(db.String(50))
    name = db.Column(db.String(100))
    phone = db.Column(db.String(50))
    dob = db.Column(db.String(50))

    # Frame
    frame_make = db.Column(db.String(100))
    frame_model = db.Column(db.String(100))
    frame_size = db.Column(db.String(100))
    frame_color = db.Column(db.String(100))

    # RIGHT
    right_sph = db.Column(db.String(20))
    right_cyl = db.Column(db.String(20))
    right_axis = db.Column(db.String(20))
    right_add = db.Column(db.String(20))
    right_pd = db.Column(db.String(20))

    # LEFT
    left_sph = db.Column(db.String(20))
    left_cyl = db.Column(db.String(20))
    left_axis = db.Column(db.String(20))
    left_add = db.Column(db.String(20))
    left_pd = db.Column(db.String(20))

    # Lens
    lens_type = db.Column(db.String(100))
    coating = db.Column(db.String(100))
    tint = db.Column(db.String(100))
    base_curve = db.Column(db.String(100))

    # Order status
    status = db.Column(db.String(20), default="pending")

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# -------------------------
# INIT DB + ADMIN
# -------------------------
with app.app_context():

    db.create_all()

admin_email = "admin@optocare.com"

admin_password = os.environ.get(
    "ADMIN_PASSWORD"
)

if not admin_password:

    raise Exception(
        "ADMIN_PASSWORD missing"
    )

    admin = Partner.query.filter_by(
        email=admin_email
    ).first()

    if not admin:

        admin = Partner(
            full_name="System Admin",
            email=admin_email,
            password=generate_password_hash(admin_password),
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
            return "Email already exists."

        new_partner = Partner(
            full_name=request.form.get('full_name'),
            email=email,
            password=generate_password_hash(
                request.form.get('password')
            ),
            store_name=request.form.get('company_name'),
            location=request.form.get('location'),
            phone=request.form.get('phone'),
            partner_type=", ".join(
                request.form.getlist('partner_type')
            ),
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

        partner = Partner.query.filter_by(
            email=request.form['email']
        ).first()

        if not partner:
            return "Invalid login details"

        if not check_password_hash(
            partner.password,
            request.form['password']
        ):
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
# FORGOT PASSWORD
# -------------------------
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():

    if request.method == 'POST':

        email = request.form.get('email')

        user = Partner.query.filter_by(
            email=email
        ).first()

        if not user:
            return "No account found with that email."

        # Generate token
        token = serializer.dumps(
            email,
            salt='password-reset-salt'
        )

        # Create reset link
        reset_link = url_for(
            'reset_password',
            token=token,
            _external=True
        )

        # TEMPORARY
        # Later you will email this
        return f"""
        <h3>Password Reset Link</h3>

        <p>Copy this link:</p>

        <a href="{reset_link}">
            {reset_link}
        </a>
        """

    return render_template('forgot-password.html')


# -------------------------
# RESET PASSWORD
# -------------------------
@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):

    try:

        email = serializer.loads(
            token,
            salt='password-reset-salt',
            max_age=3600   # link valid for 1 hour
        )

    except:
        return "Reset link expired or invalid."

    user = Partner.query.filter_by(
        email=email
    ).first()

    if not user:
        return "User not found."

    if request.method == 'POST':

        new_password = request.form.get(
            'password',
            ''
        )

        confirm_password = request.form.get(
            'confirm_password',
            ''
        )

        # Match check
        if new_password != confirm_password:
            return "Passwords do not match."

        # Minimum length
        if len(new_password) < 12:
            return (
                "Password must be at least "
                "12 characters long."
            )

        # Uppercase
        if not any(
            c.isupper()
            for c in new_password
        ):
            return (
                "Password needs at least "
                "1 uppercase letter."
            )

        # Lowercase
        if not any(
            c.islower()
            for c in new_password
        ):
            return (
                "Password needs at least "
                "1 lowercase letter."
            )

        # Number
        if not any(
            c.isdigit()
            for c in new_password
        ):
            return (
                "Password needs at least "
                "1 number."
            )

        # Special character
        special = "!@#$%^&*()-_=+[]{}"

        if not any(
            c in special
            for c in new_password
        ):
            return (
                "Password needs at least "
                "1 special character."
            )

        user.password = generate_password_hash(
            new_password
        )

        db.session.commit()

        return redirect(
            url_for('login')
        )

    return render_template(
        'reset-password.html'
    )

# -------------------------
# ADMIN
# -------------------------
@app.route('/admin')
def admin():

    if not admin_required():
        return redirect(url_for('login'))

    partners = Partner.query.all()

    pending = Partner.query.filter_by(
        is_approved=False
    ).all()

    return render_template(
        'admin-dashboard.html',
        partners=partners,
        pending=pending
    )


# -------------------------
# ADMIN ORDERS LIST
# -------------------------
@app.route('/admin/orders')
def admin_orders():

    if not admin_required():
        return redirect(url_for('login'))

    orders = Order.query.order_by(
        Order.created_at.desc()
    ).all()

    return render_template(
        'admin-orders.html',
        orders=orders
    )


# -------------------------
# ADMIN VIEW SINGLE ORDER
# -------------------------
@app.route('/admin/order/<int:id>')
def admin_view_order(id):

    if not admin_required():
        return redirect(url_for('login'))

    order = db.session.get(Order, id)

    if not order:
        return "Order not found"

    return render_template(
        'admin-order-details.html',
        order=order
    )


# -------------------------
# UPDATE ORDER STATUS
# -------------------------
@app.route('/admin/order/<int:id>/update', methods=['POST'])
def update_order_status(id):

    if not admin_required():
        return "Access denied"

    order = db.session.get(Order, id)

    if not order:
        return "Order not found"

    status = request.form.get('status')

    if status not in [
        "pending",
        "processing",
        "completed",
        "rejected"
    ]:
        return "Invalid status"

    order.status = status

    db.session.commit()

    return redirect(url_for('admin_orders'))


# -------------------------
# APPROVE PARTNER
# -------------------------
@app.route('/approve/<int:id>')
def approve(id):

    if not admin_required():
        return "Access denied"

    partner = db.session.get(Partner, id)

    if partner:

        partner.is_approved = True
        partner.is_rejected = False

        db.session.commit()

    return redirect(url_for('admin'))


# -------------------------
# REJECT PARTNER
# -------------------------
@app.route('/reject/<int:id>')
def reject(id):

    if not admin_required():
        return "Access denied"

    partner = db.session.get(Partner, id)

    if partner:

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

    return render_template(
        'partner-dashboard.html',
        partner=partner
    )


# -------------------------
# TERMS AND CONDITIONS
# -------------------------
@app.route('/terms-and-conditions')
def terms_conditions():
    return render_template('terms.html')


# -------------------------
# CREATE ORDER
# -------------------------
@app.route('/create-order', methods=['GET', 'POST'])
def create_order():

    user = current_user()

    if not user:
        return redirect(url_for('login'))

    if request.method == 'POST':

        order = Order(

            partner_id=user.id,

            order_number=request.form.get('order_number'),
            date=request.form.get('date'),

            name=request.form.get('name'),
            phone=request.form.get('phone'),
            dob=request.form.get('dob'),

            frame_make=request.form.get('frame_make'),
            frame_model=request.form.get('frame_model'),
            frame_size=request.form.get('frame_size'),
            frame_color=request.form.get('frame_color'),

            right_sph=request.form.get('right_sph'),
            right_cyl=request.form.get('right_cyl'),
            right_axis=request.form.get('right_axis'),
            right_add=request.form.get('right_add'),
            right_pd=request.form.get('right_pd'),

            left_sph=request.form.get('left_sph'),
            left_cyl=request.form.get('left_cyl'),
            left_axis=request.form.get('left_axis'),
            left_add=request.form.get('left_add'),
            left_pd=request.form.get('left_pd'),

            lens_type=request.form.get('lens_type'),
            coating=request.form.get('coating'),
            tint=request.form.get('tint'),
            base_curve=request.form.get('base_curve'),

            remarks=request.form.get('remarks'),
        )

        db.session.add(order)
        db.session.commit()

        return redirect(url_for('my_orders'))

    return render_template('create-order.html')


# -------------------------
# SERVICES PAGE
# -------------------------
@app.route('/services/<service_name>')
def service_page(service_name):

    services = {

        "eyewear-frames": {
            "title": "Eyewear / Frames",
            "description": "Premium optical frames from top global brands.",
            "images": [
                "frames1.jpg",
                "frames2.jpg",
                "frames3.jpg"
            ]
        },

        "sunglasses": {
            "title": "Sunglasses",
            "description": "Luxury sunglasses for fashion and UV protection.",
            "images": [
                "sunglasses1.jpg",
                "sunglasses2.jpg",
                "sunglasses3.jpg"
            ]
        },

        "contact-lenses": {
            "title": "Contact Lenses",
            "description": "Prescription and cosmetic contact lenses.",
            "images": [
                "lenses1.jpg",
                "lenses2.jpg",
                "lenses3.jpg"
            ]
        },

        "ophthalmic-lenses": {
            "title": "Ophthalmic Lenses",
            "description": "Advanced lenses with premium coatings and protection.",
            "images": [
                "ophthalmic1.jpg",
                "ophthalmic2.jpg",
                "ophthalmic3.jpg"
            ]
        },

        "repairs-adjustments": {
            "title": "Repairs & Adjustments",
            "description": "Professional optical repairs and fittings.",
            "images": [
                "repair1.jpg",
                "repair2.jpg",
                "repair3.jpg"
            ]
        },

        "ophthalmic-machines": {
            "title": "Ophthalmic Machines Consultancy",
            "description": "Modern ophthalmic machines and consultation services.",
            "images": [
                "machine1.jpg",
                "machine2.jpg",
                "machine3.jpg"
            ]
        },

        "accessories": {
            "title": "Accessories",
            "description": "Cases, cleaning kits, tools and optical accessories.",
            "images": [
                "accessory1.jpg",
                "accessory2.jpg",
                "accessory3.jpg"
            ]
        }

    }

    service = services.get(service_name)

    if not service:
        return "Service not found"

    return render_template(
        'service-page.html',
        service=service
    )

# -------------------------
# MY ORDERS
# -------------------------
@app.route('/my-orders')
def my_orders():

    user = current_user()

    if not user:
        return redirect(url_for('login'))

    orders = Order.query.filter_by(
        partner_id=user.id
    ).order_by(
        Order.created_at.desc()
    ).all()

    return render_template(
        'my-orders.html',
        orders=orders
    )


# -------------------------
# PUBLIC PARTNERS
# -------------------------
@app.route('/partners')
def partners():

    approved = Partner.query.filter_by(
        is_approved=True
    ).all()

    return render_template(
        'partners.html',
        partners=approved
    )


# -------------------------
# PARTNER PROFILE
# -------------------------
@app.route('/partner/<int:id>')
def partner_profile(id):

    partner = db.session.get(Partner, id)

    if not partner or not partner.is_approved:
        return "This partner is not available."

    return render_template(
        'partner-profile.html',
        partner=partner
    )


# -------------------------
# RUN
# -------------------------
if __name__ == '__main__':
    app.run(debug=True)