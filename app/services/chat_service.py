from app.extensions import db, qdrant_client, openai_client
from app.models.chat import ChatSession, Message
from app.core.config import Config
from qdrant_client.http import models as qmodels
import json

class ChatService:
    
    @staticmethod
    def get_embedding(text):
        response = openai_client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding

    @staticmethod
    def create_session(case_id, title=None):
        session = ChatSession(case_id=case_id, title=title or "New Chat")
        db.session.add(session)
        db.session.commit()
        return session

    @staticmethod
    def send_message(session_id, content):
        session = ChatSession.query.get(session_id)
        if not session:
            raise ValueError("Session not found")

        # 1. Save User Message
        user_msg = Message(session_id=session_id, role='user', content=content)
        db.session.add(user_msg)
        
        # 2. Vector Search (RAG)
        query_vector = ChatService.get_embedding(content)
        
        # IMPORTANT: Filter by CaseID to prevent data leak between cases
        search_result = qdrant_client.search(
            collection_name=Config.QDRANT_COLLECTION,
            query_vector=query_vector,
            limit=5,
            query_filter=qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="caseId",
                        match=qmodels.MatchValue(value=str(session.case_id))
                    )
                ]
            )
        )

        # 3. Construct Context & Citations
        context_text = ""
        citations = []
        
        for hit in search_result:
            payload = hit.payload
            snippet = payload.get('content', '')
            context_text += f"Document: {payload.get('fileName')}\nContent: {snippet}\n\n"
            
            citations.append({
                "docId": payload.get('docId'),
                "fileName": payload.get('fileName'),
                "content": snippet[:200] + "...", # Preview
                "page": payload.get('page')
            })

        # 4. LLM Generation
        system_prompt = f"""You are a Legal AI Assistant. Use the following context to answer the user's question. 
        If the answer is not in the context, say so. 
        Context: 
        {context_text}"""

        completion = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content}
            ]
        )
        
        bot_response_text = completion.choices[0].message.content

        # 5. Save Bot Message
        bot_msg = Message(
            session_id=session_id, 
            role='bot', 
            content=bot_response_text,
            citations=citations
        )
        db.session.add(bot_msg)
        db.session.commit()

        return bot_msg