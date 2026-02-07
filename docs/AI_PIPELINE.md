# AI Processing Pipeline - Chi Tiết Thiết Kế

## 1. TỔNG QUAN AI PIPELINE

### 1.1 Các Thành Phần Chính

```
┌─────────────────────────────────────────────────────────────┐
│                      DOCUMENT UPLOAD                         │
└─────────────┬───────────────────────────────────────────────┘
              │
    ┌─────────↓──────────┐
    │ 1. VALIDATION      │
    │ - File type check  │
    │ - File size check  │
    │ - Virus scan       │
    └─────────┬──────────┘
              │
    ┌─────────↓──────────────────────┐
    │ 2. STORAGE & INDEXING          │
    │ - Save to S3                   │
    │ - Record in DB                 │
    │ - Publish to MQ                │
    └─────────┬──────────────────────┘
              │
    ┌─────────↓──────────────────────┐
    │ 3. OCR & TEXT EXTRACTION       │
    │ - PyTorch/Tesseract            │
    │ - Extract raw text             │
    │ - Detect language              │
    │ - Calculate confidence         │
    └─────────┬──────────────────────┘
              │
    ┌─────────↓──────────────────────┐
    │ 4. NLP PROCESSING              │
    │ - Entity extraction             │
    │ - Key term identification       │
    │ - Language understanding        │
    └─────────┬──────────────────────┘
              │
    ┌─────────↓──────────────────────┐
    │ 5. SUMMARIZATION               │
    │ - Extractive summary            │
    │ - Abstractive summary           │
    │ - Section identification        │
    └─────────┬──────────────────────┘
              │
    ┌─────────↓──────────────────────┐
    │ 6. EMBEDDING GENERATION        │
    │ - Vector embedding              │
    │ - Semantic representation       │
    │ - Store in vector DB            │
    └─────────┬──────────────────────┘
              │
    ┌─────────↓──────────────────────┐
    │ 7. INDEXING                    │
    │ - Elasticsearch indexing        │
    │ - Full-text search ready        │
    └─────────┬──────────────────────┘
              │
    ┌─────────↓──────────────────────┐
    │ UPDATE DATABASE & NOTIFY       │
    │ - Mark as COMPLETED             │
    │ - Notify user                   │
    └─────────────────────────────────┘
```

---

## 2. OCR & TEXT EXTRACTION SERVICE

### 2.1 Technology Stack

```python
# Requirements
pytesseract==0.3.10  # OCR engine
pdf2image==1.16.3    # PDF to image conversion
Pillow==9.5.0        # Image processing
opencv-python==4.7.0 # Computer vision
python-docx==0.8.11  # DOCX parsing
pdfplumber==0.9.0    # PDF extraction
PyPDF2==3.14.0       # PDF manipulation
langdetect==1.0.9    # Language detection
```

### 2.2 OCR Service Implementation

