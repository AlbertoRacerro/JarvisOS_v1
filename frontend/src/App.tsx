import { useState } from "react";

import Layout from "./components/Layout";
import AIDraft from "./pages/AIDraft";
import BlueCAD from "./pages/BlueCAD";
import Dashboard from "./pages/Dashboard";
import DevLocalChat from "./pages/DevLocalChat";
import DomainFoundation from "./pages/DomainFoundation";
import SystemStatus from "./pages/SystemStatus";

export type AppPage = "dashboard" | "foundation" | "bluecad" | "ai" | "system" | "devlocalchat";

function App() {
  const [page, setPage] = useState<AppPage>("dashboard");

  return (
    <Layout activePage={page} onNavigate={setPage}>
      {page === "dashboard" && <Dashboard />}
      {page === "foundation" && <DomainFoundation />}
      {page === "bluecad" && <BlueCAD />}
      {page === "ai" && <AIDraft />}
      {page === "system" && <SystemStatus />}
      {import.meta.env.DEV && page === "devlocalchat" && <DevLocalChat />}
    </Layout>
  );
}

export default App;
