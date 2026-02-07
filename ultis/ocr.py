import base64
import os
import io
import requests
import time
from docx import Document as DocxDocument
from mistralai import Mistral

class ContentExtractionService:
    def __init__(self):
        # Khởi tạo client một lần duy nhất để tối ưu hiệu năng
        self.mistral_client = Mistral(api_key=os.environ.get("MISTRAL_API_KEY"))
        self.ocr_model = "mistral-ocr-latest"

    def _encode_to_base64(self, file_path):
        """Helper: Chuyển file sang Data URI Base64"""
        with open(file_path, "rb") as f:
            encoded_string = base64.b64encode(f.read()).decode('utf-8')
        
        ext = file_path.split('.')[-1].lower()
        mime_type = "application/pdf" if ext == 'pdf' else f"image/{ext}"
        return f"data:{mime_type};base64,{encoded_string}"

    def process_mistral_ocr(self, file_path, retries=2):
        """Xử lý OCR qua Mistral với cơ chế thử lại (Retry)"""
        try:
            data_uri = self._encode_to_base64(file_path)
            
            for attempt in range(retries + 1):
                try:
                    ocr_response = self.mistral_client.ocr.process(
                        model=self.ocr_model,
                        document={"type": "document_url", "document_url": data_uri}
                    )
                    return [{"page": i + 1, "content": p.markdown} for i, p in enumerate(ocr_response.pages)]
                except Exception as e:
                    if attempt < retries:
                        time.sleep(2) # Nghỉ 2s trước khi thử lại (Xử lý Rate Limit tạm thời)
                        continue
                    raise e
        except Exception as e:
            print(f"❌ Mistral OCR Error [{os.path.basename(file_path)}]: {e}")
            return None

    def process_native_text(self, file_path):
        """Xử lý đọc file text/docx trực tiếp từ ổ cứng (không dùng requests)"""
        try:
            ext = file_path.split('.')[-1].lower()
            if ext == 'docx':
                doc = DocxDocument(file_path)
                text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
            else:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
            return [{"page": 1, "content": text}]
        except Exception as e:
            print(f"❌ Native Text Error [{os.path.basename(file_path)}]: {e}")
            return None

    def extract_content(self, file_path):
        """Router chính: Nhận đường dẫn file cục bộ và điều hướng xử lý"""
        if not os.path.exists(file_path):
            return None

        ext = file_path.split('.')[-1].lower()
        
        # Nhóm xử lý OCR (File nặng/Ảnh)
        if ext in ['pdf', 'jpg', 'jpeg', 'png', 'webp']:
            return self.process_mistral_ocr(file_path)
        
        # Nhóm xử lý Native (File văn bản)
        elif ext in ['docx', 'txt', 'md']:
            return self.process_native_text(file_path)
            
        return None