```python
# services/ocr_service.py

import asyncio
import logging
from typing import Optional, Dict, List
from pathlib import Path
import tempfile
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
import cv2
import numpy as np
from langdetect import detect, DetectorFactory
import pdfplumber

DetectorFactory.seed = 0

class OCRService:
    def __init__(self, language: str = 'vie+eng'):
        self.language = language
        self.supported_formats = {
            'pdf': self._process_pdf,
            'docx': self._process_docx,
            'png': self._process_image,
            'jpg': self._process_image,
            'jpeg': self._process_image,
            'txt': self._process_text,
            'doc': self._process_doc
        }

    async def process_document(
        self,
        file_path: str,
        file_type: str,
        enable_preprocessing: bool = True
    ) -> Dict:
        """
        Process document and extract text
        
        Returns:
        {
            'raw_content': str,
            'page_count': int,
            'language': str,
            'confidence': float,
            'pages': [
                {
                    'page_number': int,
                    'content': str,
                    'confidence': float,
                    'dimensions': {'width', 'height'}
                }
            ],
            'processing_time': float,
            'error': str or None
        }
        """
        try:
            file_type = file_type.lower().strip('.')
            
            if file_type not in self.supported_formats:
                return {
                    'success': False,
                    'error': f'Unsupported file type: {file_type}'
                }
            
            processor = self.supported_formats[file_type]
            return await processor(file_path, enable_preprocessing)
            
        except Exception as e:
            logging.error(f"OCR processing error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _process_pdf(
        self,
        file_path: str,
        enable_preprocessing: bool
    ) -> Dict:
        """Process PDF files"""
        pages_data = []
        all_text = []
        
        with pdfplumber.open(file_path) as pdf:
            page_count = len(pdf.pages)
            
            for page_idx, page in enumerate(pdf.pages):
                # Try pdfplumber text extraction first (faster, more accurate for digital PDFs)
                text = page.extract_text()
                
                # If no text extracted and it's scanned PDF, use OCR
                if not text or len(text.strip()) < 10:
                    # Convert to image and perform OCR
                    images = convert_from_path(
                        file_path,
                        first_page=page_idx + 1,
                        last_page=page_idx + 1
                    )
                    
                    if images:
                        image = images[0]
                        text, confidence = await self._image_to_text(
                            image,
                            enable_preprocessing
                        )
                else:
                    confidence = 0.95  # High confidence for digital text

                pages_data.append({
                    'page_number': page_idx + 1,
                    'content': text,
                    'confidence': confidence,
                    'dimensions': {
                        'width': page.width,
                        'height': page.height
                    }
                })
                
                all_text.append(text)

        # Detect language
        combined_text = '\n'.join(all_text)
        language = self._detect_language(combined_text)
        avg_confidence = np.mean([p['confidence'] for p in pages_data])

        return {
            'success': True,
            'raw_content': combined_text,
            'page_count': page_count,
            'language': language,
            'confidence': float(avg_confidence),
            'pages': pages_data
        }

    async def _process_image(
        self,
        file_path: str,
        enable_preprocessing: bool
    ) -> Dict:
        """Process image files (PNG, JPG, etc.)"""
        image = Image.open(file_path)
        
        text, confidence = await self._image_to_text(image, enable_preprocessing)
        language = self._detect_language(text)

        return {
            'success': True,
            'raw_content': text,
            'page_count': 1,
            'language': language,
            'confidence': confidence,
            'pages': [{
                'page_number': 1,
                'content': text,
                'confidence': confidence,
                'dimensions': {
                    'width': image.width,
                    'height': image.height
                }
            }]
        }

    async def _image_to_text(
        self,
        image: Image,
        enable_preprocessing: bool
    ) -> tuple:
        """Convert image to text using Tesseract"""
        
        # Preprocessing for better OCR results
        if enable_preprocessing:
            image = self._preprocess_image(image)

        # OCR
        text = pytesseract.image_to_string(image, lang=self.language)
        
        # Get detailed info including confidence
        data = pytesseract.image_to_data(image, lang=self.language)
        
        # Calculate average confidence
        lines = data.split('\n')[1:]  # Skip header
        confidences = []
        for line in lines:
            parts = line.split('\t')
            if len(parts) >= 11:
                try:
                    conf = int(parts[10])
                    if conf >= 0:  # -1 means no text in region
                        confidences.append(conf / 100.0)
                except (ValueError, IndexError):
                    pass

        avg_confidence = np.mean(confidences) if confidences else 0.0

        return text, float(avg_confidence)

    def _preprocess_image(self, image: Image) -> Image:
        """Apply preprocessing to improve OCR accuracy"""
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Convert to numpy array for OpenCV
        img_array = np.array(image)
        
        # Grayscale
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray, h=10)
        
        # Threshold (binarization) for scanned documents
        _, binary = cv2.threshold(denoised, 150, 255, cv2.THRESH_BINARY)
        
        # Dilation & erosion to clean up
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        processed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        # Upscale if image is small (improves OCR)
        height, width = processed.shape
        if width < 1000:
            scale = 1000 / width
            processed = cv2.resize(
                processed,
                None,
                fx=scale,
                fy=scale,
                interpolation=cv2.INTER_CUBIC
            )

        return Image.fromarray(processed)

    async def _process_docx(self, file_path: str, **kwargs) -> Dict:
        """Process DOCX files"""
        from docx import Document
        
        doc = Document(file_path)
        text_parts = []
        
        for paragraph in doc.paragraphs:
            text_parts.append(paragraph.text)
        
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    text_parts.append(cell.text)

        content = '\n'.join(text_parts)
        language = self._detect_language(content)

        return {
            'success': True,
            'raw_content': content,
            'page_count': 1,
            'language': language,
            'confidence': 0.99,
            'pages': [{
                'page_number': 1,
                'content': content,
                'confidence': 0.99
            }]
        }

    async def _process_text(self, file_path: str, **kwargs) -> Dict:
        """Process plain text files"""
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        language = self._detect_language(content)

        return {
            'success': True,
            'raw_content': content,
            'page_count': 1,
            'language': language,
            'confidence': 1.0,
            'pages': [{
                'page_number': 1,
                'content': content,
                'confidence': 1.0
            }]
        }

    async def _process_doc(self, file_path: str, **kwargs) -> Dict:
        """Process legacy DOC files using python-docx or conversion"""
        # For .doc files, try using docx library or convert to docx first
        # This is a simplified version
        try:
            from docx import Document
            # Try opening as docx
            doc = Document(file_path)
            text_parts = [p.text for p in doc.paragraphs]
            content = '\n'.join(text_parts)
        except:
            # Fallback to read as text
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

        language = self._detect_language(content) if content else 'unknown'

        return {
            'success': True,
            'raw_content': content,
            'page_count': 1,
            'language': language,
            'confidence': 0.85,
            'pages': [{
                'page_number': 1,
                'content': content,
                'confidence': 0.85
            }]
        }

    def _detect_language(self, text: str) -> str:
        """Detect language of text"""
        if not text or len(text.strip()) < 10:
            return 'vi'  # Default to Vietnamese
        
        try:
            detected = detect(text)
            return detected
        except:
            return 'vi'  # Default fallback
```

