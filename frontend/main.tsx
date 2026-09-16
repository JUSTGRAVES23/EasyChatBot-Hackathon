import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import AppRouter from "./src/router";
import { AuthProvider } from "./src/auth/AuthProvider";

import "./styles/operations-center.css";

const rootElement = document.getElementById("root");

if (!rootElement) {
  throw new Error(
    'EasyChatBot frontend could not start: missing <div id="root"></div>.',
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