import os
import time
import re
import json
import pdfkit
import pymysql
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# 디렉토리 설정
base_dir = os.getcwd()
html_dir = "kb_temp_html"
pdf_dir = "kb_pdfs"

os.makedirs(html_dir, exist_ok=True)
os.makedirs(pdf_dir, exist_ok=True)

# DB 연결
conn = pymysql.connect(
    host="localhost",
    user="root",
    password="@datasolution",
    db="bank",
    charset="utf8mb4"
)
cursor = conn.cursor()

# 크롬 옵션 설정
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_experimental_option("prefs", {
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
})

# 드라이버 시작
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# 게시판 접속
url = "https://omoney.kbstar.com/quics?page=C018592"
driver.get(url)
time.sleep(2)
soup = BeautifulSoup(driver.page_source, "html.parser")
rows = soup.select("table tbody tr")


# 게시글 처리 루프
for row in rows:
    tds = row.find_all("td")
    if len(tds) < 4:
        continue

    title_tag = tds[1].find("a")
    if not title_tag:
        continue

    title = title_tag.get_text(strip=True)
    href = title_tag.get("href", "")
    match = re.search(r"articleId=(\d+)", href)
    if not match:
        print(f"[WARN] href 매칭 실패: {href}")
        continue

    artid = match.group(1)
    date_str = tds[2].text.strip().replace(".", "-")


    cursor.execute("SELECT 1 FROM kb_items WHERE artid = %s", (artid,))
    if cursor.fetchone():
        print(f"이미 존재하는 artid {artid}, 크롤링 중단")
        break

    try:
        href = title_tag.get("href", "")
        detail_url = f"https://omoney.kbstar.com/{href}"
        driver.get(detail_url)

        time.sleep(2)
        detail_soup = BeautifulSoup(driver.page_source, "html.parser")

        form = detail_soup.select_one("form#frmDownload1")
        attachments = []
        if form:
            file_name_input = form.select_one("input[name='_FILE_NAME']")
            if file_name_input:
                file_name = file_name_input.get("value", "").strip()
                action_url = form.get("action", "").strip()
                full_url = f"https://omoney.kbstar.com{action_url}"
                attachments.append((file_name, full_url))

        content_path = attachments[0][1] if attachments else ""

        cursor.execute(
            """
            INSERT INTO kb_items (artid, title, date, content_path)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE title=VALUES(title), date=VALUES(date), content_path=VALUES(content_path)
            """,
            (artid, title, date_str, content_path)
        )

        for name, url in attachments:
            cursor.execute(
                """
                INSERT IGNORE INTO kb_attachments (artid, file_name, file_url)
                VALUES (%s, %s, %s)
                """,
                (artid, name, url)
            )
        print(f"[완료] artid {artid} 저장됨")

    except Exception as e:
        print(f"[오류] artid {artid}: {e}")
        driver.get(url)
        time.sleep(2)

conn.commit()
cursor.close()
conn.close()
driver.quit()
print("모든 작업 완료")
