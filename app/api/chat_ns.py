from flask_restx import Namespace, Resource, fields
from flask import request
from app.services.chat_service import ChatService

api = Namespace('chat', description='RAG Chat Operations')

# DTOs
citation_model = api.model('Citation', {
    'docId': fields.String,
    'fileName': fields.String,
    'page': fields.Integer,
    'content': fields.String
})

message_model = api.model('Message', {
    'id': fields.String,
    'role': fields.String,
    'content': fields.String,
    'citations': fields.List(fields.Nested(citation_model)),
    'timestamp': fields.DateTime
})

chat_input_model = api.model('ChatInput', {
    'content': fields.String(required=True)
})

@api.route('/session/<string:case_id>')
class ChatSessionCreate(Resource):
    def post(self, case_id):
        """Create a new chat session for a case"""
        session = ChatService.create_session(case_id)
        return {'sessionId': str(session.id), 'caseId': str(session.case_id)}

@api.route('/<string:session_id>/message')
class ChatMessage(Resource):
    @api.marshal_with(message_model)
    @api.expect(chat_input_model)
    def post(self, session_id):
        """Send a message to the bot (RAG)"""
        data = request.json
        msg = ChatService.send_message(session_id, data['content'])
        return msg

@api.route('/<string:session_id>/history')
class ChatHistory(Resource):
    @api.marshal_list_with(message_model)
    def get(self, session_id):
        """Get chat history"""
        from app.models.chat import ChatSession
        session = ChatSession.query.get_or_404(session_id)
        return session.messages

@api.route('/tts')
class TextToSpeech(Resource):
    def post(self):
        """Simple wrapper for TTS (OpenAI Audio API)"""
        data = request.json
        text = data.get('text')
        # Implementation of OpenAI TTS API call here
        # Return audio stream or URL
        return {"message": "TTS Placeholder"}