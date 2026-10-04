import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { MotionConfig } from "framer-motion";

import { App } from "./App";
import "./styles/heroui.css";
import "./styles/tokens.css";
import "./ui/animations/presets.css";

const container = document.getElementById("root");
if (!container) {
  throw new Error("Root container #root is missing from index.html");
}

// PWA: register the service worker in production only, so Vite's dev server
// (HMR) is never shadowed by a cached shell.
if (import.meta.env.PROD && "serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    void navigator.serviceWorker.register("/sw.js").catch(() => undefined);
  });
}

createRoot(container).render(
  <StrictMode>
    <MotionConfig reducedMotion="user">
      <App />
    </MotionConfig>
  </StrictMode>,
);
