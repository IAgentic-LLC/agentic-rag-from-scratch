import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "bootstrap/dist/css/bootstrap.min.css";
import "./styles.css";

// ?scale=2 draws the same 1200 x 675 stage at 2x in a larger viewport (crisp frames for the film); without it the app fills the window.
const scale = Number(new URLSearchParams(location.search).get("scale"));
if (scale > 1) { document.documentElement.classList.add("scaled"); document.documentElement.style.setProperty("--scale", String(scale)); }

ReactDOM.createRoot(document.getElementById("root")!).render(<React.StrictMode><App /></React.StrictMode>);
