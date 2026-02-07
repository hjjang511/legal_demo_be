# import uuid
# import time
# from flask import current_app
# from qdrant_client import QdrantClient
# from qdrant_client.http import models
# import re

# from app.ultis.model_ultis import get_openai_client

# # OpenAI text-embedding-3-small dùng 1536. 
# # Nếu bạn dùng text-embedding-3-large có thể lên tới 3072.
# VECTOR_SIZE = 1536 

# def get_qdrant_client():
#     url = current_app.config.get('QDRANT_URL')
#     api_key = current_app.config.get('QDRANT_API_KEY')
#     if url.startswith("http://"):
#         return QdrantClient(url=url) 
#     return QdrantClient(url=url, api_key=api_key)

# def get_collection_name(bot_id):
#     return f"id_{bot_id}"

# def ensure_collection_exists(collection_name):
#     client = get_qdrant_client()
#     if not client.collection_exists(collection_name=collection_name):
#         client.create_collection(
#             collection_name=collection_name,
#             vectors_config=models.VectorParams(
#                 size=VECTOR_SIZE, 
#                 distance=models.Distance.COSINE
#             )
#         )
#     try:
#         client.create_payload_index(
#             collection_name=collection_name,
#             field_name="url",
#             field_schema=models.PayloadSchemaType.KEYWORD
#         )
#     except Exception:
#         pass

# def get_batch_embeddings(texts):
#     """
#     Tạo vector cho danh sách text bằng OpenAI
#     """
#     client = get_openai_client()
    
#     try:
#         response = client.embeddings.create(
#             input=texts,
#             model="text-embedding-3-small"
#         )
#         # Lấy danh sách embedding theo đúng thứ tự
#         return [data.embedding for data in response.data]
#     except Exception as e:
#         print(f"⚠️ Error embedding batch with OpenAI: {e}")
#         raise e

# def chunk_text(text, chunk_size=1000, overlap=100):
#     # (Giữ nguyên logic chunking của bạn vì nó xử lý text thuần túy)
#     if not text: return []
#     sentences = re.split(r'(?<=[.?!])\s+', text)
#     if not sentences: sentences = text.split('\n')
#     chunks = []; current_chunk = []; current_len = 0
#     for sentence in sentences:
#         sentence = sentence.strip()
#         if not sentence: continue
#         sent_len = len(sentence)
#         if current_len + sent_len <= chunk_size:
#             current_chunk.append(sentence)
#             current_len += sent_len + 1
#         else:
#             if current_chunk: chunks.append(" ".join(current_chunk))
#             overlap_buffer = []; overlap_len = 0
#             for s in reversed(current_chunk):
#                 if overlap_len + len(s) < overlap:
#                     overlap_buffer.insert(0, s)
#                     overlap_len += len(s) + 1
#                 else: break
#             current_chunk = list(overlap_buffer)
#             current_len = overlap_len
#             if sent_len > chunk_size:
#                 current_chunk.append(sentence)
#                 chunks.append(" ".join(current_chunk))
#                 current_chunk = []; current_len = 0
#             else:
#                 current_chunk.append(sentence)
#                 current_len += sent_len + 1
#     if current_chunk: chunks.append(" ".join(current_chunk))
#     return chunks

# def upload_knowledge_to_qdrant(bot_id, full_text, url):
#     try:
#         collection_name = get_collection_name(bot_id)
#         ensure_collection_exists(collection_name)
#         client = get_qdrant_client()

#         # Clean old data
#         try:
#             client.delete(
#                 collection_name=collection_name,
#                 points_selector=models.FilterSelector(
#                     filter=models.Filter(
#                         must=[models.FieldCondition(key="url", match=models.MatchValue(value=url))]
#                     )
#                 )
#             )
#         except Exception: pass

#         chunks = chunk_text(full_text)
#         if not chunks: return False

#         # OpenAI Embedding
#         embeddings = get_batch_embeddings(chunks)

#         points = []
#         for i, chunk in enumerate(chunks):
#             points.append(models.PointStruct(
#                 id=str(uuid.uuid4()),
#                 vector=embeddings[i],
#                 payload={
#                     "text_content": chunk,
#                     "url": url,
#                     "created_at": int(time.time())
#                 },
#             ))

