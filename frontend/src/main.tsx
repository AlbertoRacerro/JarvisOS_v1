import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App";
import { applyStoredAppearance } from "./theme";
import "./styles/tokens.css";
import "./styles/global.css";
import "./styles/foundation.css";
import "./styles/shell.css";
import "./styles/runs.css";
import "./styles/engineering-data.css";
import "./styles/analytics.css";
import "./styles/review.css";
import "./styles/ai-threads.css";
import "./styles/settings.css";
import "./styles/responsive.css";

applyStoredAppearance();

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
