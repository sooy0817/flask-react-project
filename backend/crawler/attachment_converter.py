import os
import re
import pythoncom
import win32com.client
import pymysql

def sanitize_filename(filename):
    """
    Windows에서 사용할 수 없는 문자 제거: \ / : * ? " < > | #
    """
    return re.sub(r'[\\/:*?"<>|#]', '_', filename)

def convert_and_update_attachments(download_dir, pdf_output_dir, db_config):
    os.makedirs(pdf_output_dir, exist_ok=True)

    # DB 연결
    conn = pymysql.connect(**db_config)
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

        # 파일 이름에 포함된 artid 추출
        artid_match = re.search(r'(\d+)', file_name)
        if not artid_match:
            print(f"⛔ artid 못 찾음: {file_name}")
            continue

        artid = artid_match.group(1)

        # 🔒 안전한 PDF 파일 이름 생성
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

            # DB에 PDF 경로 저장
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
        "host": "localhost",
        "user": "root",
        "password": "@datasolution",
        "db": "bank",
        "charset": "utf8mb4"
    }

    convert_and_update_attachments(download_dir, pdf_output_dir, db_config)
