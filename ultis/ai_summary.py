import os
from openai import OpenAI  # Sử dụng thư viện OpenAI chính thức

# Khởi tạo client OpenAI
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def get_prompt_content(category, file_name):
    """
    Đọc nội dung file prompt dựa trên thư mục phân loại.
    :param category: Tên thư mục con (ví dụ: 'summary' hoặc 'summary_document')
    :param file_name: Tên file cần đọc ('instruction.txt', 'example.json')
    """
    # Lấy đường dẫn đến thư mục 'ultis' (nơi chứa file ai_summary.py)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Xây dựng đường dẫn: ultis -> prompt -> [category] -> [file_name]
    full_path = os.path.join(base_dir, 'prompt', category, file_name)
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ Không tìm thấy file: {full_path}")
        return ""

def generate_master_summary_with_citations(doc_summaries):
    # 1. Load Instruction và Example từ folder 'summary'
    instruction = get_prompt_content('summary', 'instruction.txt')
    example = get_prompt_content('summary', 'example.json')

    if not instruction or not example:
        return None

    # 2. Tạo context từ dữ liệu đầu vào
    context_list = "\n".join([
        f"TÀI LIỆU [{i+1}]: ID: {d['id']}, File: {d['name']}\nNội dung: {d['summary']}\n"
        for i, d in enumerate(doc_summaries)
    ])

    # 3. Thực hiện gọi OpenAI
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"{instruction}\n\n Mẫu kết quả:\n{example}"},
                {"role": "user", "content": f"Danh sách tài liệu:\n{context_list}"}
            ],
            response_format={ "type": "json_object" },
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Master Summary Error: {e}")
        return None

def summarize_document_content(pages_data):
    """
    Sử dụng GPT-4o để tóm tắt nội dung hồ sơ pháp lý.
    """
    try:
        # Gom text từ các trang, đánh dấu rõ ràng để AI không bị nhầm lẫn
        full_text = "\n".join([f"### TRANG {p['page']}: {p['content']}" for p in pages_data])
        
        # GPT-4o có context window lớn (128k), nhưng tóm tắt file đơn lẻ 
        # thì 15k-20k tokens đầu là đủ để nắm nội dung chính.
        input_text = full_text[:25000] 

        prompt = f"""
        Bạn là một Luật sư cao cấp với khả năng phân tích hồ sơ nhạy bén. 
        Hãy tóm tắt tài liệu dưới đây một cách súc tích nhưng đầy đủ các thông tin then chốt.

        YÊU CẦU:
        1. Tóm tắt nội dung chính trong khoảng 3-5 câu.
        2. Gạch đầu dòng các thực thể quan trọng: Loại tài liệu, Nguyên đơn, Bị đơn, Ngày ký kết/Ngày xảy ra sự việc.
        3. Văn phong: Chuyên nghiệp, khách quan, thuật ngữ pháp lý chính xác.

        NỘI DUNG TÀI LIỆU:
        {input_text}
        
        BẢN TÓM TẮT PHÁP LÝ:
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Hoặc "gpt-4-turbo"
            messages=[
                {"role": "system", "content": "Bạn là chuyên gia bóc tách dữ liệu cho hệ thống quản lý án phí và hồ sơ tòa án."},
                {"role": "user", "content": prompt}
            ],
            temperature=0, # Giữ độ chính xác tuyệt đối, tránh sáng tạo
            max_tokens=1000
        )
        
        return response.choices[0].message.content

    except Exception as e:
        print(f"❌ OpenAI Summarization Error: {str(e)}")
        return None
