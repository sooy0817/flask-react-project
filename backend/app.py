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
from langchain_ollama import OllamaLLM
import logging

from extract_date import extract_end_date_from_summary
import psycopg2
import psycopg2.extras


load_dotenv()


os.environ["LANGCHAIN_TRACING_V2"] = "false"

app = Flask(__name__)
CORS(app)  # React에서 호출 가능하게 CORS 허용

summary_prompt = PromptTemplate.from_template("""
다음 입찰공고 문서를 읽고 입찰과 관련된 핵심 정보를 요약해서 JSON 형태로 반환해줘. 반드시 한국어로 작성하고, 항목은 상황에 맞게 유동적으로 구성해도 좋아.
요약 시에는 문서 내용을 왜곡하거나 정보의 변경이 있으면 안돼. 줄글이 아닌 정보전달만 해줘.

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
        password="ucjTeuup7FY6ZCsSRVPjiS5RDZWqalBG",
        port=5432,
        sslmode="require",  # ✅ 반드시 추가
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


@app.route("/api/summary", methods=["POST"])
def summarize():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    data = request.get_json()
    artid = data.get("artid")
    title = data.get("title", "입찰공고 요약")
    content_path = data.get("content_path")
    attachments = data.get("attachments", [])
    use_ollama = data.get("use_ollama", False)
    ollama_model = data.get("ollama_model", "").lower()

    conn = get_connection()
    cursor = conn.cursor()

    if data.get("cache_table"):
        cache_table = data["cache_table"]
    elif use_ollama and "gemma3" in ollama_model:
        cache_table = "summary_cache_gemma3"
    elif use_ollama:
        cache_table = "summary_cache_ollama"
    else:
        cache_table = "summary_cache"

    cursor.execute(f"SELECT summary_json FROM {cache_table} WHERE artid = %s", (artid,))
    row = cursor.fetchone()
    if row:
        print(f"캐시된 요약 반환 - artid {artid} ({cache_table})")
        conn.close()
        return jsonify({"summary": json.loads(row["summary_json"])})

    # 이후 요약 생성 로직은 기존대로 유지

    documents = []
    if content_path:
        relative_path = content_path.replace("/files/", "crawler/")
        pdf_path = os.path.join(base_dir, relative_path)
        if os.path.exists(pdf_path):
            try:
                pdf_docs = PyPDFLoader(pdf_path).load()
                documents.extend(pdf_docs)

                logger = logging.getLogger("SummaryFilter")
                logger.setLevel(logging.INFO)

                for i, doc in enumerate(pdf_docs):
                    logger.info(f"📄 PDF 문서 {i + 1} 페이지 내용:\n{doc.page_content[:500]}...\n")
            except Exception as e:
                print(f"PDF 로딩 실패: {e}")

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("SummaryFilter")

    EXCLUDE_KEYWORDS = ["신청서", "유의서", "일반조건", "양식", "납부서", "제안요청서", "승낙", "서약서", "확약서", "동의서"]

    for att in attachments:
        try:
            file_name = att["file_name"]
            if any(keyword in file_name for keyword in EXCLUDE_KEYWORDS):
                logger.info(f"⏩ 제외된 첨부파일: {file_name}")
                continue

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
                logger.info(f"⚠️ 지원되지 않는 확장자: {file_path}")
                continue

            documents.extend(docs)
            logger.info(f"✅ 포함된 첨부파일: {file_name}")

        except Exception as e:
            logger.error(f"❌ {file_name} 로딩 실패: {e}")
            continue

    use_ollama = data.get("use_ollama", False)
    ollama_model = data.get("ollama_model", "gemma2:2b")

    if not documents:
        return jsonify({"summary": "❌ 요약할 수 있는 문서가 없습니다."})

    if use_ollama:
        llm = OllamaLLM(model=ollama_model, temperature=0)
        prompt_text = summary_prompt.format(document="\n\n".join([doc.page_content for doc in documents]))
        result = llm.invoke(prompt_text)
        summary_text = getattr(result, "content", str(result)).strip()
    else:
        llm = ChatOpenAI(model_name="gpt-4o", temperature=0)
        runnable_chain = summary_prompt | llm
        result = runnable_chain.invoke({"title": title, "document": "\n\n".join([doc.page_content for doc in documents])})
        summary_text = getattr(result, "content", str(result)).strip()

    if summary_text.startswith("```json"):
        summary_text = re.sub(r"^```json\s*|\s*```$", "", summary_text.strip(), flags=re.DOTALL)

    try:
        summary_json = json.loads(summary_text)
    except json.JSONDecodeError:
        summary_json = {"title": title, "summary": [{"항목": "요약", "내용": summary_text}]}

    cursor.execute(
        f"REPLACE INTO {cache_table} (artid, summary_json) VALUES (%s, %s)",
        (artid, json.dumps(summary_json, ensure_ascii=False))
    )

    end_date = extract_end_date_from_summary(summary_json)

    cursor.execute(
        f"""
        REPLACE INTO {cache_table} (artid, summary_json{', end_date' if end_date else ''})
        VALUES (%s, %s{', %s' if end_date else ''})
        """,
        (artid, json.dumps(summary_json, ensure_ascii=False), end_date) if end_date else (
        artid, json.dumps(summary_json, ensure_ascii=False))
    )

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"summary": summary_json})

@app.route("/api/scrap", methods=["GET", "POST"])
def handle_scrap():
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "GET":
        cursor.execute("SELECT artid FROM scrapped_items")
        rows = cursor.fetchall()
        conn.close()
        return jsonify({"artids": [row["artid"] for row in rows]})

    elif request.method == "POST":
        data = request.get_json()
        for item in data.get("items", []):
            artid = item["artid"]
            title = item["title"]
            bank = item["bank"]
            post_date = item['date']
            content_path = item.get("content_path", "")
            cursor.execute(
                "REPLACE INTO scrapped_items (artid, title, bank, date ,content_path) VALUES (%s, %s, %s, %s, %s)",
                (artid, title, bank, post_date, content_path)
            )

        conn.commit()
        conn.close()
        return jsonify({"status": "success"})

@app.route("/api/scrap/delete", methods=["POST"])
def delete_scraps():
    data = request.get_json()
    artids = data.get("artids", [])

    if not artids:
        return jsonify({"message": "삭제할 항목이 없습니다."}), 400

    conn = get_connection()
    cursor = conn.cursor()
    try:
        format_strings = ','.join(['%s'] * len(artids))
        cursor.execute(f"DELETE FROM scrapped_items WHERE artid IN ({format_strings})", tuple(artids))
        conn.commit()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": f"{len(artids)}건 삭제 완료"})

@app.route("/api/scrap/details", methods=["GET"])
def get_scrapped_details():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.artid, s.title, s.bank, s.content_path, s.date as post_date, c.end_date
        FROM scrapped_items s
        LEFT JOIN summary_cache c ON s.artid = c.artid
        WHERE c.end_date IS NOT NULL
    """)

    rows = cursor.fetchall()
    print(f"🔍 scrap rows 개수: {len(rows)}")
    conn.close()
    return jsonify({"data": rows})


@app.route("/api/all/details", methods=["GET"])
def get_all_details():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT ab.artid, ab.title, ab.bank, ab.content_path, ab.date as post_date, sc.end_date as end_date
        FROM (
            SELECT i.bank, i.artid, i.title, i.content_path, i.date FROM hana_items i
            UNION ALL
            SELECT 'shinhan', i.artid, i.title, i.content_path, i.date FROM shinhan_items i
            UNION ALL
            SELECT i.bank, i.artid, i.title, i.content_path, i.date FROM shjoongang_items i
            UNION ALL
            SELECT i.bank, i.artid, i.title, i.content_path, i.date FROM suhyup_items i
            UNION ALL
            SELECT i.bank, i.artid, i.title, i.content_path, i.date FROM kb_items i
            UNION ALL
            SELECT i.bank, i.artid, i.title, i.content_path, i.date FROM woori_items i
        ) ab
        LEFT JOIN summary_cache sc ON ab.artid = sc.artid
        WHERE sc.end_date IS NOT NULL
    """)

    rows = cursor.fetchall()
    print(f"🔍 all rows 개수: {len(rows)}")
    conn.close()
    return jsonify({"data": rows})





if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)

