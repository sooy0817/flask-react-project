import { useEffect, useState, useRef } from "react";
import { Calendar, dateFnsLocalizer } from "react-big-calendar";
import { format } from "date-fns/format";
import { parse } from "date-fns/parse";
import { startOfWeek } from "date-fns/startOfWeek";
import { getDay } from "date-fns/getDay";
import "react-big-calendar/lib/css/react-big-calendar.css";
import { useNavigate } from "react-router-dom";
import * as koLocale from "date-fns/locale/ko";
import { getBankLogo } from "../utils/getBankLogo";

const locales = {
  "ko-KR": koLocale,
};

const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek,
  getDay,
  locales,
});




function CalendarPage() {
  const [selectedDateEvents, setSelectedDateEvents] = useState<any[]>([]);
  const navigate = useNavigate();
  const [showAll, setShowAll] = useState(false);
const [scrapEvents, setScrapEvents] = useState<any[]>([]);
const [allEvents, setAllEvents] = useState<any[]>([]);
const events = showAll ? scrapEvents : allEvents;
const [currentDate, setCurrentDate] = useState(new Date());
const detailSectionRef = useRef<HTMLDivElement | null>(null);


    const formatKoreanDate = (dateString: string) => {
      const date = new Date(dateString);
      const year = date.getFullYear();
      const month = date.getMonth() + 1;
      const day = date.getDate();
      return `${year}년 ${month}월 ${day}일`;
    };


useEffect(() => {
  // 스크랩된 이벤트
  fetch("http://localhost:5001/api/scrap/details")
    .then((res) => res.json())
    .then((res) => {
      const formatted = (res.data || []).map((item: any) => ({
        title: item.title,
        start: new Date(item.end_date),
        end: new Date(item.end_date),
        artid: item.artid,
        bank: item.bank,
          post_date: item.post_date,
        end_date: item.end_date,
      }));
      setScrapEvents(formatted);
    });

  // 전체 마감 일정
 fetch("http://localhost:5001/api/all/details")
  .then((res) => res.json())
  .then((res) => {
    const formatted = (res.data || [])
      .filter((item: any) => item.end_date)
      .map((item: any) => ({
        title: item.title,
        start: new Date(item.end_date),
        end: new Date(item.end_date),
        artid: item.artid,
        bank: item.bank,
          post_date: item.post_date,
        end_date: item.end_date,

      }));
    setAllEvents(formatted);
  });

}, []);


  const onSelectDate = (slotInfo: any) => {
    const clickedDate = slotInfo.start.toISOString().slice(0, 10);
    const selected = events.filter(
      (event) => event.start.toISOString().slice(0, 10) === clickedDate
    );
    setSelectedDateEvents(selected);
  };
const EventComponent = ({ event }: any) => {
  const handleMoreClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedDateEvents(event._fullGroup || [event]);
    setTimeout(() => {
      detailSectionRef.current?.scrollIntoView({ behavior: "smooth" });
    }, 0);
  };


  return (
    <div style={{ textAlign: "center", paddingTop: "2px", marginBottom: "4px" }}>
      <img src={getBankLogo(event.bank)} alt={event.bank} style={{ height: "20px" }} />
      <div
        style={{
          fontSize: "13px",
          color: "#333",
          whiteSpace: "normal",
          wordBreak: "break-word",
            display: "-webkit-box",
    WebkitLineClamp: 2,
    WebkitBoxOrient: "vertical",
    overflow: "hidden",
        }}
      >
        {event.title}
      </div>

      {event._extraCount > 0 && (
        <button
          onClick={handleMoreClick}
          style={{
            fontSize: "11px",
            color: "#1976d2",
            background: "none",
            border: "none",
            cursor: "pointer",
            marginTop: "2px",
            textDecoration: "underline",
          }}
        >
          +{event._extraCount} more
        </button>
      )}
    </div>
  );
};



  const getCustomEvents = (events: any[]) => {
  const grouped: Record<string, any[]> = {};

  events.forEach((event) => {
    const dateKey = event.start.toISOString().slice(0, 10);
    if (!grouped[dateKey]) grouped[dateKey] = [];
    grouped[dateKey].push(event);
  });

  const processed = Object.entries(grouped).map(([_, eventList]) => {
    const first = eventList[0];
    const extraCount = eventList.length - 1;

    return {
    ...first,
    _fullGroup: eventList,
    _extraCount: extraCount,
  };
});

  return processed;
};

  const visibleEvents = getCustomEvents(events);


  const EnhancedEventComponent = (props: any) => (
  <EventComponent
    {...props}
    onShowMore={(list: any[]) => {
      setSelectedDateEvents(list);
      setTimeout(() => {
        detailSectionRef.current?.scrollIntoView({ behavior: "smooth" });
      }, 0);
    }}
  />
);


    return (
        <div style={{padding: "30px"}}>
            <h2 style={{fontSize: "32px", marginBottom: "30px", textAlign: "center"}}>공고 마감 일정</h2>
          <button
              onClick={() => setShowAll((prev) => !prev)}
              style={{
                  marginBottom: "20px",
                  padding: "6px 12px",
                  borderRadius: "6px",
                  border: "1px solid #ccc",
                  cursor: "pointer",
              }}
          >
              {showAll ? "📅 전체 마감 보기" : "⭐ 스크랩만 보기"}
          </button>
          <Calendar
              localizer={localizer}
              events={visibleEvents}
              date={currentDate}
              startAccessor="start"
              endAccessor="end"
              views={["month"]}
              selectable
              onSelectSlot={onSelectDate}
                onSelectEvent={(event : any) => {
    setSelectedDateEvents(event._fullGroup || [event]);
  }}
              onNavigate={(newDate) => {
                console.log("📆 달력 이동됨:", newDate);
                setCurrentDate(newDate);
              }}
              components={{ event: EnhancedEventComponent }}

              eventPropGetter={() => ({
                  style: {
                      backgroundColor: "transparent",
                      border: "none",
                      padding: 0,
                  },
              })}
              style={{height: "700px"}}
              popup
              dayPropGetter={() => ({
                  style: {
                      padding: "4px",
                      fontSize: "12px",
                  },
              })}
          />

          {selectedDateEvents.length > 0 && (
              <div ref={detailSectionRef}  style={{marginTop: "30px"}}>
                  <h3 style={{marginBottom: "16px", fontSize: "20px"}}>
                      📅 {selectedDateEvents.length > 0 ? formatKoreanDate(selectedDateEvents[0].end_date) : ""} 마감 공고
                  </h3>


                  <ul style={{listStyle: "none", padding: 0}}>
                      {selectedDateEvents.map((event, idx) => (
                          <li
                              key={idx}
                              onClick={() => navigate(`/detail/${event.artid}`)}
                              style={{
                                  display: "flex",
                                  alignItems: "center",
                                  padding: "10px 12px",
                                  marginBottom: "8px",
                                  backgroundColor: "#f9f9f9",
                                  border: "1px solid #ddd",
                                  borderRadius: "8px",
                                  cursor: "pointer",
                                  transition: "background-color 0.2s",
                              }}
                          >
                              <img
                                  src={getBankLogo(event.bank)}
                                  alt={event.bank}
                                  style={{height: "28px", marginRight: "12px"}}
                              />
                              <div>
                                  <div style={{fontWeight: "bold", fontSize: "16px"}}>{event.title}</div>
                                  <div style={{color: "#666", fontSize: "13px"}}>
                                      📅공고일 : {formatKoreanDate(event.post_date)}
                                  </div>
                              </div>
                          </li>
                      ))}
                  </ul>
              </div>
          )}
      </div>
  );
}

export default CalendarPage;
