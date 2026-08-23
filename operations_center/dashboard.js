(() => {
"use strict";
const $ = id => document.getElementById(id);
const esc = v => String(v ?? "").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;");

function number(v) { if (v === null || v === undefined || v === "") return "—"; const n=Number(v); return Number.isFinite(n)?n.toLocaleString():String(v); }
function percent(v) { if (v === null || v === undefined || v === "") return "—"; const n=Number(v); return Number.isFinite(n)?`${n.toFixed(1)}%`:String(v); }
function money(v) { if (v === null || v === undefined || v === "") return "—"; const n=Number(v); return Number.isFinite(n)?new Intl.NumberFormat("en-US",{style:"currency",currency:"USD"}).format(n):String(v); }
function latency(v) { if (v === null || v === undefined || v === "") return "—"; const n=Number(v); return Number.isFinite(n)?`${n.toFixed(2)}s`:String(v); }

function health(p) {
  const s=String(p.health || p.status || p.monitoring_status || (p.active ? "healthy":"unavailable")).toLowerCase();
  if (s.includes("critical")||s.includes("unavailable")||s.includes("failed")||s.includes("down")) return ["critical","Unavailable"];
  if (s.includes("degraded")||s.includes("warning")||s.includes("unhealthy")) return ["warning","Degraded"];
  if (s.includes("healthy")||s.includes("operational")||s.includes("active")||s==="ok") return ["healthy","Healthy"];
  return ["unknown","Unknown"];
}

function renderProviders(list) {
  list = Array.isArray(list) ? list : [];
  $("providerCount").textContent =
    `${list.length} provider${list.length === 1 ? "" : "s"}`;

  if (!list.length) {
    $("providers").innerHTML =
      '<tr><td colspan="7" class="empty">No provider observations are currently available.</td></tr>';
    $("providerSummary").textContent =
      "No provider observations available";
    return;
  }

  $("providers").innerHTML = list.map(p => {
    const [state, label] = health(p);
    const model = p.model ||
      (Array.isArray(p.models) ? p.models.join(", ") : "—");
    const latencyValue =
      p.latency_ms ?? p.average_latency_ms ?? p.avg_latency_ms;
    const errorRate =
      p.error_rate ?? p.error_rate_percent;
    const lastCheck =
      p.last_checked_at ?? p.checked_at ?? p.observed_at;

    let checked = "—";
    if (lastCheck) {
      const d = new Date(lastCheck);
      if (!Number.isNaN(d.getTime())) {
        checked = d.toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit"
        });
      }
    }

    const latencyText =
      latencyValue == null ? "—" : `${Number(latencyValue).toFixed(0)} ms`;

    const errorText =
      errorRate == null ? "—" : `${Number(errorRate).toFixed(2)}%`;

    return `<tr>
      <td><b>${esc(p.provider || "Unknown")}</b></td>
      <td class="model">${esc(model)}</td>
      <td><span class="health ${state}"><i></i>${label}</span></td>
      <td><span class="active ${p.active === false ? "off" : ""}">
        ${p.active === false ? "Inactive" : "Active"}
      </span></td>
      <td>${esc(latencyText)}</td>
      <td>${esc(errorText)}</td>
      <td>${esc(checked)}</td>
    </tr>`;
  }).join("");

  const bad = list.filter(p => health(p)[0] === "critical").length;
  const degraded = list.filter(p => health(p)[0] === "warning").length;

  $("providerSummary").textContent = bad
    ? `${bad} provider${bad === 1 ? "" : "s"} unavailable`
    : degraded
      ? `${degraded} provider${degraded === 1 ? "" : "s"} degraded`
      : `${list.length} provider${list.length === 1 ? "" : "s"} operational`;
}
function renderMonitoring(status) {
  const s=String(status||"unknown").toLowerCase();
  const critical=s.includes("critical")||s.includes("unhealthy")||s.includes("down");
  const degraded=s.includes("degraded")||s.includes("warning");
  $("monitorIcon").className="monitor-icon "+(critical?"critical":degraded?"warning":"healthy");
  $("monitorIcon").textContent=critical?"!":degraded?"!":"✓";
  $("monitorTitle").textContent=critical?"Monitoring requires attention":degraded?"Monitoring is degraded":"Monitoring is healthy";
  $("monitorText").textContent=critical?"A critical monitoring condition has been detected.":degraded?"One or more monitored components require attention.":"The Operations Center is receiving a healthy monitoring state.";
  $("monitoring").textContent=status||"—";
  $("overall").className="overall "+(critical?"critical":degraded?"warning":"healthy");
  $("overall").textContent=critical?"● Attention required":degraded?"● Degraded":"● Healthy";
}

function renderEvents(list) {
  list=Array.isArray(list)?list:[];
  $("eventCount").textContent=`${list.length} event${list.length===1?"":"s"}`;
  if (!list.length) {$("events").innerHTML='<div class="empty">No operational events have been recorded yet.</div>';return;}
  $("events").innerHTML=list.slice(0,20).map(e=>{
    const s=String(e.severity||"").toLowerCase();
    const cls=s.includes("critical")||s.includes("error")?"critical":s.includes("warning")||s.includes("high")?"warning":"success";
    let time="—"; if(e.occurred_at){const d=new Date(e.occurred_at); if(!Number.isNaN(d.getTime())) time=d.toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"});}
    return `<div class="event"><i class="${cls}"></i><div><b>${esc(e.message||e.event_type||"Operational event")}</b><small>${esc(e.component||e.source||e.event_type||"Operational event")}</small></div><time>${esc(time)}</time></div>`;
  }).join("");
}

function renderDashboard(d) {
  $("confidence").textContent=percent(d.system_confidence);
  $("executions").textContent=number(d.total_executions ?? d.executions);
  $("success").textContent=percent(d.success_rate);
  $("latency").textContent=latency(d.avg_latency ?? d.average_latency);
  $("cost").textContent=money(d.total_cost ?? d.estimated_cost);
  $("quality").textContent=d.quality_score==null?"—":`${Number(d.quality_score).toFixed(1)} / 5`;
  renderProviders(d.active_providers);
  $("active").textContent=number(d.active_escalations);
  $("pending").textContent=number(d.pending_approvals);
  $("approved").textContent=number(d.approved_escalations);
  $("rejected").textContent=number(d.rejected_escalations);
  $("total").textContent=number(d.total_escalations);
  renderMonitoring(d.monitoring_status);
}

async function refresh() {
  $("connection").className="connection pending";
  $("connection").textContent="● Refreshing";
  try {
    const [dashboard,events]=await Promise.all([
      window.EasyChatBotOperationsAPI.getDashboard(),
      window.EasyChatBotOperationsAPI.getOperationalEvents()
    ]);
    renderDashboard(dashboard);
    renderEvents(events);
    $("updated").textContent=new Date().toLocaleTimeString();
    $("connection").className="connection live";
    $("connection").textContent="● Live";
    $("error").classList.add("hidden");
  } catch(e) {
    console.error(e);
    $("connection").className="connection error";
    $("connection").textContent="● Disconnected";
    $("error").classList.remove("hidden");
    $("error").textContent=`Operations Center unavailable: ${e.message}`;
  }
}
$("refresh").addEventListener("click",refresh);
refresh();
setInterval(refresh,30000);
})();