---

## 3. NLP & ENTITY EXTRACTION SERVICE

```python
# services/nlp_service.py

from typing import List, Dict
import spacy
from vncorenlp import VnCoreNLP
import regex as re
from datetime import datetime

class NLPService:
    def __init__(self):
        # Vietnamese NLP
        self.vn_nlp = VnCoreNLP("http://localhost:9000")
        
        # English NLP
        try:
            self.en_nlp = spacy.load('en_core_web_sm')
        except:
            print("Downloading English model...")
            os.system("python -m spacy download en_core_web_sm")
            self.en_nlp = spacy.load('en_core_web_sm')

    async def extract_entities(
        self,
        text: str,
        language: str = 'vi'
    ) -> Dict:
        """Extract entities from text"""
        
        if language == 'vi':
            return self._extract_vietnamese_entities(text)
        else:
            return self._extract_english_entities(text)

    def _extract_vietnamese_entities(self, text: str) -> Dict:
        """Extract entities from Vietnamese text"""
        
        result = self.vn_nlp.annotate(text)
        
        entities = {
            'people': [],
            'organizations': [],
            'locations': [],
            'dates': [],
            'money': [],
            'numbers': []
        }

        # Process entities
        for sentence in result['sentences']:
            for token in sentence['tokens']:
                if 'ner' in token:
                    ner_label = token['ner']
                    word = token['form']
                    
                    if ner_label == 'PERSON':
                        entities['people'].append(word)
                    elif ner_label == 'ORG':
                        entities['organizations'].append(word)
                    elif ner_label == 'LOCATION':
                        entities['locations'].append(word)

        # Extract dates and money patterns
        entities['dates'] = self._extract_dates_vietnamese(text)
        entities['money'] = self._extract_money_vietnamese(text)
        entities['numbers'] = self._extract_numbers(text)

        # Remove duplicates
        for key in entities:
            entities[key] = list(set(entities[key]))

        return entities

    def _extract_english_entities(self, text: str) -> Dict:
        """Extract entities from English text"""
        
        doc = self.en_nlp(text)
        
        entities = {
            'people': [],
            'organizations': [],
            'locations': [],
            'dates': [],
            'money': [],
            'numbers': []
        }

        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                entities['people'].append(ent.text)
            elif ent.label_ == 'ORG':
                entities['organizations'].append(ent.text)
            elif ent.label_ == 'GPE':  # Geopolitical entity
                entities['locations'].append(ent.text)
            elif ent.label_ == 'DATE':
                entities['dates'].append(ent.text)
            elif ent.label_ == 'MONEY':
                entities['money'].append(ent.text)

        entities['numbers'] = self._extract_numbers(text)

        # Remove duplicates
        for key in entities:
            entities[key] = list(set(entities[key]))

        return entities

    def _extract_dates_vietnamese(self, text: str) -> List[str]:
        """Extract dates from Vietnamese text"""
        
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{2,4}',  # dd/mm/yyyy
            r'\d{1,2}-\d{1,2}-\d{2,4}',  # dd-mm-yyyy
            r'ngày\s+\d{1,2}\s+tháng\s+\d{1,2}\s+năm\s+\d{4}',
            r'Ngày\s+\d{1,2}\s+tháng\s+\d{1,2}\s+năm\s+\d{4}',
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            dates.extend(matches)
        
        return list(set(dates))

    def _extract_money_vietnamese(self, text: str) -> List[str]:
        """Extract money amounts from Vietnamese text"""
        
        patterns = [
            r'\d+(\.\d{3})*\s*(đồng|đ)',
            r'\d+(\,\d+)?\s*tỷ\s*đồng',
            r'\d+(\,\d+)?\s*triệu\s*đồng',
            r'\$\s*\d+(\.\d+)?',
            r'EUR?\s*\d+(\.\d+)?',
        ]
        
        money = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            money.extend([m[0] if isinstance(m, tuple) else m for m in matches])
        
        return list(set(money))

    def _extract_numbers(self, text: str) -> List[str]:
        """Extract important numbers"""
        
        pattern = r'\d+(\.\d+)?'
        numbers = re.findall(pattern, text)
        
        # Filter to only significant numbers (more than 2 digits or decimals)
        significant = [n for n in numbers if len(n) > 2 or '.' in n]
        
        return list(set(significant))[:50]  # Limit to 50

    async def extract_key_terms(
        self,
        text: str,
        language: str = 'vi',
        top_n: int = 20
    ) -> List[str]:
        """Extract key terms using TF-IDF"""
        
        from sklearn.feature_extraction.text import TfidfVectorizer
        
        # Simple TF-IDF extraction
        vectorizer = TfidfVectorizer(
            max_features=top_n,
            ngram_range=(1, 2),
            language='vietnamese' if language == 'vi' else 'english'
        )
        
        try:
            vectorizer.fit_transform([text])
            terms = vectorizer.get_feature_names_out()
            return list(terms)
        except:
            return []
```

