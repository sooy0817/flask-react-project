import os
import time
import shutil
import pymysql
import pdfkit
import re
import requests
import pandas as pd
from io import StringIO
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def main():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    pdf_dir = os.path.join(base_dir, "hana_pdfs")
    html_dir = os.path.join(base_dir, "hana_html")
    attachment_dir = os.path.join(base_dir, "hana_attachment_downloads")
    os.makedirs(pdf_dir, exist_ok=True)
    os.makedirs(html_dir, exist_ok=True)
    os.makedirs(attachment_dir, exist_ok=True)

    # ✅ LangSmith 에러 방지용 (요약 관련 모듈 쓰는 경우 대비)
    os.environ["LANGCHAIN_TRACING_V2"] = "false"

    # Selenium 셋업
    options = Options()
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # DB 연결
    conn = pymysql.connect(
        host="localhost", user="root", password="@datasolution",
        db="bank", charset="utf8mb4"
    )
    cursor = conn.cursor()

    # 하나은행 검색 API 요청
    url = "https://www.kebhana.com/cont/search/json_api/search.jsp"
    data = {
        "query": "입찰", "collection": "etc_total",
        "catId": "spb_81", "startCount": 0, "viewCount": 10
    }
    res = requests.post(url, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=data)
    dat = pd.read_json(StringIO(res.text))
    items = dat['dataList'][0]['Result']

    for item in items:
        artid = item["ARTID"]
        cursor.execute("SELECT 1 FROM hana_items WHERE artid = %s", (artid,))
        if cursor.fetchone():
            print(f"⛔ 중복 artid: {artid}, 중단")
            break

        title = re.sub(r"#keystart#(.*?)#keyend#", r"\1", item["TITLE"])
        date_str = datetime.strptime(item["DATE"], '%Y.%m.%d').strftime('%Y-%m-%d')
        detail_url = "https://www.kebhana.com" + item["PHYDIRURL"] + item["FILENM"]

        driver.get(detail_url)
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # 📄 본문 PDF 생성
        content_div = soup.select_one("div.tableWrap")
        html = f"""
        <html><head><meta charset="utf-8"><style>
        body {{ font-family: '맑은 고딕'; font-size: 12pt; }}
        table {{ border-collapse: collapse; width: 100%; }}
        td, th {{ border: 1px solid #999; padding: 5px; }}
        </style></head><body>
        <h2>{title}</h2>{content_div}
        </body></html>
        """
        html_name = f"{artid}.html"
        html_path = os.path.join(html_dir, html_name)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

        pdf_name = f"{artid}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
        pdf_path = os.path.join(pdf_dir, pdf_name)
        config = pdfkit.configuration(wkhtmltopdf=r"C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
        pdfkit.from_file(html_path, pdf_path, configuration=config)
        public_pdf_path = f"/files/hana_pdfs/{pdf_name}"

        # ✅ DB 저장
        cursor.execute("""
            INSERT INTO hana_items (artid, title, date, content_path)
            VALUES (%s, %s, %s, %s)
        """, (artid, title, date_str, public_pdf_path))

        # 📎 첨부파일 다운로드 (href 직접 다운로드 방식)
        attachment_elements = driver.find_elements(By.CSS_SELECTOR, "a.btnBox.pdf")
        for link in attachment_elements:
            filename = link.text.strip()
            file_url = link.get_attribute("href")
            if not file_url:
                print(f"❌ URL 없음: {filename}")
                continue

            print(f"📎 직접 다운로드 시도: {filename} - {file_url}")
            safe_name = re.sub(r'[\\/*?:"<>|]', "_", filename)
            ext = os.path.splitext(file_url)[-1] or ".pdf"
            dst = os.path.join(attachment_dir, safe_name + ext)

            try:
                response = requests.get(file_url)
                with open(dst, "wb") as f:
                    f.write(response.content)

                public_url = f"/files/hana_attachment_downloads/{os.path.basename(dst)}"
                cursor.execute("""
                    INSERT IGNORE INTO hana_attachments (artid, file_name, file_url)
                    VALUES (%s, %s, %s)
                """, (artid, filename, public_url))

            except Exception as e:
                print(f"❌ 다운로드 실패: {filename} - {e}")

    conn.commit()
    cursor.close()
    conn.close()
    driver.quit()
    print("✅ 하나은행 크롤링 완료")

if __name__ == "__main__":
    main()
