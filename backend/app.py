from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import pymysql
import json
import os
from datetime import datetime, date
from crawler.run_all import run_all_crawlers
import re
from langchain_community.document_loaders import Docx2txtLoader
from langchain_community.chat_models import ChatOpenAI
from langchain.docstore.document import Document
from langchain_teddynote.document_loaders import HWPLoader
from langchain_community.document_loaders import UnstructuredExcelLoader, PyPDFLoader
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

load_dotenv()


app = Flask(__name__)
CORS(app)  # React에서 호출 가능하게 CORS 허용

summary_prompt = PromptTemplate.from_template("""
다음 입찰공고 문서를 읽고 핵심 정보를 요약해서 JSON 형태로 반환해줘. 반드시 한국어로 작성하고, 항목은 상황에 맞게 유동적으로 구성해도 좋아.

형식 예시:
{{
  "title": "...",
  "summary": [
    {{ "항목": "사업명", "내용": "..." }},
    {{ "항목": "목적", "내용": "..." }},
    ...
  ]
}}

문서 내용:
{document}

반드시 위 JSON 형식 그대로 출력해줘.
""")





@app.route("/api/run-crawler", methods=["POST"])
def run_crawler():
    try:
        run_all_crawlers()  #
        return jsonify({"status": "success", "message": "크롤링 완료"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# DB 연결 함수
def get_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='@datasolution',
        db='bank',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route("/api/all-banks", methods=["GET"])
def get_all_banks():
    conn = get_connection()
    cursor = conn.cursor()

    # JOIN 쿼리
    cursor.execute("""SELECT i.bank as bank, i.artid, i.title, i.date, i.content_path, a.file_name, a.file_url
FROM hana_items i
LEFT JOIN hana_attachments a ON i.artid = a.artid

UNION ALL

SELECT 'shinhan' as bank, i.artid, i.title, i.date, i.content_path, a.file_name, a.file_url
FROM shinhan_items i
LEFT JOIN shinhan_attachments a ON i.artid = a.artid

UNION ALL

SELECT i.bank as bank, i.artid, i.title, i.date, i.content_path, a.file_name, a.file_url
FROM shjoongang_items i
LEFT JOIN shjoongang_attachments a ON i.artid = a.artid

UNION ALL

SELECT i.bank as bank, i.artid, i.title, i.date, i.content_path, a.file_name, a.file_url
FROM suhyup_items i
LEFT JOIN suhyup_attachments a ON i.artid = a.artid

UNION ALL

SELECT i.bank as bank, i.artid, i.title, i.date, i.content_path, a.file_name, a.file_url
FROM kb_items i
LEFT JOIN kb_attachments a ON i.artid = a.artid

UNION ALL


SELECT i.bank as bank, i.artid, i.title, i.date, i.content_path, a.file_name, a.file_url
FROM woori_items i
LEFT JOIN woori_attachments a ON i.artid = a.artid

ORDER BY date DESC;
""")

    rows = cursor.fetchall()

    result = {}
    for idx, row in enumerate(rows):
        try:
            artid = row["artid"]
            raw_date = row["date"]
            if isinstance(raw_date, (datetime, date)):
                formatted_date = raw_date.strftime("%Y.%m.%d")
            elif isinstance(raw_date, str):
                formatted_date = raw_date.replace("-", ".")
            else:
                formatted_date = ""

            if artid not in result:
                result[artid] = {
                    "artid": artid,
                    "title": row["title"],
                    "date": formatted_date,
                    "content_path": row["content_path"],
                    "bank": row["bank"],
                    "attachments": []
                }

            if row["file_name"] and row["file_url"]:
                result[artid]["attachments"].append({
                    "file_name": row["file_name"],
                    "file_url": row["file_url"]
                })
        except Exception as e:
            print(f"row {idx} 처리 중 오류: {e}")
            continue

    cursor.close()
    conn.close()

    return jsonify(list(result.values()))


@app.route('/files/shjoongang_attachment_downloads/<path:filename>')
def serve_shjoongang_attachment(filename):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    folder = os.path.join(base_dir, "crawler", "shjoongang_attachment_downloads")
    return send_from_directory(folder, filename, as_attachment=True)
@app.route('/files/shjoongang_pdfs/<path:filename>')
def serve_shjoongang_pdf(filename):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    pdf_folder = os.path.join(base_dir, 'crawler', 'shjoongang_pdfs')
    return send_from_directory(pdf_folder, filename)

@app.route('/files/hana_attachment_downloads/<path:filename>')
def serve_hana_attachment(filename):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    folder = os.path.join(base_dir, "crawler", "hana_attachment_downloads")
    return send_from_directory(folder, filename, as_attachment=True)

@app.route('/files/hana_pdfs/<path:filename>')
def serve_hana_pdf(filename):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    pdf_folder = os.path.join(base_dir, 'crawler', 'hana_pdfs')
    return send_from_directory(pdf_folder, filename)

@app.route('/files/woori_pdfs/<path:filename>')
def serve_woori_pdf(filename):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    pdf_folder = os.path.join(base_dir, 'crawler', 'woori_pdfs')
    return send_from_directory(pdf_folder, filename)

@app.route('/files/woori_attachment_downloads/<path:filename>')
def serve_woori_attachment(filename):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    folder = os.path.join(base_dir, "crawler", "woori_attachment_downloads")
    return send_from_directory(folder, filename, as_attachment=True)

@app.route('/files/suhyup_pdfs/<path:filename>')
def serve_suhyup_pdf(filename):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    pdf_folder = os.path.join(base_dir, 'crawler', 'suhyup_pdfs')
    return send_from_directory(pdf_folder, filename)

@app.route('/files/suhyup_attachment_downloads/<path:filename>')
def serve_suhyup_attachment(filename):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    folder = os.path.join(base_dir, "crawler", "suhyup_attachment_downloads")  # 폴더 위치에 따라 수정
    return send_from_directory(folder, filename, as_attachment=True)


@app.route('/kb_downloads/<path:filename>')
def serve_kb_pdf(filename):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    pdf_folder = os.path.join(base_dir, 'crawler', 'kb_downloads')
    return send_from_directory(pdf_folder, filename, as_attachment=False, mimetype="application/pdf")

@app.route('/files/kb_downloads/<path:filename>')
def serve_kb_attachment(filename):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    folder = os.path.join(base_dir, 'crawler', 'kb_downloads')  # 경로 확인 필요
    return send_from_directory(folder, filename, as_attachment=True)



@app.route("/files/<bank>/<path:filename>")
def serve_attachment(bank, filename):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    download_dir = os.path.join(base_dir, "crawler", f"{bank}_attachment_downloads")

    return send_from_directory(download_dir, filename, as_attachment=True)



@app.route("/api/summary", methods=["POST"])
def summarize():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    data = request.get_json()
    title = data.get("title", "입찰공고 요약")
    content_path = data.get("content_path")
    attachments = data.get("attachments", [])

    documents = []

    # ✅ PDF 문서 로딩 (PyPDFLoader 사용)
    if content_path:
        pdf_path = os.path.join(base_dir, content_path.lstrip("/files/"))
        if os.path.exists(pdf_path):
            try:
                pdf_docs = PyPDFLoader(pdf_path).load()
                documents.extend(pdf_docs)
            except Exception as e:
                print(f"❌ PDF 로딩 실패: {e}")

    # 📎 첨부파일 로딩
    for att in attachments:
        print("📎 원본 file_url:", att["file_url"])
        try:
            relative_parts = att["file_url"].removeprefix("/files/").split("/")
            file_path = os.path.join(base_dir, "crawler", *relative_parts)
            print("📄 실제 file_path:", file_path)

            ext = os.path.splitext(file_path)[1].lower()

            if ext == ".hwp":
                docs = HWPLoader(file_path).load()
            elif ext == ".xlsx":
                docs = UnstructuredExcelLoader(file_path, mode="elements").load()
            elif ext == ".txt":
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                docs = [Document(page_content=content)]
            elif ext == ".docx":
                docs = Docx2txtLoader(file_path).load()
            elif ext == ".pdf":
                docs = PyPDFLoader(file_path).load()
            else:
                print(f"⚠️ 지원하지 않는 파일 형식: {ext}")
                continue

            documents.extend(docs)

        except Exception as e:
            print(f"❌ {file_path} 로딩 실패: {e}")
            continue

    if not documents:
        return jsonify({"summary": "❌ 요약할 수 있는 문서가 없습니다."})

    # 기존 llm 정의
    llm = ChatOpenAI(model_name="gpt-4o", temperature=0)
    runnable_chain = summary_prompt | llm

    result = runnable_chain.invoke({
        "title": title,
        "document": "\n\n".join([doc.page_content for doc in documents])
    })

    # content 속성 안전하게 추출
    summary_text = getattr(result, "content", str(result)).strip()

    if summary_text.startswith("```json"):
        summary_text = re.sub(r"^```json\s*|\s*```$", "", summary_text.strip(), flags=re.DOTALL)

    try:
        summary_json = json.loads(summary_text)
    except json.JSONDecodeError:
        summary_json = {
            "title": title,
            "summary": [{"항목": "요약", "내용": summary_text}]
        }

    return jsonify({"summary": summary_json})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)

