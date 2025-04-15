import pandas as pd
import pymysql
from io import StringIO
from datetime import datetime
from bs4 import BeautifulSoup
import os, requests, re
import pdfkit

# 요청 정보
url = "https://www.kebhana.com/cont/search/json_api/search.jsp"
headers = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/x-www-form-urlencoded"
}
data = {
    "query": "입찰",
    "collection": "etc_total",
    "catId": "spb_81",
    "startCount": 0,
    "viewCount": 10
}

# 디렉토리 설정
pdf_dir = "hana_pdfs"
html_dir = "hana_temp_html"
os.makedirs(pdf_dir, exist_ok=True)
os.makedirs(html_dir, exist_ok=True)

def clean_title(title):
    return re.sub(r"#keystart#(.*?)#keyend#", r"\1", title)

def extract_attachment_urls(soup):
    links = soup.select("a.btnBox.pdf")
    urls = []
    for link in links:
        href = link.get("href")
        name = link.get_text(strip=True)
        if href:
            if not href.startswith("http"):
                href = "https://image.kebhana.com" + href
            urls.append((name, href))
    return urls

def generate_pdf_and_attachments(artid, title, url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    content_div = soup.select_one("div.tableWrap")

    if not content_div:
        print(f"본문 div.tableWrap 찾을 수 없음: {artid}")
        return None, []

    date = soup.select_one("td.date").get_text(strip=True)

    html_content = f"""
    <html>
    <head>
        <meta charset='utf-8'>
        <style>
            body {{ font-family: '맑은 고딕', sans-serif; font-size: 12pt; margin: 20px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            td, th {{ border: 1px solid #999; padding: 5px; }}
        </style>
    </head>
    <body>
        <h2 style='text-align: center;'>{title}</h2>
        <p style='text-align: right;'>게시일: {date}</p>
        <hr>
    """

    skip_rest = False
    for elem in content_div.find_all(recursive=False):
        if elem.name == "h5" and "첨부" in elem.get_text():
            skip_rest = True
            continue
        if skip_rest:
            continue
        html_content += str(elem)

    signature = soup.select_one("div.tc.mt30")
    if signature:
        html_content += f"<hr>{str(signature)}"

    html_content += "</body></html>"

    # 저장 경로
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    html_path = os.path.join(html_dir, f"{artid}_{timestamp}.html")
    pdf_path = os.path.join(pdf_dir, f"{artid}_{timestamp}.pdf")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    config = pdfkit.configuration(wkhtmltopdf=r"C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
    pdfkit.from_file(html_path, pdf_path, configuration=config)

    attachments = extract_attachment_urls(soup)
    return pdf_path, attachments


res = requests.post(url, headers=headers, data=data)
dat = pd.read_json(StringIO(res.text))
items = dat['dataList'][0]['Result']

# DB 연결
conn = pymysql.connect(
    host="localhost",
    user='root',
    password='@datasolution',
    db='bank',
    charset='utf8mb4'
)
cursor = conn.cursor()

item_sql = """
    INSERT INTO hana_items (artid, title, date, content_path)
    VALUES (%s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE title=VALUES(title), date=VALUES(date), content_path=VALUES(content_path)
"""

attachment_sql = """
    INSERT IGNORE INTO hana_attachments (artid, file_name, file_url)
    VALUES (%s, %s, %s)
"""

for item in items:
    artid = item.get('ARTID')
    # 테이블에 이미 존재하는 artid인지 확인
    cursor.execute("SELECT 1 FROM hana_items WHERE artid = %s", (artid,))
    if cursor.fetchone():
        print(f"중복 artid 발견: {artid}, 크롤링 중단")
        break  # 또는 return (파일 전체 중단)

    title = clean_title(item.get('TITLE', ''))
    date = item.get('DATE', '')
    if date:
        date = datetime.strptime(date, '%Y.%m.%d').strftime('%Y-%m-%d')

    base_url = "https://www.kebhana.com"
    page_url = base_url + item.get('PHYDIRURL', '') + item.get('FILENM', '')

    pdf_path, attachments = generate_pdf_and_attachments(artid, title, page_url)
    if not pdf_path:
        continue

    cursor.execute(item_sql, (artid, title, date, pdf_path))

    for name, url in attachments:
        cursor.execute(attachment_sql, (artid, name, url))

conn.commit()
cursor.close()
conn.close()
print("하나은행 PDF + 첨부파일 링크 저장 완료")
