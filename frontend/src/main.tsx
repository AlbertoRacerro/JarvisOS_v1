import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App";
import { applyStoredAppearance } from "./theme";
import "./styles/tokens.css";
import "./styles/global.css";
import "./styles/foundation.css";
import "./styles/responsive.css";

applyStoredAppearance();

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
