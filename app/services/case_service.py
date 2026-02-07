import threading
import os
from app.models.case import Citation
from flask import current_app, json
from app.extensions import db
from app.models.case import Case, Document
from ultis.ai_summary import generate_master_summary_with_citations, summarize_document_content
from ultis.ocr import ContentExtractionService
from ultis.storage import StorageService
from sqlalchemy.orm import joinedload

# Khởi tạo một lần ở cấp module hoặc trong CaseService
extractor = ContentExtractionService()

class CaseService:
    @staticmethod
    def create_case(title, files):
        try:
            # 1. Khởi tạo Case
            new_case = Case(title=title, status="PROCESSING")
            db.session.add(new_case)
            db.session.flush()

            for file in files:
                # 2. Lưu file vật lý dùng StorageService
                rel_path = StorageService.save_file(new_case.id, file)
                
                # 3. Lưu bản ghi Document
                doc = Document(
                    case_id=new_case.id, 
                    file_name=file.filename, 
                    file_url=rel_path,
                    status="UPLOADED"
                )
                db.session.add(doc)

            db.session.commit()

            # 4. Kích hoạt OCR chạy ngầm
            app = current_app._get_current_object()
            threading.Thread(
                target=CaseService._run_background_ocr, 
                args=(app, new_case.id)
            ).start()

            return new_case
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def _run_background_ocr(app, case_id):
        with app.app_context():
            case = Case.query.get(case_id)
            if not case: return
            upload_base = app.config['UPLOAD_FOLDER']
            
            for doc in case.documents:
                full_path = os.path.join(upload_base, doc.file_url)
                # Thực hiện bóc tách nội dung
                content_pages = extractor.extract_content(full_path)
                
                if content_pages:
                    doc.raw_content = content_pages
                    # 2. Dùng OpenAI để tóm tắt từ Raw Content đó
                    summary_text = summarize_document_content(content_pages)
                    if summary_text:
                        doc.summary = summary_text
                    doc.status = "SUCCESS"
                else:
                    doc.status = "FAILED"
                db.session.commit()
            print("🔗 Generating Master Summary...")
            CaseService.create_master_summary(case_id)
            case.status = "COMPLETED"
            db.session.commit()

    @staticmethod
    def get_all_cases():
        """Lấy danh sách rút gọn các vụ án"""
        return Case.query.order_by(Case.created_at.desc()).all()

    @staticmethod
    def get_case_by_id(case_id):
        """Lấy chi tiết một vụ án kèm theo Citations và Documents"""
        return Case.query.options(
            joinedload(Case.citations).joinedload(Citation.document),
            joinedload(Case.documents)
        ).filter_by(id=case_id).first()
    
    @staticmethod
    def create_master_summary(case_id):
        case = Case.query.get(case_id)
        if not case: return

        # 1. Chuẩn bị dữ liệu đầu vào từ các file đã xử lý xong
        doc_summaries = []
        for doc in case.documents:
            if doc.summary:
                doc_summaries.append({
                    "id": str(doc.id),
                    "name": doc.file_name,
                    "summary": doc.summary
                })

        # 2. Gọi OpenAI tạo summary
        ai_result_raw = generate_master_summary_with_citations(doc_summaries)
        if not ai_result_raw: return
        
        ai_data = json.loads(ai_result_raw)
        
        # 3. Cập nhật Master Summary cho Case
        # Thay thế mã [ref: uuid] thành [1], [2] để Frontend hiển thị đẹp
        final_summary = ai_data['summary']
        doc_id_map = {doc['id']: i+1 for i, doc in enumerate(doc_summaries)}
        
        # Xóa các citation cũ (nếu có) trước khi tạo mới
        Citation.query.filter_by(case_id=case_id).delete()

        # 4. Lưu Citations vào DB
        for idx, doc_id in enumerate(ai_data.get('citations', [])):
            new_citation = Citation(
                case_id=case_id,
                document_id=doc_id,
                citation_index=idx + 1 # Số thứ tự hiển thị [1], [2]...
            )
            db.session.add(new_citation)
            
            # (Tùy chọn) Re-format mã trích dẫn trong text từ UUID sang [index]
            final_summary = final_summary.replace(f"[ref: {doc_id}]", f"[{idx + 1}]")

        case.master_summary = final_summary
        case.status = "COMPLETED"
        db.session.commit()