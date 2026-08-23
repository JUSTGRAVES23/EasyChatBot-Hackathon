import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import OperationsCenterDashboard from "./pages/operations-center/OperationsCenterDashboard";

import "./styles/operations-center-dashboard.css";


function App() {

    const path = window.location.pathname;


    if (path.startsWith("/operations-center")) {

        return <OperationsCenterDashboard />;

    }


    return (
        <div>
            EasyChatBot
        </div>
    );
}


const rootElement = document.getElementById("root");


if (!rootElement) {

    throw new Error(
        "Root element not found"
    );

}


createRoot(rootElement).render(
    <StrictMode>
        <App />
    </StrictMode>
);