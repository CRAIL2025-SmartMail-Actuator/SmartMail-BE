from app import db
from datetime import datetime


class Email(db.Model):
    __tablename__ = "emails"

    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.Text)
    body = db.Column(db.Text)
    category = db.Column(db.String(50))
    received_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    message_id = db.Column(db.String(255), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "sender": self.sender,
            "subject": self.subject,
            "body": self.body,
            "category": self.category,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "processed_at": self.processed_at.isoformat()
            if self.processed_at
            else None,
            "message_id": self.message_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
