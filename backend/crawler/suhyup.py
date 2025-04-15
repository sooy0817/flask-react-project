import os
import re
import time
import pymysql
import pdfkit
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ====== DB 연결 ======
conn = pymysql.connect(
    host="localhost",
    user="root",
    password="@datasolution",
    db="bank",
    charset="utf8mb4"
)
cursor = conn.cursor()

# ====== 폴더 준비 ======
pdf_dir = "suhyup_pdfs"
html_dir = "suhyup_temp_html"
os.makedirs(pdf_dir, exist_ok=True)
os.makedirs(html_dir, exist_ok=True)

# ====== Selenium 세팅 ======
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# ====== URL 접속 및 프레임 진입 ======
url = "https://www.suhyup-bank.com/ib20/mnu/PBM00551"
driver.get(url)
time.sleep(2)
driver.switch_to.frame("ib20_content_frame")

# ====== 검색 입력 및 엔터 ======
search_input = driver.find_element(By.ID, "columnValue")
search_input.send_keys("입찰")
search_input.send_keys("\n")
time.sleep(2)

# ====== 검색 결과 목록 파싱 ======
html = driver.page_source
soup = BeautifulSoup(html, "html.parser")
rows = soup.select("table.boardList tbody tr")

for row in rows:
    tds = row.find_all("td")
    if len(tds) < 4:
        continue

    title_tag = tds[1].find("a")
    if not title_tag:
        continue

    title = title_tag.get_text(strip=True)
    onclick_attr = title_tag.get("onclick", "")
    match = re.search(r"goDetail\((\d+)\)", onclick_attr)
    if not match:
        continue
    artid = match.group(1)

    cursor.execute("SELECT 1 FROM suhyup_items WHERE artid = %s", (artid,))
    if cursor.fetchone():
        print(f"이미 존재하는 artid {artid}, 크롤링 중단")
        break  # 또는 continue
    date = tds[2].get_text(strip=True)

    # ====== 상세 페이지 이동 ======
    try:
        # 검색 결과 페이지 다시 로딩 & 프레임 진입
        driver.get(url)
        time.sleep(2)
        driver.switch_to.frame("ib20_content_frame")

        # 다시 검색
        search_input = driver.find_element(By.ID, "columnValue")
        search_input.clear()
        search_input.send_keys("입찰")
        search_input.send_keys("\n")
        time.sleep(2)

        # 해당 게시글 클릭
        target_link = driver.find_element(By.XPATH, f'//a[contains(@onclick, "goDetail({artid})")]')
        target_link.click()
        time.sleep(2)

        # 상세 페이지 파싱
        html = driver.page_source
        detail_soup = BeautifulSoup(html, "html.parser")

        content_div = detail_soup.select("div.textArea")[0]
        if not content_div:
            print(f"본문 누락 - {artid}")
            continue

        # HTML 저장
        html_filename = f"{artid}.html"
        html_path = os.path.join(html_dir, html_filename)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(f"""
            <html><head><meta charset="utf-8">
            <style>
                body {{ font-family: '맑은 고딕'; font-size: 12pt; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                td, th {{ border: 1px solid #999; padding: 5px; }}
            </style>
            </head><body>
                {str(content_div)}
            </body></html>
            """)

        # PDF 변환
        pdf_filename = f"{artid}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
        pdf_path = os.path.join(pdf_dir, pdf_filename)
        config = pdfkit.configuration(wkhtmltopdf=r"C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
        pdfkit.from_file(html_path, pdf_path, configuration=config)

        # 본문 DB 저장
        sql = """
            INSERT INTO suhyup_items (artid, title, date, content_path)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE title=VALUES(title), date=VALUES(date), content_path=VALUES(content_path)
        """
        cursor.execute(sql, (artid, title, date, pdf_path))
        print(f"저장 완료: {artid} → {pdf_path}")

        # 첨부파일 저장
        attachment_section = detail_soup.select("div.textArea")[1]
        a_tags = attachment_section.select("a")

        for a in a_tags:
            file_name = a.get_text(strip=True)
            onclick = a.get("href", "")
            match = re.search(r"filename=(.*?)'\)", onclick)
            if not match:
                continue
            file_path_encoded = match.group(1)  # 예: 붙임2.%20제안요청서.pdf
            file_path_decoded = file_path_encoded.replace("%20", " ")
            file_url = f"https://www.suhyup-bank.com/data/file/TB_NEWS/6038/{file_path_encoded}"
            cursor.execute(
                "INSERT IGNORE INTO suhyup_attachments (artid, file_name, file_url) VALUES (%s, %s, %s)",
                (artid, file_name, file_url)
            )

    except Exception as e:
        print(f"오류 발생 - {artid}: {e}")
        continue

# ====== 종료 ======
conn.commit()
cursor.close()
conn.close()
driver.quit()
print("입찰 검색 결과 크롤링 완료")