#         client.upsert(collection_name=collection_name, points=points, wait=True)
#         return True
#     except Exception as e:
#         print(f"❌ Error: {e}")
#         return False

# def search_knowledge(bot_id, query_text, file_urls=None, limit=5, score_threshold=0.35):
#     """
#     Tìm kiếm vector và trả về cả Content lẫn URL nguồn.
#     Args:
#         file_urls (list): Danh sách URL cần lọc (VD: ['https://a.pdf', 'https://b.docx'])
#     """
#     client = get_qdrant_client()
#     openai_client = get_openai_client()
#     collection_name = get_collection_name(bot_id)

#     if not client.collection_exists(collection_name):
#         return []

#     try:
#         # Embed câu hỏi
#         response = openai_client.embeddings.create(
#             input=[query_text],
#             model="text-embedding-3-small"
#         )
#         query_vector = response.data[0].embedding
#     except Exception as e:
#         print(f"Error embedding query: {e}")
#         return []
    
#     # Tạo bộ lọc (nếu user chỉ định file_urls)
#     search_filter = None
#     if file_urls and isinstance(file_urls, list) and len(file_urls) > 0:
#         search_filter = models.Filter(
#             must=[
#                 models.FieldCondition(
#                     key="url",
#                     match=models.MatchAny(any=file_urls)
#                 )
#             ]
#         )

#     # Tìm kiếm
#     search_result = client.query_points(
#         collection_name=collection_name,
#         query=query_vector,
#         limit=limit,
#         score_threshold=score_threshold,
#         query_filter=search_filter
#     )

#     # --- [SỬA ĐỔI QUAN TRỌNG] ---
#     results = []
#     for point in search_result.points:
#         if point.payload:
#             results.append({
#                 "content": point.payload.get("text_content", ""),
#                 "source_url": point.payload.get("url", "Unknown Source")
#             })
            
#     return results

# def delete_knowledge_from_qdrant(bot_id, url):
#     try:
#         collection_name = get_collection_name(bot_id)
#         client = get_qdrant_client()
#         client.delete(
#             collection_name=collection_name,
#             points_selector=models.FilterSelector(
#                 filter=models.Filter(
#                     must=[models.FieldCondition(key="url", match=models.MatchValue(value=url))]
#                 )
#             )
#         )
#         return True
#     except Exception as e:
#         print(f"❌ Error deleting knowledge: {e}")
#         return False
    
# def get_all_content(bot_id, file_urls=None):
#     """
#     Lấy toàn bộ nội dung từ vector DB, có filter theo URL nếu cần.
#     Trả về list dict để đồng bộ format với hàm search_knowledge.
#     """
#     try:
#         collection_name = get_collection_name(bot_id)
#         client = get_qdrant_client()
        
#         if not client.collection_exists(collection_name):
#             return []

#         # Tạo bộ lọc nếu file_urls được cung cấp
#         search_filter = None
#         if file_urls and isinstance(file_urls, list) and len(file_urls) > 0:
#             search_filter = models.Filter(
#                 must=[
#                     models.FieldCondition(
#                         key="url",
#                         match=models.MatchAny(any=file_urls)
#                     )
#                 ]
#             )

#         result = []
#         # Lưu ý: scroll chỉ lấy mặc định số lượng nhất định, 
#         # nếu dữ liệu lớn cần vòng lặp while với next_page_offset. 
#         # Ở đây tạm để limit=1000 cho đơn giản theo code cũ.
#         scroll_result = client.scroll(
#             collection_name=collection_name,
#             limit=1000, 
#             with_payload=True,
#             scroll_filter=search_filter
#         )

#         # Trích xuất dữ liệu chuẩn format
#         for point in scroll_result[0]: # scroll trả về (points, offset)
#             if point.payload and "text_content" in point.payload:
#                 result.append({
#                     "content": point.payload.get("text_content", ""),
#                     "source_url": point.payload.get("url", "Unknown Source")
#                 })

#         return result
#     except Exception as e:
#         print(f"❌ Error getting all content: {e}")
#         return []
    
# def delete_collection_from_qdrant(bot_id):
#     try:
#         collection_name = get_collection_name(bot_id)
#         client = get_qdrant_client()
#         client.delete_collection(collection_name=collection_name)
#         return True
#     except Exception as e:
#         print(f"❌ Error deleting collection: {e}")
#         return False