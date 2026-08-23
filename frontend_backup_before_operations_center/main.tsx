import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import GovernanceOperationsCenter from "./pages/operations-center/GovernanceOperationsCenter";


function renderGovernanceCenter() {

  const rootElement =
    document.getElementById("root");


  if (!rootElement) {

    throw new Error(
      "Root element not found."
    );

  }


  createRoot(rootElement).render(

    <StrictMode>

      <GovernanceOperationsCenter />

    </StrictMode>

  );

}


function startApplication() {

  const path =
    window.location.pathname.replace(/\/+$/, "") || "/";


  if (
    path === "/operations-center/governance"
  ) {

    renderGovernanceCenter();

    return;

  }


  /*
   * Existing learner dashboard remains
   * controlled by legacy index.html/app.js.
   */

}


startApplication();