---

## 4. TEXT SUMMARIZATION SERVICE

```python
# services/summarization_service.py

from typing import Dict, List
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import torch
from nltk.tokenize import sent_tokenize
import nltk

nltk.download('punkt')

class SummarizationService:
    def __init__(self):
        self.device = 0 if torch.cuda.is_available() else -1
        
        # Vietnamese summarization model
        self.vi_summarizer = pipeline(
            "summarization",
            model="VietAI/vit5-base-vietnamese-sum",
            device=self.device
        )
        
        # English summarization
        self.en_summarizer = pipeline(
            "summarization",
            model="facebook/bart-large-cnn",
            device=self.device
        )

    async def summarize(
        self,
        text: str,
        language: str = 'vi',
        summary_ratio: float = 0.3,
        max_length: int = 500
    ) -> Dict:
        """
        Summarize text
        
        Returns:
        {
            'extractive_summary': str,  # Direct extract
            'abstractive_summary': str, # Paraphrased
            'sentences_selected': int,
            'compression_ratio': float
        }
        """
        
        try:
            # Extractive summarization (select important sentences)
            extractive = self._extractive_summary(text, summary_ratio)
            
            # Abstractive summarization (paraphrase)
            if language == 'vi':
                abstractive = self._abstractive_summarize_vietnamese(
                    text,
                    max_length
                )
            else:
                abstractive = self._abstractive_summarize_english(
                    text,
                    max_length
                )
            
            original_sents = len(sent_tokenize(text))
            selected_sents = len(sent_tokenize(extractive))
            compression_ratio = len(text) / len(extractive) if extractive else 0

            return {
                'success': True,
                'extractive_summary': extractive,
                'abstractive_summary': abstractive,
                'sentences_selected': selected_sents,
                'original_sentences': original_sents,
                'compression_ratio': compression_ratio
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _extractive_summary(self, text: str, ratio: float = 0.3) -> str:
        """Extract important sentences"""
        
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        
        sentences = sent_tokenize(text)
        
        if len(sentences) <= 2:
            return text

        # TF-IDF vectorization
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(sentences)
        
        # Similarity matrix
        similarity_matrix = cosine_similarity(tfidf_matrix)
        
        # Score sentences
        scores = similarity_matrix.sum(axis=1)
        
        # Select top sentences (maintaining order)
        num_select = max(1, int(len(sentences) * ratio))
        top_indices = sorted(
            range(len(sentences)),
            key=lambda i: scores[i],
            reverse=True
        )[:num_select]
        
        # Maintain original order
        top_indices = sorted(top_indices)
        summary = ' '.join([sentences[i] for i in top_indices])
        
        return summary

    def _abstractive_summarize_vietnamese(
        self,
        text: str,
        max_length: int
    ) -> str:
        """Vietnamese abstractive summarization"""
        
        # Chunk text for long documents
        max_input = 1024
        if len(text) > max_input:
            text = text[:max_input]
        
        try:
            summary = self.vi_summarizer(
                text,
                max_length=min(max_length, 500),
                min_length=100,
                do_sample=False
            )
            return summary[0]['summary_text']
        except:
            return ""

    def _abstractive_summarize_english(
        self,
        text: str,
        max_length: int
    ) -> str:
        """English abstractive summarization"""
        
        max_input = 2048
        if len(text) > max_input:
            text = text[:max_input]
        
        try:
            summary = self.en_summarizer(
                text,
                max_length=min(max_length, 300),
                min_length=100,
                do_sample=False
            )
            return summary[0]['summary_text']
        except:
            return ""

    async def generate_case_sections(
        self,
        documents_content: List[Dict],  # [{fileName, content}]
        case_info: Dict
    ) -> Dict:
        """
        Generate structured case summary sections
        
        Returns:
        {
            'case_overview': str,
            'legal_basis': str,
            'analysis_evaluation': str,
            'claims_and_demands': str,
            'conclusion': str
        }
        """
        
        # Combine all documents
        all_content = '\n\n'.join(
            [f"[{doc['fileName']}]\n{doc['content']}" 
             for doc in documents_content]
        )

        sections = {}

        # Extract each section
        sections['case_overview'] = await self._extract_section(
            all_content,
            "Nội dung vụ việc, sự kiện tình tiết quan trọng"
        )
        
        sections['legal_basis'] = await self._extract_section(
            all_content,
            "Căn cứ pháp lý, luật áp dụng"
        )
        
        sections['analysis_evaluation'] = await self._extract_section(
            all_content,
            "Phân tích, đánh giá, lập luận"
        )
        
        sections['claims_and_demands'] = await self._extract_section(
            all_content,
            "Yêu cầu, đề xuất, kiến nghị"
        )
        
        sections['conclusion'] = await self._extract_section(
            all_content,
            "Kết luận"
        )

        return sections

    async def _extract_section(
        self,
        text: str,
        section_name: str
    ) -> str:
        """Extract relevant section from text"""
        
        # Find section or generate based on keywords
        keywords = section_name.lower().split()
        
        lines = text.split('\n')
        relevant_lines = []
        
        for line in lines:
            if any(kw in line.lower() for kw in keywords):
                relevant_lines.append(line)
            elif len(relevant_lines) > 0 and len(relevant_lines) < 10:
                relevant_lines.append(line)

        section_text = '\n'.join(relevant_lines)
        
        if not section_text or len(section_text) < 50:
            # Generate if not found
            section_text = await self.summarize(
                text,
                max_length=300
            )

        return section_text[:1000]  # Limit to 1000 chars
```

