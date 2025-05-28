import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

function SimilarPage() {
  const [searchParams] = useSearchParams();
  const artid = searchParams.get("artid");
  const API_URL = import.meta.env.VITE_API_URL;

  const [targetItem, setTargetItem] = useState<any | null>(null);
  const [similarList, setSimilarList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!artid) return;
    async function fetchTargetAndSimilar() {
      try {
        const res = await fetch(`${API_URL}/api/all-banks`);
        const list = await res.json();
        const match = list.find((item: any) => String(item.artid) === String(artid));
        if (!match) throw new Error("기준 공고를 찾을 수 없습니다.");
        setTargetItem(match);

        const similarRes = await fetch(`${API_URL}/api/similar-faiss`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title: match.title }),
        });
        const similarData = await similarRes.json();
        setSimilarList(similarData?.results || []);
      } catch (error) {
        console.error("❌ 유사공고 검색 실패:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchTargetAndSimilar();
  }, [artid, API_URL]);

  const formatDate = (date: string) => new Date(date).toLocaleDateString();

  return (
    <div style={{ padding: "40px", fontFamily: "Arial, sans-serif", backgroundColor: "#f9f9f9" }}>
      <h2 style={{ fontSize: "24px", fontWeight: "bold", marginBottom: "20px" }}>📚 유사 입찰공고 결과</h2>

{targetItem && (
  <div style={{ backgroundColor: "#e0f7fa", padding: "20px", borderRadius: "10px", marginBottom: "20px" }}>
    <h3 style={{ fontSize: "18px", margin: "0 0 10px 0", color: "#00796b" }}>기준 공고</h3>
    <p style={{ margin: "0", fontWeight: "bold", fontSize: "20px", color: "#333" }}>{targetItem.title}</p>
  </div>
)}


      {loading ? (
        <p>로딩 중...</p>
      ) : similarList.length === 0 ? (
        <p>❌ 유사 공고를 찾을 수 없습니다.</p>
      ) : (
        <>
          {/* 기존 카드 리스트 */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "20px", marginBottom: "40px" }}>
            {similarList.map((item, idx) => (
              <div key={idx} style={{ backgroundColor: "white", borderRadius: "10px", boxShadow: "0 2px 5px rgba(0,0,0,0.1)", padding: "20px", transition: "transform 0.2s", cursor: "pointer" }}>
                <a
                  href={item.url}
                  target="_blank"
                  rel="noreferrer"
                  style={{ fontSize: "16px", fontWeight: "bold", color: "#007bff", textDecoration: "none" }}
                >
                  {item.title}
                </a>
                <p style={{ fontSize: "14px", margin: "10px 0 0 0" }}>
                  🏢 {item.bank} | 📅 {formatDate(item.date)} | 🔎 유사도: {item.similarity.toFixed(3)}
                </p>
                <p style={{ fontSize: "14px", margin: "5px 0" }}>
                  💰 예상금액: {item.estimated_price?.toLocaleString() || "정보 없음"} | 계약방식: {item.contract_method} | 입찰방식: {item.bid_method}
                </p>
                {item.winner && (
                  <p style={{ fontSize: "14px", margin: "5px 0" }}>
                    🏆 낙찰자: {item.winner} | 💵 {item.winning_price?.toLocaleString() || "정보 없음"} | 💯 {item.winning_rate}%
                  </p>
                )}
              </div>
            ))}
          </div>

          {/* 비교 표 */}
          <h3 style={{fontSize: "20px", fontWeight: "bold", marginBottom: "10px"}}>📊 비교 표</h3>
          <div style={{overflowX: "auto", maxWidth: "100%"}}>
            <table style={{
              width: "100%",
              borderCollapse: "collapse",
              backgroundColor: "white",
              tableLayout: "fixed"
            }}>
              <colgroup>
                <col style={{width: "150px"}}/>
                {/* 항목 */}
                <col style={{width: "200px"}}/>
                {/* 기준 공고 */}
                {similarList.map((_, idx) => <col key={idx} style={{width: "200px"}}/>)}
              </colgroup>
              <thead>
              <tr style={{backgroundColor: "#007bff", color: "white"}}>
                <th style={{
                  padding: "12px",
                  border: "1px solid #ddd",
                  position: "sticky",
                  left: 0,
                  backgroundColor: "#007bff",
                  zIndex: 3
                }}>항목
                </th>
                <th style={{
                  padding: "12px",
                  border: "1px solid #ddd",
                  position: "sticky",
                  left: 150,  // 첫 번째 열의 width 만큼 offset
                  backgroundColor: "#080fff",
                  zIndex: 2
                }}>기준 공고
                </th>
                {similarList.map((_, idx) => (
                    <th key={idx} style={{padding: "12px", border: "1px solid #ddd"}}>유사공고 {idx + 1}</th>
                ))}
              </tr>
              </thead>
              <tbody>
              {[
                {label: "제목", values: [targetItem.title, ...similarList.map(i => i.title)]},
                {label: "기관", values: [targetItem.bank, ...similarList.map(i => i.bank)]},
                {label: "공고일", values: [formatDate(targetItem.date), ...similarList.map(i => formatDate(i.date))]},
                {label: "유사도", values: ["-", ...similarList.map(i => i.similarity.toFixed(3))]},
                {
                  label: "예상금액",
                  values: [targetItem.estimated_price?.toLocaleString() || "정보 없음", ...similarList.map(i => i.estimated_price?.toLocaleString() || "정보 없음")]
                },
                {
                  label: "계약방식",
                  values: [targetItem.contract_method || "정보 없음", ...similarList.map(i => i.contract_method || "정보 없음")]
                },
                {
                  label: "입찰방식",
                  values: [targetItem.bid_method || "정보 없음", ...similarList.map(i => i.bid_method || "정보 없음")]
                },
              ].map((row, idx) => (
                  <tr key={idx} style={{backgroundColor: idx % 2 === 0 ? "#f9f9f9" : "white"}}>
                    <td style={{
                      padding: "10px",
                      border: "1px solid #ddd",
                      position: "sticky",
                      left: 0,
                      backgroundColor: "#f1f1f1",
                      zIndex: 2,
                      fontWeight: "bold",
                      wordBreak: "break-word"
                    }}>{row.label}</td>
                    <td style={{
                      padding: "10px",
                      border: "1px solid #ddd",
                      position: "sticky",
                      left: 150,
                      backgroundColor: "#f9f9f9",
                      zIndex: 1,
                      wordBreak: "break-word"
                    }}>{row.values[0]}</td>
                    {row.values.slice(1).map((val, vIdx) => (
                        <td key={vIdx}
                            style={{padding: "10px", border: "1px solid #ddd", wordBreak: "break-word"}}>{val}</td>
                    ))}
                  </tr>
              ))}
              {similarList.some(i => i.winner) && (
                  <>
                    <tr>
                      <td style={{
                        padding: "10px",
                        border: "1px solid #ddd",
                        position: "sticky",
                        left: 0,
                        backgroundColor: "#f1f1f1",
                        zIndex: 2,
                        fontWeight: "bold"
                      }}>낙찰자
                      </td>
                      <td style={{
                        padding: "10px",
                        border: "1px solid #ddd",
                        position: "sticky",
                        left: 150,
                        backgroundColor: "#f9f9f9",
                        zIndex: 1
                      }}>-
                      </td>
                      {similarList.map((i, idx) => <td key={idx}>{i.winner || "정보 없음"}</td>)}
                    </tr>
                    <tr>
                      <td style={{
                        padding: "10px",
                        border: "1px solid #ddd",
                        position: "sticky",
                        left: 0,
                        backgroundColor: "#f1f1f1",
                        zIndex: 2,
                        fontWeight: "bold"
                      }}>낙찰금액
                      </td>
                      <td style={{
                        padding: "10px",
                        border: "1px solid #ddd",
                        position: "sticky",
                        left: 150,
                        backgroundColor: "#f9f9f9",
                        zIndex: 1
                      }}>-
                      </td>
                      {similarList.map((i, idx) => <td key={idx}>{i.winning_price?.toLocaleString() || "정보 없음"}</td>)}
                    </tr>
                    <tr>
                      <td style={{
                        padding: "10px",
                        border: "1px solid #ddd",
                        position: "sticky",
                        left: 0,
                        backgroundColor: "#f1f1f1",
                        zIndex: 2,
                        fontWeight: "bold"
                      }}>낙찰률
                      </td>
                      <td style={{
                        padding: "10px",
                        border: "1px solid #ddd",
                        position: "sticky",
                        left: 150,
                        backgroundColor: "#f9f9f9",
                        zIndex: 1
                      }}>-
                      </td>
                      {similarList.map((i, idx) => <td
                          key={idx}>{i.winning_rate ? `${i.winning_rate}%` : "정보 없음"}</td>)}
                    </tr>
                  </>
              )}
              </tbody>
            </table>
          </div>

        </>
      )}
    </div>
  );
}

export default SimilarPage;