from langchain_ollama import OllamaLLM





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
import psycopg2
import psycopg2.extras

load_dotenv()


os.environ["LANGCHAIN_TRACING_V2"] = "false"

app = Flask(__name__)
CORS(app)  # React에서 호출 가능하게 CORS 허용

summary_prompt = PromptTemplate.from_template("""
다음 입찰공고 문서를 읽고 입찰과 관련된 핵심 정보를 요약해서 JSON 형태로 반환해줘. 반드시 한국어로 작성하고, 항목은 상황에 맞게 유동적으로 구성해도 좋아.
요약 시에는 문서 내용을 왜곡하거나 정보의 변경이 있으면 안돼. 줄글이 아닌 정보전달만 해줘

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


def get_connection():
    return psycopg2.connect(
        host="dpg-d0lbspje5dus73ceh1lg-a.oregon-postgres.render.com",
        dbname="bank_mgh0",
        user="dsuser",
        password="ucjTeuup7FY6ZcsSRVPji5S8RDZWqalBG",
        port=5432,
        cursor_factory=psycopg2.extras.RealDictCursor
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


@app.route('/files/kb_pdfs/<path:filename>')
def serve_kb_pdf(filename):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    pdf_folder = os.path.join(base_dir, 'crawler', 'kb_pdfs')
    return send_from_directory(pdf_folder, filename)

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


from langchain_ollama import OllamaLLM

@app.route("/api/summary-ollama", methods=["POST", ""])
def summarize_ollama():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    data = request.get_json()
    artid = data.get("artid")
    title = data.get("title", "입찰공고 요약")
    content_path = data.get("content_path")
    attachments = data.get("attachments", [])

    conn = get_connection()
    cursor = conn.cursor()


    cursor.execute("SELECT summary_json FROM summary_cache_ollama WHERE artid = %s", (artid,))
    row = cursor.fetchone()
    if row:
        print(f"🟩 Ollama 캐시 반환 - artid {artid}")
        conn.close()
        return jsonify({"summary": json.loads(row["summary_json"])})

    documents = []


    if content_path:
        relative_path = content_path.replace("/files/", "crawler/")
        pdf_path = os.path.join(base_dir, relative_path)
        if os.path.exists(pdf_path):
            try:
                pdf_docs = PyPDFLoader(pdf_path).load()
                documents.extend(pdf_docs)
            except Exception as e:
                print(f"PDF 로딩 실패: {e}")


    for att in attachments:
        try:
            relative_parts = att["file_url"].removeprefix("/files/").split("/")
            file_path = os.path.join(base_dir, "crawler", *relative_parts)
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
                continue

            documents.extend(docs)
        except Exception as e:
            print(f"첨부파일 로딩 실패: {file_path} | 에러: {e}")
            continue

    if not documents:
        return jsonify({"summary": "요약할 수 있는 문서가 없습니다."})


    llm = OllamaLLM(model="gemma2:2b", temperature=0)
    prompt_text = summary_prompt.format(document="\n\n".join([doc.page_content for doc in documents]))
    result = llm.invoke(prompt_text)

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

    # 결과 저장: summary_cache_ollama 테이블에 저장
    cursor.execute(
        "REPLACE INTO summary_cache_ollama (artid, summary_json) VALUES (%s, %s)",
        (artid, json.dumps(summary_json, ensure_ascii=False))
    )
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"summary": summary_json})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)

