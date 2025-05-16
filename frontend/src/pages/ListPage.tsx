import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getBankLogo } from "../utils/getBankLogo";
import { FaChevronLeft, FaChevronRight, FaUserCircle, FaStar, FaRegCalendarAlt } from "react-icons/fa";

function ListPage() {
  const [data, setData] = useState<any[]>([]);
  const [searchKeyword, setSearchKeyword] = useState("");
  const [selectedBank, setSelectedBank] = useState("전체");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [isCrawling, setIsCrawling] = useState(false);
  const [selectMode, setSelectMode] = useState(false);
  const [selectedArtIds, setSelectedArtIds] = useState<string[]>([]);
  const [scrappedArtIds, setScrappedArtIds] = useState<string[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;
  const navigate = useNavigate();

  const filteredData = data.filter((item) => {
    const matchKeyword = item.title.includes(searchKeyword);
    const matchBank = selectedBank === "전체" || item.bank === selectedBank;
    const itemDate = new Date(item.date);
    const from = startDate ? new Date(startDate) : null;
    const to = endDate ? new Date(endDate) : null;
    const matchDate = (!from || itemDate >= from) && (!to || itemDate <= to);
    return matchKeyword && matchBank && matchDate;
  });

  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = (currentPage - 1) * itemsPerPage;
  const paginatedData = filteredData.slice(indexOfFirstItem, indexOfLastItem);
  const totalPages = Math.ceil(filteredData.length / itemsPerPage);

  useEffect(() => {
    fetch("http://localhost:5001/api/all-banks")
      .then((res) => res.json())
      .then((json) => setData(json))
      .catch((err) => console.error("Error fetching data:", err));

    fetch("http://localhost:5001/api/scrap")
      .then((res) => res.json())
      .then((json) => setScrappedArtIds(json.artids))
      .catch((err) => console.error("스크랩 상태 가져오기 실패", err));
  }, []);

  useEffect(() => {
    setCurrentPage(1);
  }, [searchKeyword, selectedBank, startDate, endDate]);

  const handleManualCrawl = async () => {
    if (isCrawling) return;
    setIsCrawling(true);
    try {
      const res = await fetch("http://localhost:5001/api/run-crawler", { method: "POST" });
      const result = await res.json();
      alert(result.message);
      const refreshed = await fetch("http://localhost:5001/api/all-banks");
      const json = await refreshed.json();
      setData(json);
    } catch (err) {
      alert("크롤링 실패! 서버를 확인하세요.");
    } finally {
      setIsCrawling(false);
    }
  };

  const handleScrapConfirm = async () => {
  try {
    // 1. 저장할 전체 item 목록 구성 (selectedArtIds를 기반으로)
    const scrapItems = data
      .filter((item) => selectedArtIds.includes(item.artid))
      .map((item) => ({
        artid: item.artid,
        title: item.title,
        bank: item.bank,
        date: item.date,
        content_path: item.content_path,
      }));

    // 2. 서버에 스크랩 저장 요청
    await fetch("http://localhost:5001/api/scrap", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ items: scrapItems })
    });

    // 3. 체크 해제된 항목 삭제
    const toDelete = scrappedArtIds.filter(id => !selectedArtIds.includes(id));
    if (toDelete.length > 0) {
      await fetch("http://localhost:5001/api/scrap/delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ artids: toDelete })
      });
    }

    // 4. UI 상태 반영
    setScrappedArtIds(selectedArtIds);
    setSelectedArtIds([]);
    setSelectMode(false);
  } catch (err) {
    alert("스크랩 저장/삭제 실패");
    console.error(err); // 에러 로그도 확인
  }
};


  const handleToggleSelectMode = () => {
    setSelectMode((prev) => {
      if (!prev) {
        const initialChecked = filteredData.filter((item) => scrappedArtIds.includes(item.artid)).map((item) => item.artid);
        setSelectedArtIds(initialChecked);
      }
      return !prev;
    });
  };

  return (
    <div>
      <div style={{ maxWidth: "1200px", margin: "0 auto", padding: "40px", fontFamily: "Segoe UI, sans-serif" }}>
        <h2 style={{ fontSize: "45px", marginBottom: "10px", color: "#333", textAlign: "center" }}>입찰 공고 리스트</h2>

        <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginBottom: "10px" }}>
          <button
            onClick={() => navigate("/calendar")}
            style={{ display: "flex", alignItems: "center", gap: "8px", backgroundColor: "#fff", color: "#007bff", border: "1px solid #007bff", padding: "8px 16px", borderRadius: "8px", cursor: "pointer", fontSize: "16px", boxShadow: "0 2px 8px rgba(0,0,0,0.05)" }}>
            <FaRegCalendarAlt size={20} />
            공고 마감 일정
          </button>
          {!selectMode ? (
            <button onClick={handleToggleSelectMode} style={{ padding: "8px 16px", borderRadius: "8px", backgroundColor: "#f0f0f0" }}>📌 스크랩</button>
          ) : (
            <button onClick={handleScrapConfirm} style={{ padding: "8px 16px", borderRadius: "8px", backgroundColor: "#199fff", color: "white" }}>확인</button>
          )}
        </div>

        <div style={{ height: "1px", backgroundColor: "#ddd", marginBottom: "40px" }} />

        <div style={{ display: "flex", flexWrap: "wrap", gap: "12px", marginBottom: "24px", alignItems: "center" }}>
          <input type="text" placeholder="공고 검색" value={searchKeyword} onChange={(e) => setSearchKeyword(e.target.value)} style={{ padding: "8px 12px", borderRadius: "6px", border: "1px solid #ccc", flex: 1 }} />
          <select value={selectedBank} onChange={(e) => setSelectedBank(e.target.value)} style={{ padding: "8px 12px", borderRadius: "6px", border: "1px solid #ccc", flex: 1 }}>
            <option value="전체">전체 은행</option>
            {[...new Set(data.map((item) => item.bank))].map((bank, idx) => (
              <option key={idx} value={bank}>{bank}</option>
            ))}
          </select>
          <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} style={{ padding: "8px", borderRadius: "6px", border: "1px solid #ccc" }} />
          <span style={{ fontSize: "14px" }}>~</span>
          <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} style={{ padding: "8px", borderRadius: "6px", border: "1px solid #ccc" }} />
          <button onClick={handleManualCrawl} disabled={isCrawling} style={{ padding: "8px 16px", backgroundColor: isCrawling ? "#bbb" : "#007bff", color: "white", border: "none", borderRadius: "6px" }}>
            {isCrawling ? "크롤링 중..." : "수동 크롤링 실행"}
          </button>
        </div>

        <table style={{ width: "100%", borderCollapse: "collapse", backgroundColor: "#fff", borderRadius: "8px", overflow: "hidden", boxShadow: "0 4px 12px rgba(0, 0, 0, 0.05)" }}>
          <thead>
            <tr style={{ backgroundColor: "#f0f2f5", textAlign: "left" }}>
              <th style={{ padding: "12px 16px", width: "20%" }}>은행명</th>
              <th style={{ padding: "12px 16px", width: "60%" }}>입찰공고명</th>
              <th style={{ padding: "12px 16px", width: "15%" }}>게시일</th>
              <th style={{ padding: "12px 16px", width: "5%", textAlign: "center" }}>⭐</th>
            </tr>
          </thead>
          <tbody>
            {paginatedData.map((item) => (
              <tr
                key={item.artid}
                style={{ cursor: "pointer", borderTop: "1px solid #eee", transition: "background-color 0.2s ease" }}
                onMouseOver={(e) => (e.currentTarget.style.backgroundColor = "#f9fbfc")}
                onMouseOut={(e) => (e.currentTarget.style.backgroundColor = "white")}
              >
                <td style={{ padding: "12px 16px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <img src={getBankLogo(item.bank)} alt="로고" style={{ width: "20px", height: "20px" }} />
                    <span>{item.bank}</span>
                  </div>
                </td>
                <td style={{ padding: "12px 16px", wordBreak: "break-word" }} onClick={() => navigate(`/detail/${item.artid}`, { state: item })}>{item.title}</td>
                <td style={{ padding: "12px 16px", color: "#666" }}>{item.date.replace(/-/g, ".")}</td>
                <td style={{ textAlign: "center" }}>
                  {selectMode ? (
                    <input
                      type="checkbox"
                      checked={selectedArtIds.includes(item.artid)}
                      onChange={(e) => {
                        const checked = e.target.checked;
                        setSelectedArtIds((prev) =>
                          checked ? [...prev, item.artid] : prev.filter((id) => id !== item.artid)
                        );
                      }}
                    />
                  ) : scrappedArtIds.includes(item.artid) ? (
                    <FaStar color="#f2b01e" title="스크랩됨" />
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {totalPages > 1 && (
          <div style={{ textAlign: "center", marginTop: "20px" }}>
            <button onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))} disabled={currentPage === 1}><FaChevronLeft /> 이전</button>
            <span style={{ margin: "0 12px", fontWeight: "bold" }}>{currentPage} / {totalPages}</span>
            <button onClick={() => setCurrentPage((prev) => Math.min(prev + 1, totalPages))} disabled={currentPage === totalPages}>다음 <FaChevronRight /></button>
          </div>
        )}
      </div>
    </div>
  );
}

export default ListPage;
