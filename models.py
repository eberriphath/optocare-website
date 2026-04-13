from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Partner(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)

    store_name = db.Column(db.String(100))
    location = db.Column(db.String(200))
    phone = db.Column(db.String(50))
    services = db.Column(db.Text)
    partner_type = db.Column(db.String(100))
    is_rejected = db.Column(db.Boolean, default=False)

    document = db.Column(db.String(200))

    is_approved = db.Column(db.Boolean, default=False)
    is_rejected = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Partner {self.email}>'