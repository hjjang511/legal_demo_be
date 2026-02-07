import os
from werkzeug.utils import secure_filename
from flask import current_app

class StorageService:
    @staticmethod
    def save_file(case_id, file):
        filename = secure_filename(file.filename)
        # Format: case_id/filename để dễ quản lý
        relative_path = os.path.join(str(case_id), filename)
        full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], relative_path)
        
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        file.save(full_path)
        return relative_path # Lưu path tương đối vào DB