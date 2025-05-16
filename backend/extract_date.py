import re
from datetime import datetime

def extract_end_date_from_summary(summary_json):
    KEYWORDS_PARTIAL = [
        "입찰", "참가", "제출", "등록", "공고",
        "접수", "신청", "마감", "기한", "기간"
    ]

    full_date_regex = r"(\d{4})[년.\-/\s]*(\d{1,2})[월.\-/\s]*(\d{1,2})"
    partial_date_regex = r"(?<!\d)(\d{1,2})[.\-/\s]+(\d{1,2})(?!\d)"

    candidate_dates = []

    print("📋 요약 항목에서 날짜 추출 시작")

    for item in summary_json.get("summary", []):
        항목 = item.get("항목", "")
        내용 = item.get("내용", "")

        # 키워드 매치 수 확인
        match_count = sum(1 for k in KEYWORDS_PARTIAL if k in 항목)
        if match_count < 2:
            continue

        print(f"🔎 [{항목}] → [{내용}]")

        # 날짜 파싱 방해하는 요소 제거
        내용 = re.sub(r"(로|길)\d{1,3}", "", 내용)  # 도로명 주소 제거
        내용 = re.sub(r"\d{2,4}[.\-]\d{3,4}[.\-]\d{4}", "", 내용)  # 전화번호
        내용 = re.sub(r"\d+(만원|원|회|점|개|부)", "", 내용)  # 단위
        내용 = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "", 내용)  # 이메일

        dates_in_this_item = []
        current_year = None

        # 연도 포함 날짜
        for y, m, d in re.findall(full_date_regex, 내용):
            try:
                dt = datetime(year=int(y), month=int(m), day=int(d))
                dates_in_this_item.append(dt)
                current_year = int(y)
                print(f"  ✅ 연도 포함 날짜 추출: {dt.strftime('%Y.%m.%d')}")
            except:
                print(f"  ⚠️ 날짜 파싱 실패 (연도 있음): {y}.{m}.{d}")

        # 연도 보완 날짜
        for m, d in re.findall(partial_date_regex, 내용):
            if current_year:
                try:
                    dt = datetime(year=current_year, month=int(m), day=int(d))
                    dates_in_this_item.append(dt)
                    print(f" 연도 보완 날짜 추출: {dt.strftime('%Y.%m.%d')}")
                except:
                    print(f" 날짜 파싱 실패 (연도 보완): {current_year}.{m}.{d}")

        # 항목 내 최대 날짜만 후보로 추가
        if dates_in_this_item:
            latest = max(dates_in_this_item)
            candidate_dates.append(latest)

    if not candidate_dates:
        print("추출된 날짜 없음")
        return None

    final_date = max(candidate_dates)
    print(f"최종 선택된 end_date: {final_date.strftime('%Y.%m.%d')}")
    return final_date.strftime("%Y.%m.%d")
