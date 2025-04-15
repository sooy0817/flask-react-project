from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import pymysql
import os
from datetime import datetime, date
import subprocess

app = Flask(__name__)
CORS(app)  # React에서 호출 가능하게 CORS 허용

@app.route("/api/run-crawler", methods=["POST"])
def run_crawler():
    try:
        subprocess.run(["python", "crawler/run_all.py"], check=True)
        return jsonify({"status": "success", "message": "크롤링 완료"}), 200
    except subprocess.CalledProcessError as e:
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
    for row in rows:
        artid = row["artid"]

        # 안전하게 날짜 포맷팅
        raw_date = row["date"]
        print(raw_date)
        print(type(raw_date))
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

    cursor.close()
    conn.close()

    return jsonify(list(result.values()))


@app.route('/shjoongang_pdfs/<path:filename>')
def serve_shjoongang_pdf(filename):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    pdf_folder = os.path.join(base_dir, 'crawler', 'shjoongang_pdfs')
    return send_from_directory(pdf_folder, filename)

@app.route('/hana_pdfs/<path:filename>')
def serve_hana_pdf(filename):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    pdf_folder = os.path.join(base_dir, 'crawler', 'hana_pdfs')
    return send_from_directory(pdf_folder, filename)

@app.route('/woori_pdfs/<path:filename>')
def serve_woori_pdf(filename):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    pdf_folder = os.path.join(base_dir, 'crawler', 'woori_pdfs')
    return send_from_directory(pdf_folder, filename)

@app.route('/suhyup_pdfs/<path:filename>')
def serve_suhyup_pdf(filename):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    pdf_folder = os.path.join(base_dir, 'crawler', 'suhyup_pdfs')
    return send_from_directory(pdf_folder, filename)

@app.route("/files/<bank>/<path:filename>")
def serve_attachment(bank, filename):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    download_dir = os.path.join(base_dir, "crawler", f"{bank}_attachment_downloads")

    return send_from_directory(download_dir, filename, as_attachment=True)



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)

