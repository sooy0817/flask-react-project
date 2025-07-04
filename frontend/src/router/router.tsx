// src/router/router.tsx
import { createBrowserRouter } from "react-router-dom";
import ListPage from "../pages/ListPage";
import DetailPage from "../pages/DetailPage";
import CalendarPage from "../pages/CalendarPage";
import ScrapPage from "../pages/ScrapPage";
import DefaultLayout from "../layouts/DefaultLayout";
import SimilarPage from "../pages/SimilarPage";

const router = createBrowserRouter([
  {
    path: "/",
    element: <ListPage />,
  },
  {
    path: "/detail/:artid",
    element: <DetailPage />,
  },
  {
    path: "/",
    element: <DefaultLayout />,
    children: [
      {
        path: "calendar",
        element: <CalendarPage />,
      },
        {
        path: "scrap",
        element: <ScrapPage />,
      },
        {
        path: "past-similar",
        element: <SimilarPage />,
      },
    ],
  },
]);

export default router;
