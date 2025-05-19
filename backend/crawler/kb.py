import os
import time
import re
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import UnexpectedAlertPresentException, NoAlertPresentException
import psycopg2
import psycopg2.extras


def wait_for_download_complete(directory, timeout=20):
    start_time = time.time()
    while time.time() - start_time < timeout:
        downloading = [f for f in os.listdir(directory) if f.endswith(".crdownload")]
        if not downloading:
            return True
        time.sleep(0.5)
    return True


def main():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    download_dir = os.path.join(base_dir, "kb_downloads")
    pdf_dir = os.path.join(base_dir, "kb_pdfs")
    os.makedirs(download_dir, exist_ok=True)
    os.makedirs(pdf_dir, exist_ok=True)

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

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    prefs = {"download.default_directory": download_dir}
    chrome_options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    url = "https://omoney.kbstar.com/quics?page=C018592"
    driver.get(url)
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    rows = soup.select("table tbody tr")

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
            print(f"이미 존재하는 artid {artid}, 스킵")
            continue  # ✅ break → continue

        try:
            detail_url = f"https://omoney.kbstar.com/{href}"
            driver.get(detail_url)
            time.sleep(2)

            attachments = []
            content_path = None
            has_successful_download = False

            attachment_links = driver.find_elements(By.CSS_SELECTOR, "dd.upfile li a")
            print(f"[INFO] 첨부파일 {len(attachment_links)}개 발견")

            for idx, a in enumerate(attachment_links):
                try:
                    file_name = a.text.strip()
                    print(f"[INFO] ▶️ 파일 클릭 시도: {file_name}")

                    before_files = set(os.listdir(download_dir))
                    a.click()
                    print("[INFO] 파일 클릭됨, 다운로드 대기 중...")

                    wait_for_download_complete(download_dir)
                    time.sleep(1)

                    after_files = set(os.listdir(download_dir))
                    new_files = list(after_files - before_files)

                    if not new_files:
                        print(f"[경고] 다운로드 실패: {file_name}")
                        continue

                    downloaded_file = new_files[0]
                    downloaded_path = os.path.join(download_dir, downloaded_file)
                    pdf_path = os.path.join(pdf_dir, downloaded_file)

                    # ✅ 파일이 이미 존재하면 삭제
                    if os.path.exists(pdf_path):
                        os.remove(pdf_path)

                    os.rename(downloaded_path, pdf_path)

                    public_url = f"/files/kb_downloads/{downloaded_file}"
                    print(f"[INFO] 다운로드 성공: {public_url}")

                    if content_path is None:
                        content_path = f"/files/kb_pdfs/{downloaded_file}"
                    else:
                        attachments.append((file_name, public_url))

                    has_successful_download = True

                except UnexpectedAlertPresentException:
                    try:
                        alert = driver.switch_to.alert
                        print(f"[ALERT] 경고창 내용: {alert.text}")
                        alert.accept()
                        print(f"[INFO] 알림창 닫음: 파일 미존재로 다운로드 스킵")
                    except NoAlertPresentException:
                        print(f"[WARN] 알림창 없음")
                    continue

            try:
                if has_successful_download and content_path:
                    bank_name = "국민은행"

                    cursor.execute(
                        """
                        INSERT INTO kb_items (artid, bank, title, date, content_path)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (artid) DO UPDATE SET
                            bank = EXCLUDED.bank,
                            title = EXCLUDED.title,
                            date = EXCLUDED.date,
                            content_path = EXCLUDED.content_path
                        """,
                        (artid, bank_name, title, date_str, content_path)
                    )

                for name, path in attachments:
                    cursor.execute(
                        """
                        INSERT INTO kb_attachments (artid, file_name, file_url)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (artid, file_name) DO NOTHING
                        """,
                        (artid, name, path)
                    )

                conn.commit()
                print(f"[완료] artid {artid} 저장됨")

            except Exception as db_err:
                conn.rollback()
                print(f"[DB ERROR] artid {artid}: {db_err}")

        except Exception as e:
            print(f"[오류] artid {artid}: {e}")
            driver.get(url)
            time.sleep(2)

    cursor.close()
    conn.close()
    driver.quit()
    print("모든 작업 완료")


if __name__ == "__main__":
    main()
