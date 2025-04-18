def main():
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

    # ====== wkhtmltopdf 경로 명시 ======
    PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf=r"C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")

    # ====== DB 연결 ======
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="@datasolution",
        db="bank",
        charset="utf8mb4"
    )
    cursor = conn.cursor()

    # ====== 저장 폴더 준비 ======
    base_dir = os.path.abspath(os.path.dirname(__file__))
    pdf_dir = os.path.join(base_dir, "shjoongang_pdfs")
    html_dir = os.path.join(base_dir, "shjoongang_temp_html")
    attachment_dir = os.path.join(base_dir, "shjoongang_attachment_downloads")
    os.makedirs(attachment_dir, exist_ok=True)
    os.makedirs(pdf_dir, exist_ok=True)
    os.makedirs(html_dir, exist_ok=True)

    # ====== 목록 페이지 요청 ======
    url = "https://www.suhyup.co.kr/suhyup/223/subview.do"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    rows = soup.select("table.board-link-list tbody tr")

    # ====== Selenium 브라우저 준비 ======
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)
    time.sleep(2)

    # ====== 목록 반복 처리 ======
    for row in rows:
        tds = row.find_all("td")
        if len(tds) < 6:
            continue

        title_tag = tds[1].find("a")
        title = title_tag.get_text(strip=True)
        href = title_tag.get("href", "")
        match = re.search(r'/bbs/suhyup/(\d+)/(\d+)/artclView\.do', href)
        if not match:
            continue

        bbs_id = match.group(1)
        artid = match.group(2)

        cursor.execute("SELECT 1 FROM shjoongang_items WHERE artid = %s", (artid,))
        if cursor.fetchone():
            print(f"이미 존재하는 artid {artid}, 크롤링 중단")
            break

        detail_url = f"https://www.suhyup.co.kr{href}"
        date_str = tds[2].text.strip()
        date = date_str.replace(".", "-")

        try:
            driver.get(detail_url)
            time.sleep(2)
            html = driver.page_source
            detail_soup = BeautifulSoup(html, "html.parser")

            header_div = detail_soup.select_one("div.view-info")
            content_div = detail_soup.select_one("div.view-con")

            if not content_div:
                print(f"본문 div.view-con 없음: {artid}")
                continue

            # 첨부파일 저장
            attachment_links = detail_soup.select('div.view-file dd.insert a:not(.prev)')
            for a in attachment_links:
                file_name = a.get_text(strip=True)
                file_url = a.get("href")
                if not file_url:
                    continue
                full_file_url = f"https://www.suhyup.co.kr{file_url}"
                safe_file_name = re.sub(r'[\\/*?:"<>|]', "_", file_name)
                save_path = os.path.join(attachment_dir, safe_file_name)

                try:
                    file_res = requests.get(full_file_url, headers=headers)
                    with open(save_path, "wb") as f:
                        f.write(file_res.content)

                    # 프론트에서 접근 가능한 경로로 저장
                    public_path = f"/files/shjoongang_attachment_downloads/{safe_file_name}"

                    cursor.execute(
                        """
                        INSERT IGNORE INTO shjoongang_attachments (artid, file_name, file_url)
                        VALUES (%s, %s, %s)
                        """,
                        (artid, file_name, public_path)
                    )
                    print(f"첨부파일 저장 완료: {file_name}")

                except Exception as e:
                    print(f"첨부파일 다운로드 실패: {file_name}, 오류: {e}")

            # HTML 저장
            html_filename = f"{artid}.html"
            html_path = os.path.join(html_dir, html_filename)
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(f"""
                <html>
                <head>
                    <meta charset="utf-8">
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

            # PDF 저장
            pdf_filename = f"{artid}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
            pdf_path = os.path.join(pdf_dir, pdf_filename)
            pdfkit.from_file(html_path, pdf_path, configuration=PDFKIT_CONFIG)

            # 프론트에서 접근 가능한 PDF 경로 저장
            pdf_public_path = f"/files/shjoongang_pdfs/{pdf_filename}"

            sql = """
                INSERT INTO shjoongang_items (artid, title, date, content_path)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE title=VALUES(title), date=VALUES(date), content_path=VALUES(content_path)
            """
            cursor.execute(sql, (artid, title, date, pdf_public_path))
            print(f"PDF 저장 완료: {artid} → {pdf_public_path}")

        except Exception as e:
            print(f"오류 발생 - {artid}: {e}")
            continue

    conn.commit()
    cursor.close()
    conn.close()
    driver.quit()
    print("PDF + 첨부파일 DB 저장 완료")

if __name__ == "__main__":
    main()
