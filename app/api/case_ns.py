from flask import request
from flask_restx import Namespace, Resource, fields
from werkzeug.datastructures import FileStorage
from app.services.case_service import CaseService

case_ns = Namespace('cases', description='Quản lý hồ sơ vụ án và tài liệu trích dẫn')

# 1. Định nghĩa Models cho Swagger UI (Response Documentation)
document_model = case_ns.model('Document', {
    'id': fields.String(example='uuid-string'),
    'file_name': fields.String(example='hop_dong_mua_ban.pdf'),
    'status': fields.String(example='SUCCESS'),
    'file_url': fields.String(example='/uploads/case_id/file.pdf')
})

citation_model = case_ns.model('Citation', {
    'id': fields.Integer(example=1),
    'document_id': fields.String(example='uuid-string'),
    'file_name': fields.String(example='hop_dong_mua_ban.pdf'),
    'page_number': fields.Integer(example=1),
    'citation_index': fields.Integer(example=1)
})

case_detail_model = case_ns.model('CaseDetail', {
    'id': fields.String(example='uuid-string'),
    'title': fields.String(example='Tranh chấp hợp đồng bất động sản'),
    'master_summary': fields.String(example='Nội dung tổng hợp có trích dẫn [1]...'),
    'status': fields.String(example='COMPLETED'),
    'created_at': fields.DateTime(),
    'citations': fields.List(fields.Nested(citation_model)),
    'documents': fields.List(fields.Nested(document_model))
})

upload_parser = case_ns.parser()
upload_parser.add_argument('title', type=str, required=True, help='Tiêu đề vụ án', location='form')
upload_parser.add_argument('files', type=FileStorage, location='files', required=True, action='append', help='Danh sách file hồ sơ')

@case_ns.route('')
class CaseList(Resource):
    @case_ns.doc('list_cases')
    @case_ns.marshal_list_with(case_ns.model('CaseList', {
        'id': fields.String(),
        'title': fields.String(),
        'status': fields.String(),
        'created_at': fields.DateTime()
    }))
    def get(self):
        """Lấy danh sách tất cả vụ án"""
        return CaseService.get_all_cases()

    @case_ns.doc('create_case', responses={201: 'Created', 400: 'Validation Error'})
    @case_ns.expect(upload_parser, validate=True) # Thêm validate=True ở đây
    def post(self):
        """Tạo vụ án mới và tải lên tài liệu"""
        # Sử dụng parse_args từ parser thay vì request.form trực tiếp
        args = upload_parser.parse_args()
        
        title = args.get('title')
        files = args.get('files')
        
        # Kiểm tra thủ công nếu parser bypass (hiếm gặp)
        if not title or not files:
            case_ns.abort(400, "Thiếu Tiêu đề hoặc File đính kèm")
            
        new_case = CaseService.create_case(title, files)
        return {"id": str(new_case.id), "message": "Khởi tạo thành công"}, 20

@case_ns.route('/<uuid:case_id>')
@case_ns.param('case_id', 'ID định danh duy nhất của vụ án')
@case_ns.response(404, 'Không tìm thấy hồ sơ')
class CaseDetail(Resource):
    @case_ns.doc('get_case_detail')
    @case_ns.marshal_with(case_detail_model)
    def get(self, case_id):
        """Lấy chi tiết vụ án (Gồm nội dung tổng hợp và trích dẫn)"""
        case = CaseService.get_case_by_id(case_id)
        if not case:
            case_ns.abort(404, f"Case {case_id} không tồn tại")
        
        # Ở đây ta có thể dùng marshal_with của restx hoặc schema.dump của marshmallow
        return case, 200

@case_ns.route('/<uuid:case_id>/documents')
@case_ns.param('case_id', 'ID định danh của vụ án')
class CaseDocuments(Resource):
    @case_ns.doc('get_case_documents')
    @case_ns.marshal_list_with(document_model)
    def get(self, case_id):
        """Lấy danh sách tài liệu gốc thuộc vụ án"""
        case = CaseService.get_case_by_id(case_id)
        if not case:
            case_ns.abort(404, "Không tìm thấy hồ sơ")
        return case.documents, 200