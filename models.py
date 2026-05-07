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

    # 🔗 Relationship (optional but useful)
    orders = db.relationship('Order', backref='partner', lazy=True)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    partner_id = db.Column(db.Integer, db.ForeignKey('partner.id'), nullable=False)

    # Client Info
    order_number = db.Column(db.String(100))
    date = db.Column(db.String(50))
    name = db.Column(db.String(100))
    phone = db.Column(db.String(50))
    dob = db.Column(db.String(50))

    # Prescription (Right)
    right_sph = db.Column(db.String(20))
    right_cyl = db.Column(db.String(20))
    right_axis = db.Column(db.String(20))
    right_add = db.Column(db.String(20))

    pd = db.Column(db.String(20))

    # Prescription (Left)
    left_sph = db.Column(db.String(20))
    left_cyl = db.Column(db.String(20))
    left_axis = db.Column(db.String(20))
    left_add = db.Column(db.String(20))

    pd = db.Column(db.String(20))

    # Frame details
    frame_make = db.Column(db.String(100))
    frame_model = db.Column(db.String(100))
    frame_shape = db.Column(db.String(100))
    tint = db.Column(db.String(100))

    # Lens
    lens_type = db.Column(db.String(100))
    coating = db.Column(db.String(100))
    base_curve = db.Column(db.String(100))

    status = db.Column(db.String(20), default="pending")