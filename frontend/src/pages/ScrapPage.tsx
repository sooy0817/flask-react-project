import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getBankLogo } from "../utils/getBankLogo";

interface ScrapItem {
  title: string;
  artid: string;
  bank: string;
  post_date: string;
  end_date: string;
}

function ScrapPage() {
    const [scrapLists, setScrapLists] = useState<ScrapItem[]>([]);
  const navigate = useNavigate();

  const [isEditing, setIsEditing] = useState(false);
const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());
    const handleConfirmSelection = async () => {
  const toDelete = Array.from(selectedItems);

  try {
    const res = await fetch("http://localhost:5001/api/scrap/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ artids: toDelete }),
    });

    if (!res.ok) {
      alert("삭제에 실패했습니다.");
      return;
    }


    // 성공하면 프론트 목록도 갱신
    const remaining = scrapLists.filter(item => !selectedItems.has(item.artid));
    setScrapLists(remaining);
    setIsEditing(false);
    setSelectedItems(new Set());
  } catch (error) {
    console.error("삭제 중 오류 발생:", error);
    alert("서버 오류로 삭제에 실패했습니다.");
  }
};


  const today = new Date();
today.setHours(0, 0, 0, 0);

  const formatKoreanDate = (dateString: string) => {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = date.getMonth() + 1;
    const day = date.getDate();
    return `${year}년 ${month}월 ${day}일`;
  };

  const todayStr = formatKoreanDate(today.toISOString());

  const isSameDate = (d1: Date, d2: Date) =>
    d1.getFullYear() === d2.getFullYear() &&
    d1.getMonth() === d2.getMonth() &&
    d1.getDate() === d2.getDate();

  useEffect(() => {
    fetch("http://localhost:5001/api/scrap/details")
      .then((res) => res.json())
      .then((res) => {
        const formatted = (res.data || []).map((item: any) => ({
          title: item.title,
          artid: item.artid,
          bank: item.bank,
          post_date: item.post_date,
          end_date: item.end_date,
        }));
        setScrapLists(formatted);
      });
  }, []);

  const handleClick = (item: ScrapItem) => {
    navigate(`/detail/${item.artid}`);
  };

  const todayItems = scrapLists.filter((item) =>
    isSameDate(new Date(item.end_date), today)
  );
  const upcomingItems = scrapLists.filter(
    (item) => new Date(item.end_date) > today
  );
  const expiredItems = scrapLists.filter(
    (item) => new Date(item.end_date) < today
  );

  const renderList = (list: ScrapItem[]) => (
  <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
    {list.map((item) => {
      const isSelected = selectedItems.has(item.artid);
      return (
        <li
          key={item.artid}
          onClick={() => {
            if (!isEditing) handleClick(item);
          }}
          style={{
            border: isSelected ? "2px solid #007bff" : "1px solid #e5e5e5",
            padding: "16px 0",
            cursor: isEditing ? "default" : "pointer",
            display: "flex",
            alignItems: "center",
            gap: "16px",
            paddingLeft: "12px",
            paddingRight: "12px",
            borderRadius: "8px",
            backgroundColor: isSelected ? "#f0f8ff" : "white",
          }}
        >
          <img src={getBankLogo(item.bank)} alt={item.bank} style={{ height: "30px" }} />
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 600, fontSize: "16px", color: "#1e1e1e", lineHeight: "1.5" }}>{item.title}</div>
            <div style={{ fontSize: "13px", color: "#888", marginTop: "6px" }}>
              마감일: {formatKoreanDate(item.end_date)}
            </div>
          </div>
          {isEditing && (
            <button
              onClick={() => {
                const newSet = new Set(selectedItems);
                if (newSet.has(item.artid)) {
                  newSet.delete(item.artid);
                } else {
                  newSet.add(item.artid);
                }
                setSelectedItems(newSet);
              }}
              style={{
                border: "none",
                background: "transparent",
                color: "#bba",
                fontSize: "20px",
                cursor: "pointer",
              }}
            >
              ✕
            </button>
          )}
        </li>
      );
    })}
  </ul>
);


  return (
      <div style={{padding: "40px", backgroundColor: "#f9f9f9", minHeight: "100vh"}}>
          <div
              style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "flex-end",
                  marginBottom: "32px",
              }}
          >
              <h2 style={{fontSize: "28px", color: "#1a1a1a", fontWeight: 700, letterSpacing: "-0.5px"}}>스크랩 공고 목록</h2>
              <div style={{display: "flex", gap: "12px", alignItems: "center"}}>
                  <div style={{fontSize: "14px", color: "#666"}}>{todayStr}</div>
                  {!isEditing && (
  <button onClick={() => {
    setIsEditing(true);
    setSelectedItems(new Set());
  }}>
    편집
  </button>
)}
{isEditing && (
  <>
    {selectedItems.size > 0 && (
      <button onClick={() => handleConfirmSelection()}>확인</button>
    )}
    <button
      onClick={() => {
        setSelectedItems(new Set()); // 선택만 초기화, 편집 유지
      }}
    >
      취소
    </button>
  </>
)}

              </div>
          </div>


          <div
              style={{
                  ...cardBoxStyle,
                  marginBottom: "40px",
              }}
          >
              <h3 style={sectionTitleStyle}>금일 마감 공고</h3>
              {todayItems.length > 0 ? (
                  renderList(todayItems)
              ) : (
                  <div style={emptyTextStyle}>금일 마감된 공고가 없습니다.</div>
              )}
          </div>

          <div style={{display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px"}}>
              <div style={cardBoxStyle}>
                  <h3 style={sectionTitleStyle}>진행 중 공고</h3>
                  {upcomingItems.length > 0 ? (
                      renderList(upcomingItems)
                  ) : (
                      <div style={emptyTextStyle}>진행 중 공고가 없습니다.</div>
                  )}
              </div>

              <div style={cardBoxStyle}>
                  <h3 style={sectionTitleStyle}>마감된 공고</h3>
                  {expiredItems.length > 0 ? (
                      renderList(expiredItems)
                  ) : (
                      <div style={emptyTextStyle}>마감된 공고가 없습니다.</div>
                  )}
              </div>
          </div>
      </div>
  );
}

const cardBoxStyle: React.CSSProperties = {
    backgroundColor: "#ffffff",
    border: "1px solid #d9d9d9",
    borderRadius: "12px",
    padding: "24px",
    boxShadow: "none",
};

const sectionTitleStyle: React.CSSProperties = {
    fontSize: "18px",
    fontWeight: 700,
    color: "#1a1a1a",
    marginBottom: "16px",
    paddingBottom: "10px",
    borderBottom: "1px solid  #007bff",
    letterSpacing: "-0.2px",
};

const emptyTextStyle: React.CSSProperties = {
    color: "#999",
    fontStyle: "italic",
    fontSize: "14px",
};

export default ScrapPage;