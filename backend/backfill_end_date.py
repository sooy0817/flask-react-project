import pymysql
import json
from extract_date import extract_end_date_from_summary
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

def backfill_end_dates(table_name="summary_cache"):
    conn = get_connection()
    cursor = conn.cursor()

    # end_date가 비어 있는 요약 데이터만 조회
    cursor.execute(
        f"SELECT artid, summary_json FROM {table_name} WHERE end_date IS NULL"
    )
    rows = cursor.fetchall()

    print(f"🔍 '{table_name}' 대상 요약 {len(rows)}건 처리 중...\n")

    for row in rows:
        artid = row["artid"]
        try:
            summary_json = json.loads(row["summary_json"])
            end_date = extract_end_date_from_summary(summary_json)

            if end_date:
                print(f"✅ {artid} → 추출된 end_date: {end_date}")
                cursor.execute(
                    f"UPDATE {table_name} SET end_date = %s WHERE artid = %s",
                    (end_date, artid)
                )
            else:
                print(f"⚠️ {artid} → end_date 없음")

        except Exception as e:
            print(f"❌ {artid} 처리 중 오류: {e}")

    conn.commit()
    cursor.close()
    conn.close()
    print(f"\n✅ '{table_name}' end_date 백필 완료")

if __name__ == "__main__":
    backfill_end_dates("summary_cache")