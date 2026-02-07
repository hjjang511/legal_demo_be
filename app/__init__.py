from flask import Flask, send_from_directory
from flask_cors import CORS

from app.core.config import Config
from app.extensions import db, migrate

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 1. Khởi tạo Extensions
    CORS(app)
    db.init_app(app)
    migrate.init_app(app, db)

    from app.api import api_bp
    app.register_blueprint(api_bp)

    # 3. Route để phục vụ file tĩnh (Xem tài liệu đã upload)
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    return app