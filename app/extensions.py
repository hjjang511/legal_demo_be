from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from qdrant_client import QdrantClient
from openai import OpenAI
from app.core.config import Config


db = SQLAlchemy()
migrate = Migrate()

# Lazy loading clients
qdrant_client = QdrantClient(url=Config.QDRANT_URL, api_key=Config.QDRANT_API_KEY)
openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)