import pymysql
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv
load_dotenv()
import psycopg2
import psycopg2.extras


def get_connection():
    return psycopg2.connect(
        host="dpg-d0lbspje5dus73ceh1lg-a.oregon-postgres.render.com",
        dbname="bank_mgh0",
        user="dsuser",
        password="ucjTeuup7FY6ZcsSRVPji5S8RDZWqalBG",
        port=5432,
        cursor_factory=psycopg2.extras.RealDictCursor
    )
# 키워드 추출 함수
def extract_keywords(artid, title, bank):
    llm = ChatOpenAI(model_name="gpt-4o", temperature=0)
    prompt = PromptTemplate.from_template("""
    다음 입찰공고 제목에서 실제 사업의 목적, 시스템 이름, 기술명, 도입 대상 등 실질적인 키워드들을 추출해줘. 
    키워드 개수는 3-5개 정도면 좋겠지만, 추출할 키워드가 많이 없다면 핵심 키워드 한개만 뽑아도 좋아.
불필요한 단어(예: 입찰, 도입, 재공고, 공고 등)는 제외하고, 중요한 고유명사나 공고 핵심 단어 중심으로 추출해.
키워드는 쉼표로 구분해줘.

제목:
"{text}"

키워드:

    """)
    chain = LLMChain(llm=llm, prompt=prompt)
    try:
        result = chain.run(text=title)
        keywords = [kw.strip() for kw in result.split(",") if kw.strip()]
    except Exception as e:
        print(f"키워드 추출 실패: {artid} → {e}")
        return

    conn = get_connection()
    cursor = conn.cursor()
    for kw in keywords:
        cursor.execute("INSERT IGNORE INTO keyword_table (artid, keyword, bank) VALUES (%s, %s, %s)", (artid, kw, bank))
    conn.commit()
    conn.close()
    print(f"키워드 저장 완료: {artid}")

# 전체 공고에서 키워드 추출

def extract_keywords_for_all():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT ab.artid, ab.title, ab.bank
        FROM (
            SELECT i.artid, i.title, i.bank FROM hana_items i
            UNION ALL
            SELECT i.artid, i.title, 'shinhan' AS bank FROM shinhan_items i
            UNION ALL
            SELECT i.artid, i.title, i.bank FROM shjoongang_items i
            UNION ALL
            SELECT i.artid, i.title, i.bank FROM suhyup_items i
            UNION ALL
            SELECT i.artid, i.title, i.bank FROM kb_items i
            UNION ALL
            SELECT i.artid, i.title, i.bank FROM woori_items i
        ) ab
    """)

    rows = cursor.fetchall()
    for row in rows:
        extract_keywords(row["artid"], row["title"], row["bank"])

    conn.close()
    print("전체 키워드 추출 완료")


if __name__ == "__main__":
    extract_keywords_for_all()