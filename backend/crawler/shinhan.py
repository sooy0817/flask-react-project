import requests
from bs4 import BeautifulSoup
import pymysql
import re
import os
from datetime import datetime
import pdfkit
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

# DB 연결
conn = pymysql.connect(
    host="localhost",
    user='root',
    password='@datasolution',
    db='bank',
    charset='utf8mb4'
)
cursor = conn.cursor()

# 저장 경로
pdf_dir = "shinhan_pdfs"
html_dir = "shinhan_temp_html"
os.makedirs(pdf_dir, exist_ok=True)
os.makedirs(html_dir, exist_ok=True)

# 게시판 목록 요청
url = "https://www.shinhan.com/hpe/index.jsp#300501020000"
headers = {"User-Agent": "Mozilla/5.0"}
res = requests.get(url, headers=headers)
soup = BeautifulSoup(res.text, "html.parser")
rows = soup.select("table.board-list-1 tbody tr")

# Selenium 브라우저 준비
options = Options()

options.add_argument("--disable-gpu")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get(url)
time.sleep(2)

# 게시글 반복
for row in rows:
    tds = row.find_all("td")
    if len(tds) < 5:
        continue

    title_tag = tds[1].find("a")
    title = title_tag.get("title", "").strip()

    onclick = title_tag.get("onclick", "")
    match = re.search(r"bbs_gotoView\(this,'([^']+)'\s*,\s*(\d+)\)", onclick)
    if not match:
        continue

    bbs_id = match.group(1)
    artid = match.group(2)
    date_str = tds[3].text.strip()
    date = date_str.replace(".", "-")

    try:
        # Selenium에서 해당 게시글 클릭
        article_link = driver.find_element(By.ID, f"article_link_{artid}")
        article_link.click()
        time.sleep(2)

        # 현재 페이지 HTML 가져오기
        html = driver.page_source
        detail_soup = BeautifulSoup(html, "html.parser")
        header_div = detail_soup.select_one("div.board-view-header")
        content_div = detail_soup.select_one("div.board-view-cont")

        if not content_div:
            print(f"본문 div.board-view-cont 찾을 수 없음: {artid}")
            driver.back()
            time.sleep(1)
            continue

        # 첨부파일 추출 및 DB 저장
        attachment_links = detail_soup.select('div.view-file dd.insert a:not(.prev)')
        for a in attachment_links:
            file_name = a.get_text(strip=True)
            file_url = a.get("href")
            if not file_url:
                continue
            full_file_url = f"https://www.suhyup.co.kr{file_url}"
            cursor.execute(
                """
                INSERT IGNORE INTO suhyup_attachments (artid, file_name, file_url)
                VALUES (%s, %s, %s)
                """,
                (artid, file_name, full_file_url)
            )

        # HTML 파일 저장
        html_filename = f"{artid}.html"
        html_path = os.path.join(html_dir, html_filename)

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(f"""
            <html>
            <head>
                <meta charset=\"utf-8\">
                <style>
                    body {{
                        font-family: '맑은 고딕', sans-serif;
                        font-size: 12pt;
                        margin: 20px;
                    }}
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                    }}
                    td, th {{
                        border: 1px solid #999;
                        padding: 5px;
                    }}
                </style>
            </head>
            <body>
                {str(header_div) if header_div else ''}
                {str(content_div)}
            </body>
            </html>
            """)

        # PDF 파일로 변환
        pdf_filename = f"{artid}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
        pdf_path = os.path.join(pdf_dir, pdf_filename)

        # wkhtmltopdf 경로 지정
        config = pdfkit.configuration(wkhtmltopdf=r"C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")

        pdfkit.from_file(html_path, pdf_path, configuration=config)

        # DB 저장
        sql = """
            INSERT INTO woori_items (artid, title, date, content_path)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE title=VALUES(title), date=VALUES(date), content_path=VALUES(content_path)
        """
        cursor.execute(sql, (artid, title, date, pdf_path))
        print(f"저장 완료: {artid} → {pdf_path}")

        # 목록으로 돌아가기
        driver.back()
        time.sleep(1)

    except Exception as e:
        print(f"오류 발생 - {artid}: {e}")
        driver.get(url)
        time.sleep(2)

conn.commit()
cursor.close()
conn.close()
driver.quit()
print("본문 header+content PDF + 첨부파일 정보 저장 완료")