---

## 5. EMBEDDING & VECTOR SEARCH SERVICE

```python
# services/embedding_service.py

from typing import List, Dict
import numpy as np
from sentence_transformers import SentenceTransformer
import torch

class EmbeddingService:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Use multilingual model for Vietnamese/English
        self.model = SentenceTransformer(
            'sentence-transformers/distiluse-base-multilingual-cased-v2',
            device=self.device
        )

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text
        
        Returns: 1D array of shape (768,) for distiluse model
        """
        
        # Clean text
        text = text.strip()[:512]  # Limit to 512 chars for efficiency
        
        embedding = self.model.encode(text)
        
        return embedding.tolist()

    async def generate_embeddings_batch(
        self,
        texts: List[str]
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        
        embeddings = self.model.encode(texts)
        return embeddings.tolist()

    async def similarity_search(
        self,
        query: str,
        documents: List[Dict],  # [{id, content, embedding}]
        top_k: int = 5
    ) -> List[Dict]:
        """
        Find most similar documents to query
        
        Returns: [{id, content, similarity_score}]
        """
        
        query_embedding = await self.generate_embedding(query)
        query_vec = np.array(query_embedding)

        similarities = []
        for doc in documents:
            if 'embedding' not in doc:
                continue
            
            doc_vec = np.array(doc['embedding'])
            
            # Cosine similarity
            similarity = np.dot(query_vec, doc_vec) / (
                np.linalg.norm(query_vec) * np.linalg.norm(doc_vec)
            )
            
            similarities.append({
                'id': doc['id'],
                'content': doc.get('content', '')[:500],
                'similarity': float(similarity)
            })

        # Sort and return top-k
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:top_k]
```

