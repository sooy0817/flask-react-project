def main():
    import os
    import time
    import re
    import pymysql
    from datetime import datetime
    from bs4 import BeautifulSoup
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    import requests
    import pdfkit

    base_dir = os.path.abspath(os.path.dirname(__file__))
    html_dir = os.path.join(base_dir, "woori_temp_html")
    pdf_dir = os.path.join(base_dir, "woori_pdfs")
    download_dir = os.path.join(base_dir, "woori_attachment_downloads")
    os.makedirs(html_dir, exist_ok=True)
    os.makedirs(pdf_dir, exist_ok=True)
    os.makedirs(download_dir, exist_ok=True)

    conn = pymysql.connect(host="localhost", user="root", password="@datasolution", db="bank", charset="utf8mb4")
    cursor = conn.cursor()

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    url = "https://spot.wooribank.com/pot/Dream?withyou=BPPBC0011"
    driver.get(url)
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    rows = soup.select("table.board-list-1 tbody tr")

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

        bbs_id, artid = match.groups()
        date_str = tds[3].text.strip().replace(".", "-")

        cursor.execute("SELECT 1 FROM woori_items WHERE artid = %s", (artid,))
        if cursor.fetchone():
            print(f"이미 존재하는 artid {artid}, 크롤링 중단")
            break

        try:
            driver.find_element(By.ID, f"article_link_{artid}").click()
            time.sleep(2)
            detail_soup = BeautifulSoup(driver.page_source, "html.parser")

            header_div = detail_soup.select_one("div.board-view-header")
            content_div = detail_soup.select_one("div.board-view-cont")
            if not content_div:
                print(f"본문 없음: {artid}")
                driver.back(); time.sleep(1); continue

            attachment_links = driver.find_elements(By.CSS_SELECTOR, "ul.board-add-file li a")
            for a in attachment_links:
                file_name = a.text.strip()
                before_files = set(os.listdir(download_dir))

                a.click()
                time.sleep(5)

                after_files = set(os.listdir(download_dir))
                new_files = list(after_files - before_files)
                if new_files:
                    downloaded_file_path = os.path.join(download_dir, new_files[0])

                    bank_name = "woori"
                    file_url = f"/files/{bank_name}_attachment_downloads/{file_name}"

                    cursor.execute(
                        """
                        INSERT INTO woori_attachments (artid, file_name, file_url)
                        VALUES (%s, %s, %s)
                        ON DUPLICATE KEY UPDATE file_url = VALUES(file_url)
                        """,
                        (artid, file_name, file_url)
                    )

            html_filename = f"{artid}.html"
            html_path = os.path.join(html_dir, html_filename)
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(f"""
                <html>
                <head><meta charset=\"utf-8\"><style>
                body {{ font-family: '맑은 고딕'; font-size: 12pt; margin: 20px; }}
                table {{ width: 100%; border-collapse: collapse; }}
                td, th {{ border: 1px solid #999; padding: 5px; }}
                </style></head>
                <body>{str(header_div) if header_div else ''}{str(content_div)}</body></html>
                """)


            # PDF 저장 후
            pdf_filename = f"{artid}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
            pdf_path = os.path.join(pdf_dir, pdf_filename)

            # PDF 생성
            config = pdfkit.configuration(wkhtmltopdf=r"C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
            pdfkit.from_file(html_path, pdf_path, configuration=config)


            rel_path = os.path.relpath(pdf_path, base_dir).replace("\\", "/")
            web_path = f"/files/{rel_path}"

            bank_name = "우리은행"

            cursor.execute(
                """
                INSERT INTO woori_items (artid, bank, title, date, content_path)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (artid) DO UPDATE SET
                    bank = EXCLUDED.bank,
                    title = EXCLUDED.title,
                    date = EXCLUDED.date,
                    content_path = EXCLUDED.content_path
                """,
                (artid, bank_name, title, date_str, web_path)
            )

            print(f"저장 완료: {artid}")

            driver.back()
            time.sleep(1)

        except Exception as e:
            print(f"오류 ({artid}): {e}")
            driver.get(url)
            time.sleep(2)

    conn.commit()
    cursor.close()
    conn.close()
    driver.quit()
    print("모든 작업 완료")

if __name__ == "__main__":
    main()
