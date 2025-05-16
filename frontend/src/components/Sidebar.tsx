import React from "react";
import { Link, useLocation } from "react-router-dom";

const Sidebar = () => {
  const location = useLocation();

  const menuStyle = (path: string) => ({
    padding: "16px 24px",
    textDecoration: "none",
    color: location.pathname === path ? "#1976d2" : "#333",
    backgroundColor: location.pathname === path ? "#e3f2fd" : "transparent",
    display: "block",
    fontWeight: location.pathname === path ? "bold" : "normal",
  });

  return (
    <div
      style={{
        width: "220px",
        height: "100vh",
        backgroundColor: "#fafafa",
        borderRight: "1px solid #ccc",
        display: "flex",
        flexDirection: "column",
        paddingTop: "40px",
        boxSizing: "border-box",
        position: "sticky",
        top: 0,
      }}
    >
      <Link to="/calendar" style={menuStyle("/calendar")}>
        📅 공고 마감 일정
      </Link>
      <Link to="/scrap" style={menuStyle("/scrap")}>
        ⭐ 스크랩 공고
      </Link>
    </div>
  );
};

export default Sidebar;
