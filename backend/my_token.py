import os
import pymysql
from transformers import AutoTokenizer
from langchain_community.document_loaders import Docx2txtLoader, UnstructuredExcelLoader, PyPDFLoader
from langchain_teddynote.document_loaders import HWPLoader
from langchain.docstore.document import Document
from huggingface_hub import login
import psycopg2
import psycopg2.extras
login("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")

# 1. tokenizer 설정
tokenizer = AutoTokenizer.from_pretrained("naver-hyperclovax/HyperCLOVAX-SEED-Text-Instruct-1.5B")
def count_tokens(text: str) -> int:
    return len(tokenizer.encode(text))

# 2. 텍스트 추출
def extract_text(file_path):
    try:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            docs = PyPDFLoader(file_path).load()
        elif ext == ".hwp":
            docs = HWPLoader(file_path).load()
        elif ext == ".xlsx":
            docs = UnstructuredExcelLoader(file_path, mode="elements").load()
        elif ext == ".docx":
            docs = Docx2txtLoader(file_path).load()
        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            docs = [Document(page_content=content)]
        else:
            return ""
        return "\n".join([doc.page_content for doc in docs])
    except Exception as e:
        print(f"{file_path} 읽기 실패: {e}")
        return ""

def get_connection():
    return psycopg2.connect(
        host="dpg-d0lbspje5dus73ceh1lg-a.oregon-postgres.render.com",
        dbname="bank_mgh0",
        user="dsuser",
        password="ucjTeuup7FY6ZcsSRVPji5S8RDZWqalBG",
        port=5432,
        cursor_factory=psycopg2.extras.RealDictCursor
    )

# 4. 본문 + 첨부 토큰 리스트 구조화
def process_all_banks():
    banks = ["hana", "shinhan", "shjoongang", "suhyup", "kb", "woori"]
    base_dir = os.path.abspath(os.path.dirname(__file__))
    conn = get_connection()
    cursor = conn.cursor()

    bank_token_map = {}

    for bank in banks:
        print(f"📦 처리중: {bank}")
        artid_token_lists = []

        items_table = f"{bank}_items"
        attachments_table = f"{bank}_attachments"

        cursor.execute(f"SELECT artid, content_path FROM {items_table}")
        items = cursor.fetchall()

        for item in items:
            artid = item["artid"]
            token_list = []

            # 본문 PDF 먼저 처리
            content_path = item.get("content_path")
            if content_path:
                pdf_path = os.path.join(base_dir, content_path.replace("/files/", "crawler/"))
                if os.path.exists(pdf_path):
                    text = extract_text(pdf_path)
                    token_list.append(count_tokens(text))
                else:
                    token_list.append(0)
            else:
                token_list.append(0)

            # 첨부파일들 처리
            cursor.execute(f"SELECT file_url FROM {attachments_table} WHERE artid = %s", (artid,))
            files = cursor.fetchall()

            for f in files:
                try:
                    relative_parts = f["file_url"].removeprefix("/files/").split("/")
                    file_path = os.path.join(base_dir, "crawler", *relative_parts)
                    if os.path.exists(file_path):
                        text = extract_text(file_path)
                        token_list.append(count_tokens(text))
                except Exception as e:
                    print(f"{bank} {artid} 첨부 오류: {e}")
                    continue

            artid_token_lists.append(token_list)

        bank_token_map[bank] = artid_token_lists

    cursor.close()
    conn.close()
    return bank_token_map


result = process_all_banks()
print(result["hana"])
print(result['shinhan'])
print(result['shjoongang'])
print(result['suhyup'])
print(result['kb'])
print(result['woori'])