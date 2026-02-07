from app import create_app
from app.extensions import db
# Khởi tạo instance của Flask từ Application Factory
app = create_app()

with app.app_context():
    db.create_all()
    print("Database tables created successfully!")

if __name__ == "__main__":
    # Chạy server ở chế độ debug để tự động reload khi sửa code
    # Port mặc định là 5000
    app.run(host="0.0.0.0", port=5000, debug=True)