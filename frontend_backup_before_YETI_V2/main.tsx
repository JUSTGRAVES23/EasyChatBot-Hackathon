import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import OperationsCenterDashboard from "./pages/operations-center/OperationsCenterDashboard";

import "./styles/operations-center-dashboard.css";


function App() {

    const path = window.location.pathname;


    if (path.startsWith("/operations-center")) {

        return (
            <OperationsCenterDashboard />
        );

    }


    return (
        <div
            style={{
                padding: "40px",
                fontFamily: "Nunito"
            }}
        >
            EasyChatBot Academy
        </div>
    );

}


const root = document.getElementById("root");


if (!root) {

    throw new Error(
        "Missing root element"
    );

}


createRoot(root).render(
    <StrictMode>
        <App />
    </StrictMode>
);