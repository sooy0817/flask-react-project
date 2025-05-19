import { useEffect, useState } from "react";
import { useParams, useLocation, useNavigate } from "react-router-dom";
import { ClipLoader } from "react-spinners";
import { getBankLogo } from "../utils/getBankLogo";

function DetailPage() {
  const { state } = useLocation();
  const { artid } = useParams();
  const navigate = useNavigate();

  const [selectedItem, setSelectedItem] = useState<any>(state || null);
  const [summaryText, setSummaryText] = useState<any | null>(null);
  const [loadingType, setLoadingType] = useState<"llm" | "db" | null>(null);
  const [summaryType, setSummaryType] = useState<"openai" | "ollama" | "gemma3" | "llama3">("openai");


  useEffect(() => {
    if (!state && artid) {
      fetch("http://localhost:5001/api/all-banks")
        .then((res) => res.json())
        .then((list) => {
          const match = list.find((item: any) => String(item.artid) === String(artid));
          if (match) setSelectedItem(match);
        })
        .catch((err) => console.error("데이터 로딩 실패:", err));
    }
  }, [state, artid]);

  useEffect(() => {
    if (selectedItem) {
      const endpoint = "/api/summary";
      setLoadingType(selectedItem.summary ? "db" : "llm");

      fetch(`http://localhost:5001${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          artid: selectedItem.artid,
          title: selectedItem.title,
          content_path: selectedItem.content_path,
          attachments: selectedItem.attachments,
          use_ollama: summaryType === "ollama" || summaryType === "gemma3" || summaryType === "llama3",
          cache_table:
            summaryType === "gemma3"
              ? "summary_cache_gemma3"
              : summaryType === "llama3"
              ? "summary_cache_llama3"
              : undefined,
          ollama_model:
            summaryType === "gemma3"
              ? "gemma3"
              : summaryType === "llama3"
              ? "llama3.2:3b"
              : "gemma2:2b",
        }),
      })
        .then((res) => res.json())
        .then((data) => {
          setSummaryText(data.summary);
          setLoadingType(null);
        })
        .catch(() => {
          setSummaryText({ error: "요약 실패" });
          setLoadingType(null);
        });
    }
  }, [selectedItem, summaryType]);

  if (!selectedItem) return <div style={{ padding: "40px" }}>불러오는 중...</div>;

  return (
    <div
      style={{ padding: "40px", fontFamily: "Segoe UI, sans-serif", backgroundColor: "#f9f9f9", minHeight: "100vh" }}>
      <div className="header-container">
        <div className="header-container-left">
          <img src={getBankLogo(selectedItem.bank)} alt={`${selectedItem.bank} 로고`} />
          <h2>{selectedItem.title}</h2>
        </div>
        <button className="back-button" onClick={() => navigate(-1)}>
          ← 목록으로 돌아가기
        </button>
      </div>

      {/* 첨부파일 */}
      {selectedItem?.attachments?.length > 0 && (
        <div style={{ marginBottom: "24px" }}>
          <h4 style={{ marginBottom: "8px" }}>📎 첨부파일</h4>
          <ul style={{ listStyle: "none", paddingLeft: 0 }}>
            {selectedItem.attachments.map((file: any, idx: number) => (
              <li key={idx} style={{ marginBottom: "4px" }}>
                <a
                  href={`http://localhost:5001${file.file_url}`}
                  download
                  target="_blank"
                  rel="noreferrer"
                  style={{ color: "#007bff", textDecoration: "none" }}>
                  📎 {file.file_name}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 요약 + PDF */}
      <div style={{ marginBottom: "20px" }}>
        <button onClick={() => setSummaryType("openai")}>🤖 OpenAI 요약</button>
        <button onClick={() => setSummaryType("ollama")}>🦙 Ollama - gemma2-2b 요약</button>
        <button onClick={() => setSummaryType("gemma3")}>🧠 Ollama - gemma3 요약</button>
        <button onClick={() => setSummaryType("llama3")}>🦙 Ollama - llama3.1:8b 요약</button>
      </div>

      <div style={{ display: "flex", gap: "24px" }}>
        {/* 요약 영역 */}
        <div
          style={{
            flex: 1,
            backgroundColor: "#ffffff",
            padding: "20px",
            borderRadius: "10px",
            boxShadow: "0 4px 12px rgba(0,0,0,0.05)",
            overflowY: "auto",
            maxHeight: "80vh",
          }}>
          <h4 style={{ marginBottom: "16px", fontSize: "18px", color: "#333" }}>📄 요약 결과</h4>

          {loadingType === "llm" && (
            <div style={{ textAlign: "center", paddingTop: "20px" }}>
              <ClipLoader color="#007bff" size={35} />
              <p style={{ color: "#999", marginTop: "12px" }}>요약중...</p>
            </div>
          )}

          {loadingType === "db" && (
            <div style={{ textAlign: "center", paddingTop: "20px" }}>
              <p style={{ color: "#999" }}>요약 내용 불러오는 중...</p>
            </div>
          )}

          {!loadingType && Array.isArray(summaryText?.summary) ? (
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <tbody>
                {summaryText.summary.map((item: any, idx: number) => (
                  <tr key={idx}>
                    <td
                      style={{
                        fontWeight: "bold",
                        padding: "8px",
                        borderBottom: "1px solid #e0e0e0",
                        width: "30%",
                        verticalAlign: "top",
                      }}>
                      {item.항목}
                    </td>
                    <td style={{ padding: "8px", borderBottom: "1px solid #e0e0e0" }}>{item.내용}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : null}
        </div>

        {/* PDF 미리보기 영역 */}
        {selectedItem?.content_path && (
          <div
            style={{
              flex: 2,
              borderRadius: "10px",
              overflow: "hidden",
              boxShadow: "0 4px 12px rgba(0,0,0,0.05)",
            }}>
            <iframe
              src={`http://localhost:5001${selectedItem.content_path}#zoom=120`}
              style={{ width: "100%", height: "80vh", border: "none" }}
              title="PDF 미리보기"
            />
          </div>
        )}
      </div>
    </div>
  );
}

export default DetailPage;
