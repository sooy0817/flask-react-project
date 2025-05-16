import React from "react";
import Sidebar from "../components/Sidebar";
import { Outlet, useNavigate } from "react-router-dom";
import { FaHome } from "react-icons/fa";

const DefaultLayout = () => {
  const navigate = useNavigate();

  return (
    <div style={{ display: "flex", height: "100vh" }}>
      <Sidebar />
      <div style={{ flex: 1, overflow: "auto", padding: "24px", position: "relative" }}>
        {/* 홈 버튼 - 우측 상단 */}
        <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: "5px" }}>
          <button
            onClick={() => navigate("/")}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              backgroundColor: "#fff",
              color: "#007bff",
              border: "1px solid #007bff",
              padding: "8px 16px",
              borderRadius: "8px",
              cursor: "pointer",
              fontSize: "16px",
              boxShadow: "0 2px 8px rgba(0,0,0,0.05)",
            }}
          >
            <FaHome size={20} />
            홈으로
          </button>
        </div>
        <Outlet />
      </div>
    </div>
  );
};

export default DefaultLayout;
