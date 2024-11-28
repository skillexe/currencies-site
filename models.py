from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    currency = db.Column(db.String(10), nullable=False)
    target_rate = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<Subscription {self.email}, {self.currency}, {self.target_rate}>"
