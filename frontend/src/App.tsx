import React, { useEffect, useState } from "react";
import { getBankLogo } from './utils/getBankLogo';

function App() {
  const [data, setData] = useState<any[]>([]);
  const [selectedItem, setSelectedItem] = useState<any | null>(null);
  const [isCrawling, setIsCrawling] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState("");
  const [selectedBank, setSelectedBank] = useState("전체");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const filteredData = data.filter((item) => {
  const matchKeyword = item.title.includes(searchKeyword);
  const matchBank = selectedBank === "전체" || item.bank === selectedBank;
  const itemDate = new Date(item.date);
  const from = startDate ? new Date(startDate) : null;
  const to = endDate ? new Date(endDate) : null;
  const matchDate =
    (!from || itemDate >= from) && (!to || itemDate <= to);

  return matchKeyword && matchBank && matchDate;
});
  const handleManualCrawl = async () => {
    if (isCrawling) return; // 중복 방지
    setIsCrawling(true);
    try {
      const res = await fetch("http://localhost:5001/api/run-crawler", {
        method: "POST",
      });
      const result = await res.json();
      alert(result.message);

      // ✅ 크롤링 후 데이터 다시 불러오기
      const refreshed = await fetch("http://localhost:5001/api/all-banks");
      const json = await refreshed.json();
      setData(json);
    } catch (err) {
      alert("크롤링 실패! 서버를 확인하세요.");
    } finally {
      setIsCrawling(false);
    }
  };


  useEffect(() => {
    fetch("http://192.168.140.23:5001/api/all-banks")
      .then((res) => res.json())
      .then((json) => setData(json))
      .catch((err) => console.error("Error fetching data:", err));
  }, []);

  return (
      <div style={{display: "flex", height: "100vh"}}>
          {/* 왼쪽 리스트 */}


          <div
              style={{
                  flex: 4,
                  padding: "20px",
                  overflowY: "scroll",
                  borderRight: "1px solid #ccc",
              }}
          >
              <h2>📄 입찰 공고 리스트</h2>
              <div style={{marginBottom: "16px"}}>
                  <input
                      type="text"
                      placeholder="공고 검색"
                      value={searchKeyword}
                      onChange={(e) => setSearchKeyword(e.target.value)}
                      style={{marginRight: "10px", padding: "4px"}}
                  />
                  <select
                      value={selectedBank}
                      onChange={(e) => setSelectedBank(e.target.value)}
                      style={{marginRight: "10px", padding: "4px"}}
                  >
                      <option value="전체">전체 은행</option>
                      {[...new Set(data.map(item => item.bank))].map((bank, idx) => (
                          <option key={idx} value={bank}>{bank}</option>
                      ))}
                  </select>
                  <input
                      type="date"
                      value={startDate}
                      onChange={(e) => setStartDate(e.target.value)}
                      style={{marginRight: "6px"}}
                  />
                  <span>~</span>
                  <input
                      type="date"
                      value={endDate}
                      onChange={(e) => setEndDate(e.target.value)}
                      style={{marginLeft: "6px"}}
                  />
                  <button
                      onClick={() => {
                          setStartDate("");
                          setEndDate("");
                      }}
                      style={{
                          marginTop: "8px",
                          padding: "2px 2px",
                          backgroundColor: "#eee",
                          border: "1px solid #ccc",
                          borderRadius: "4px",
                          cursor: "pointer"
                      }}
                  >
                      초기화
                  </button>
                  <div style={{marginBottom: "12px"}}>
                      <button
    onClick={handleManualCrawl}
    disabled={isCrawling}
    style={{
      padding: "6px 12px",
      backgroundColor: isCrawling ? "#bbb" : "#4caf50",
      color: "white",
      border: "none",
      borderRadius: "4px",
      cursor: isCrawling ? "not-allowed" : "pointer",
      marginBottom: "8px"
    }}
  >
    {isCrawling ? "크롤링 중..." : "수동 크롤링 실행"}
                      </button>
                  </div>

              </div>
              <table style={{width: "100%", borderCollapse: "collapse", tableLayout: "fixed"}}>
                  <thead>
                  <tr>
                      <th style={{borderBottom: "1px solid #ccc", textAlign: "left", padding: "8px", width: "20%"}}>
                          은행명
                      </th>
                      <th style={{borderBottom: "1px solid #ccc", textAlign: "left", padding: "8px", width: "80%"}}>
                          입찰공고명
                      </th>
                      <th style={{borderBottom: "1px solid #ccc", textAlign: "left", padding: "8px", width: "20%"}}>
                          게시일
                      </th>
                      <th style={{borderBottom: "1px solid #ccc", textAlign: "left", padding: "8px", width: "5%"}}>
                          {/* 첨부 */}
                      </th>
                  </tr>
                  </thead>
                  <tbody>
                  {filteredData.map((item) => {
                      const formattedDate = item.date ? item.date.replace(/-/g, ".") : "";
                      return (
                          <tr>
                              <td style={{padding: "8px", borderBottom: "1px solid #eee"}}>
                                  <div style={{display: "flex", alignItems: "center", gap: "8px"}}>
                                      <img
                                          src={getBankLogo(item.bank)}
                                          alt={`${item.bank} 로고`}
                                          style={{width: "20px", height: "20px", objectFit: "contain"}}
                                      />
                                      <span>{item.bank}</span>
                                  </div>
                              </td>
                              <td style={{padding: "8px", borderBottom: "1px solid #eee"}}>
                                  <div
                                      onClick={() => setSelectedItem(item)}
                                      style={{
                                          cursor: "pointer",
                                          color: "#007bff",
                                          fontSize: "1rem",
                                          lineHeight: "1.4",
                                          display: "-webkit-box",
                                          WebkitLineClamp: 2,
                                          WebkitBoxOrient: "vertical",
                                          overflow: "hidden",
                                          textOverflow: "ellipsis",
                                          wordBreak: "keep-all",
                                      }}
                                  >
                                      {item.title}
                                  </div>
                              </td>
                              <td style={{padding: "8px", borderBottom: "1px solid #eee"}}>
                                  {formattedDate}
                              </td>
                              <td style={{padding: "8px", borderBottom: "1px solid #eee", textAlign: "center"}}>
                                  {item.attachments?.length > 0 ? "📎" : ""}
                              </td>
                          </tr>

                      );
                  })}
                  </tbody>
              </table>
          </div>

          {/* 오른쪽 PDF 미리보기 */}
          <div
              style={{
                  flex: 6,
                  padding: "20px",
                  display: "flex",
                  flexDirection: "column",
                  height: "100vh",
              }}
          >
              {selectedItem ? (
                  <>
                      {/* 첨부파일 */}
                      <div style={{marginBottom: "20px"}}>
                          <h4 style={{marginBottom: "10px"}}>첨부파일</h4>
                          <ul
                              style={{
                                  display: "grid",
                                  gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
                                  gap: "6px 20px",
                                  listStyleType: "disc",
                                  paddingLeft: "20px",
                                  margin: 0,
                              }}
                          >
                              {selectedItem.attachments?.length > 0 ? (
                                  selectedItem.attachments.map((file: any, idx: number) => (
                                      <li
                                          key={idx}
                                          style={{
                                              whiteSpace: "nowrap",
                                              overflow: "hidden",
                                              textOverflow: "ellipsis",
                                              listStylePosition: "inside",
                                          }}
                                      >
                                          <a
                                              href={
                                                  file.file_url.startsWith("/files/woori/")
                                                      ? `http://localhost:5001${file.file_url}`
                                                      : file.file_url
                                              }
                                              target="_blank"
                                              rel="noreferrer"
                                              style={{color: "#3366cc", textDecoration: "none"}}
                                          >
                                              📎 {file.file_name}
                                          </a>
                                      </li>
                                  ))
                              ) : (
                                  <li style={{color: "#888"}}>첨부파일 없음</li>
                              )}
                          </ul>
                      </div>


                      {/* PDF 미리보기 */}
                      <iframe
                          src={`http://localhost:5001/${selectedItem.content_path}#zoom=120`}
                          style={{
                              width: "100%",
                              height: "calc(100vh - 100px)",
                              border: "none",
                          }}
                          title="PDF 미리보기"
                      />
                  </>
              ) : (
                  <div>우측에 PDF 미리보기가 나타납니다.</div>
              )}

          </div>
      </div>
  );
}

export default App;
