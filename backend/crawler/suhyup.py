def main():
    import os
    import re
    import time
    import pdfkit
    import psycopg2
    import psycopg2.extras
    from datetime import datetime
    from bs4 import BeautifulSoup
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager

    conn = psycopg2.connect(
        host="dpg-d0lbspje5dus73ceh1lg-a.oregon-postgres.render.com",
        dbname="bank_mgh0",
        user="dsuser",
        password="ucjTeuup7FY6ZCsSRVPjiS5RDZWqalBG",
        port=5432,
        sslmode="require",
        cursor_factory=psycopg2.extras.RealDictCursor
    )
    cursor = conn.cursor()

    base_dir = os.path.abspath(os.path.dirname(__file__))
    pdf_dir = os.path.join(base_dir, "suhyup_pdfs")
    html_dir = os.path.join(base_dir, "suhyup_temp_html")
    attachment_dir = os.path.join(base_dir, "suhyup_attachment_downloads")
    os.makedirs(attachment_dir, exist_ok=True)
    os.makedirs(pdf_dir, exist_ok=True)
    os.makedirs(html_dir, exist_ok=True)

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    url = "https://www.suhyup-bank.com/ib20/mnu/PBM00551"
    driver.get(url)
    time.sleep(2)
    driver.switch_to.frame("ib20_content_frame")

    search_input = driver.find_element(By.ID, "columnValue")
    search_input.send_keys("입찰")
    search_input.send_keys("\n")
    time.sleep(2)

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
            break
        date = tds[2].get_text(strip=True)

        try:
            driver.get(url)
            time.sleep(2)
            driver.switch_to.frame("ib20_content_frame")

            search_input = driver.find_element(By.ID, "columnValue")
            search_input.clear()
            search_input.send_keys("입찰")
            search_input.send_keys("\n")
            time.sleep(2)

            target_link = driver.find_element(By.XPATH, f'//a[contains(@onclick, "goDetail({artid})")]')
            target_link.click()
            time.sleep(2)

            html = driver.page_source
            detail_soup = BeautifulSoup(html, "html.parser")

            content_div = detail_soup.select("div.textArea")[0]
            if not content_div:
                print(f"본문 누락 - {artid}")
                continue

            html_filename = f"{artid}.html"
            html_path = os.path.join(html_dir, html_filename)
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(f"""
                <html><head><meta charset=\"utf-8\">
                <style>
                    body {{ font-family: '맑은 고딕'; font-size: 12pt; margin: 20px; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    td, th {{ border: 1px solid #999; padding: 5px; }}
                </style>
                </head><body>
                    {str(content_div)}
                </body></html>
                """)

            pdf_filename = f"{artid}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
            pdf_path = os.path.join(pdf_dir, pdf_filename)

            # PDF 생성
            config = pdfkit.configuration(wkhtmltopdf=r"C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
            pdfkit.from_file(html_path, pdf_path, configuration=config)

            # 웹에서 접근 가능한 경로로 변환하여 저장
            rel_pdf_path = f"/files/suhyup_pdfs/{pdf_filename}"

            bank_name = "수협은행"

            sql = """
                INSERT INTO suhyup_items (artid, bank, title, date, content_path)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (artid) DO UPDATE SET
                    bank = EXCLUDED.bank,
                    title = EXCLUDED.title,
                    date = EXCLUDED.date,
                    content_path = EXCLUDED.content_path
            """
            cursor.execute(sql, (artid, bank_name, title, date, rel_pdf_path))

            print(f"저장 완료: {artid} → {pdf_path}")

            attachment_section = detail_soup.select("div.textArea")[1]
            a_tags = attachment_section.select("a")

            for a in a_tags:
                file_name = a.get_text(strip=True)
                onclick = a.get("href", "")
                match = re.search(r"filename=(.*?)'\)", onclick)
                if not match:
                    continue
                file_path_encoded = match.group(1)
                file_path_decoded = file_path_encoded.replace("%20", " ")
                try:
                    file_url = f"https://www.suhyup-bank.com/data/file/TB_NEWS/6038/{file_path_encoded}"
                    safe_name = re.sub(r'[\\/*?:"<>|]', "_", file_name)
                    save_path = os.path.join(attachment_dir, safe_name)

                    file_res = requests.get(file_url)
                    with open(save_path, "wb") as f:
                        f.write(file_res.content)

                    # 프론트에서 접근 가능한 URL로 저장
                    public_url = f"/files/suhyup_attachment_downloads/{safe_name}"

                    cursor.execute(
                        "INSERT IGNORE INTO suhyup_attachments (artid, file_name, file_url) VALUES (%s, %s, %s)",
                        (artid, file_name, public_url)
                    )
                    print(f"[첨부 다운로드 완료] {file_name}")

                except Exception as e:
                    print(f"[첨부 실패] {file_name} → {e}")


        except Exception as e:
            print(f"오류 발생 - {artid}: {e}")
            continue

    conn.commit()
    cursor.close()
    conn.close()
    driver.quit()
    print("입찰 검색 결과 크롤링 완료")

if __name__ == "__main__":
    main()
