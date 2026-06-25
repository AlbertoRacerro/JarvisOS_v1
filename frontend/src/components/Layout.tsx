import type { ReactNode } from "react";

import type { AppPage } from "../App";

type LayoutProps = {
  activePage: AppPage;
  children: ReactNode;
  onNavigate: (page: AppPage) => void;
};

function Layout({ activePage, children, onNavigate }: LayoutProps) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">JarvisOS</p>
          <h1>BlueRev Model Foundry</h1>
        </div>
        <nav className="nav" aria-label="Main navigation">
          <button
            className={activePage === "dashboard" ? "nav-button active" : "nav-button"}
            type="button"
            onClick={() => onNavigate("dashboard")}
          >
            Dashboard
          </button>
          <button
            className={activePage === "system" ? "nav-button active" : "nav-button"}
            type="button"
            onClick={() => onNavigate("system")}
          >
            System Status
          </button>
          <button
            className={activePage === "foundation" ? "nav-button active" : "nav-button"}
            type="button"
            onClick={() => onNavigate("foundation")}
          >
            Domain Foundation
          </button>
          <button
            className={activePage === "ai" ? "nav-button active" : "nav-button"}
            type="button"
            onClick={() => onNavigate("ai")}
          >
            AI Draft
          </button>
          {import.meta.env.DEV && (
            <button
              className={activePage === "devlocalchat" ? "nav-button active nav-button--dev" : "nav-button nav-button--dev"}
              type="button"
              onClick={() => onNavigate("devlocalchat")}
            >
              Dev Local Chat
            </button>
          )}
        </nav>
      </aside>
      <main className="main-panel">{children}</main>
    </div>
  );
}

export default Layout;
