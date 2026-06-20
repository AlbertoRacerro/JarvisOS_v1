import { useState } from "react";

import Layout from "./components/Layout";
import AIDraft from "./pages/AIDraft";
import Dashboard from "./pages/Dashboard";
import DomainFoundation from "./pages/DomainFoundation";
import SystemStatus from "./pages/SystemStatus";

export type AppPage = "dashboard" | "foundation" | "ai" | "system";

function App() {
  const [page, setPage] = useState<AppPage>("dashboard");

  return (
    <Layout activePage={page} onNavigate={setPage}>
      {page === "dashboard" && <Dashboard />}
      {page === "foundation" && <DomainFoundation />}
      {page === "ai" && <AIDraft />}
      {page === "system" && <SystemStatus />}
    </Layout>
  );
}

export default App;
