import { StrictMode } from "react";

import { createRoot } from "react-dom/client";

import { AppProviders } from "~/app/providers/AppProviders";
import { AppRouter } from "~/app/router/AppRouter";

import { Modal } from "~/shared/ui/modal/Modal";

import "./index.css";

const root = document.getElementById("root");

if (!root) {
  throw new Error("Root element not found");
}

if (window.location.pathname === "/") {
  window.location.replace("/admin");
}

createRoot(root).render(
  <StrictMode>
    <AppProviders>
      <AppRouter />
      <Modal />
    </AppProviders>
  </StrictMode>,
);
