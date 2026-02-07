import uuid
from datetime import datetime
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db

class Case(db.Model):
    __tablename__ = 'cases'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.String(255), nullable=False)
    master_summary = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default="PENDING")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Dùng back_populates thay cho backref để đồng bộ và tường minh
    documents = db.relationship('Document', back_populates='case', cascade="all, delete-orphan")
    citations = db.relationship('Citation', back_populates='case', cascade="all, delete-orphan")

class Document(db.Model):
    __tablename__ = 'documents'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = db.Column(UUID(as_uuid=True), db.ForeignKey('cases.id'), nullable=False)
    file_url = db.Column(db.String(500), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    label = db.Column(db.String(100), nullable=True)
    summary = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default="PENDING")
    # THÊM TRƯỜNG NÀY ĐỂ LƯU KẾT QUẢ OCR THEO TRANG
    raw_content = db.Column(JSON, nullable=True)
    # BỔ SUNG: Khai báo để SQLAlchemy nhận diện được property 'citations' và 'case'
    case = db.relationship('Case', back_populates='documents')
    citations = db.relationship('Citation', back_populates='document', cascade="all, delete-orphan")

class Citation(db.Model):
    __tablename__ = 'citations'

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(UUID(as_uuid=True), db.ForeignKey('cases.id'), nullable=False)
    document_id = db.Column(UUID(as_uuid=True), db.ForeignKey('documents.id'), nullable=False)
    
    page_number = db.Column(db.Integer, nullable=True)
    snippet = db.Column(db.Text, nullable=True) 
    citation_index = db.Column(db.Integer)

    case = db.relationship('Case', back_populates='citations')
    document = db.relationship('Document', back_populates='citations')