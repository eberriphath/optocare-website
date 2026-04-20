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