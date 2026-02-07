from flask import Blueprint
from flask_restx import Api

from app.api.case_ns import case_ns

# # Import các namespace bạn đã định nghĩa
# from app.api.chat_ns import chat_ns

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

api = Api(
    api_bp,
    title='Legal RAG API',
    version='1.0',
    description='Legal Assistant Backend - AI Case Summary & Citations',
    doc='/docs' # Đường dẫn xem Swagger UI: /api/v1/docs
)

# Thêm các namespace vào instance Api
api.add_namespace(case_ns, path='/cases')
# api.add_namespace(chat_ns, path='/chat')