import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.extensions import db

class ChatSession(db.Model):
    __tablename__ = 'chat_sessions'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = db.Column(UUID(as_uuid=True), db.ForeignKey('cases.id'), nullable=False)
    title = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    messages = db.relationship('Message', backref='session', lazy=True, order_by="Message.timestamp")

class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = db.Column(UUID(as_uuid=True), db.ForeignKey('chat_sessions.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'user' or 'bot'
    content = db.Column(db.Text, nullable=False)
    citations = db.Column(JSONB, nullable=True) # Array of {docId, fileName, content, page}
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)