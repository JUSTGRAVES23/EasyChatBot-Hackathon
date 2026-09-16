import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import AppRouter from "./router";
import { AuthProvider } from "./auth/AuthProvider";

const rootElement = document.getElementById("root");

if (!rootElement) {
  throw new Error(
    "EasyChatBot React root element was not found.",
  );
}

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <AppRouter />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>,
);