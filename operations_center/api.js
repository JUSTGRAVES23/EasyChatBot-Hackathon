(() => {
"use strict";
const base = (window.EASYCHATBOT_OPERATIONS_API_BASE || "http://127.0.0.1:8000").replace(/\/$/, "");
async function request(path) {
  const response = await fetch(base + path, {headers: {Accept: "application/json"}, cache: "no-store"});
  if (!response.ok) throw new Error(`API ${response.status}: ${path}`);
  return response.json();
}
window.EasyChatBotOperationsAPI = Object.freeze({
  getDashboard: () => request("/api/operations-center/dashboard"),
  getOperationalEvents: () => request("/api/operations-center/operational-events")
});
})();
