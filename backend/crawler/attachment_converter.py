import os
import re
import pythoncom
import win32com.client
import psycopg2
import psycopg2.extras

def sanitize_filename(filename):
    return re.sub(r'[\\/:*?"<>|#]', '_', filename)

def convert_and_update_attachments(download_dir, pdf_output_dir, db_config):
    os.makedirs(pdf_output_dir, exist_ok=True)

    # DB 연결
    conn = psycopg2.connect(**db_config, cursor_factory=psycopg2.extras.RealDictCursor)
    cursor = conn.cursor()

    # 📄 HWP → PDF
    def convert_hwp_to_pdf(hwp_path, pdf_path):
        hwp = win32com.client.Dispatch("HWPFrame.HwpObject")
        hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModuleExample")
        hwp.Open(hwp_path)
        hwp.SaveAs(pdf_path, "PDF")
        hwp.Quit()

    # 📄 Excel → PDF
    def convert_excel_to_pdf(excel_path, pdf_path):
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = False
        wb = excel.Workbooks.Open(os.path.abspath(excel_path))
        wb.ExportAsFixedFormat(0, os.path.abspath(pdf_path))  # 0: PDF
        wb.Close()
        excel.Quit()

    for file_name in os.listdir(download_dir):
        file_path = os.path.join(download_dir, file_name)
        file_base, ext = os.path.splitext(file_name)
        ext = ext.lower()

        artid_match = re.search(r'(\d+)', file_name)
        if not artid_match:
            print(f"⛔ artid 못 찾음: {file_name}")
            continue

        artid = artid_match.group(1)
        safe_file_base = sanitize_filename(file_base)
        pdf_path = os.path.join(pdf_output_dir, safe_file_base + ".pdf")

        try:
            pythoncom.CoInitialize()

            if ext == ".hwp":
                convert_hwp_to_pdf(file_path, pdf_path)
            elif ext in [".xls", ".xlsx"]:
                convert_excel_to_pdf(file_path, pdf_path)
            else:
                print(f"❌ 지원하지 않는 형식: {file_name}")
                continue

            # PostgreSQL용 UPDATE
            cursor.execute(
                """
                UPDATE woori_attachments
                SET file_url = %s
                WHERE artid = %s AND file_name = %s
                """,
                (pdf_path, artid, file_name)
            )
            print(f"✅ 변환 완료 및 DB 저장: {file_name} → {pdf_path}")

        except Exception as e:
            print(f"❌ 변환 실패: {file_name} / {e}")
        finally:
            pythoncom.CoUninitialize()

    conn.commit()
    cursor.close()
    conn.close()

# 🧩 실행
if __name__ == "__main__":
    base_dir = os.getcwd()
    download_dir = os.path.join(base_dir, "woori_attachment_downloads")
    pdf_output_dir = os.path.join(base_dir, "woori_attachment_pdf")

    db_config = {
        "host": "dpg-d0lbspje5dus73ceh1lg-a.oregon-postgres.render.com",
        "port": 5432,
        "dbname": "bank_mgh0",
        "user": "dsuser",
        "password": "ucjTeuup7FY6ZcsSRVPji5S8RDZWqalBG"
    }

    convert_and_update_attachments(download_dir, pdf_output_dir, db_config)