---

## 6. WORKER SERVICE - MESSAGE QUEUE CONSUMER

```python
# services/document_processor_worker.py

import asyncio
import json
import logging
from typing import Dict
import pika
from .ocr_service import OCRService
from .nlp_service import NLPService
from .summarization_service import SummarizationService
from .embedding_service import EmbeddingService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessorWorker:
    def __init__(self, rabbitmq_url: str):
        self.conn = pika.BlockingConnection(
            pika.URLParameters(rabbitmq_url)
        )
        self.channel = self.conn.channel()
        
        # Declare queues
        self.channel.queue_declare(queue='document.upload', durable=True)
        self.channel.queue_declare(queue='document.process', durable=True)
        
        # Services
        self.ocr_service = OCRService()
        self.nlp_service = NLPService()
        self.summarization_service = SummarizationService()
        self.embedding_service = EmbeddingService()

    def start(self):
        """Start consuming messages"""
        
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue='document.upload',
            on_message_callback=self.process_document,
            auto_ack=False
        )
        
        logger.info("Worker started, waiting for messages...")
        self.channel.start_consuming()

    def process_document(self, ch, method, properties, body):
        """Process document upload"""
        
        try:
            message = json.loads(body)
            
            document_id = message['document_id']
            file_path = message['file_path']
            file_type = message['file_type']
            case_id = message['case_id']
            
            logger.info(f"Processing document: {document_id}")
            
            # Step 1: OCR
            ocr_result = asyncio.run(
                self.ocr_service.process_document(
                    file_path,
                    file_type
                )
            )
            
            if not ocr_result['success']:
                self._handle_error(document_id, ocr_result['error'])
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            raw_content = ocr_result['raw_content']
            
            # Step 2: NLP - Entity Extraction
            entities = asyncio.run(
                self.nlp_service.extract_entities(
                    raw_content,
                    ocr_result['language']
                )
            )
            
            key_terms = asyncio.run(
                self.nlp_service.extract_key_terms(
                    raw_content,
                    ocr_result['language']
                )
            )
            
            # Step 3: Summarization
            summary_result = asyncio.run(
                self.summarization_service.summarize(
                    raw_content,
                    ocr_result['language']
                )
            )
            
            # Step 4: Embedding
            embedding = asyncio.run(
                self.embedding_service.generate_embedding(raw_content)
            )
            
            # Step 5: Update database
            result = {
                'document_id': document_id,
                'case_id': case_id,
                'raw_content': raw_content,
                'summary': summary_result.get('abstractive_summary', ''),
                'entities': entities,
                'key_terms': key_terms,
                'embedding': embedding,
                'page_count': ocr_result['page_count'],
                'language': ocr_result['language'],
                'ocr_confidence': ocr_result['confidence'],
                'pages': ocr_result['pages']
            }
            
            # Send to API for database update
            asyncio.run(self._update_database(result))
            
            logger.info(f"Document {document_id} processed successfully")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    async def _update_database(self, result: Dict):
        """Send result to API for database update"""
        
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.put(
                f"http://api-server/api/documents/{result['document_id']}/processing-result",
                json=result,
                headers={'Authorization': 'Bearer SERVICE_TOKEN'}
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"API error: {resp.status}")

    def _handle_error(self, document_id: str, error_message: str):
        """Handle processing error"""
        
        import aiohttp
        
        asyncio.run(
            asyncio.create_task(
                aiohttp.ClientSession().put(
                    f"http://api-server/api/documents/{document_id}/error",
                    json={'error': error_message}
                )
            )
        )

if __name__ == '__main__':
    worker = DocumentProcessorWorker('amqp://guest:guest@localhost:5672/')
    worker.start()
```

This is a comprehensive AI processing pipeline designed specifically for legal document analysis.

