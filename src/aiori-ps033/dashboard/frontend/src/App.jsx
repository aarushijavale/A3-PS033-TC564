
import { useEffect, useState } from "react";
import "./App.css";

const SERVICES = [
  {
    id: "latency",
    name: "Latency Analysis",
    description: "Measure network response time",
    endpoint: "LATENCY",
    icon: "◷",
    color: "cyan",
  },
  {
    id: "traceroute",
    name: "Traceroute",
    description: "Trace the network path and hops",
    endpoint: "TRACEROUTE",
    icon: "⌁",
    color: "blue",
  },
  {
    id: "pathmtu",
    name: "Path MTU Detection",
    description: "Identify maximum transmission unit",
    endpoint: "PATH MTU",
    icon: "◈",
    color: "purple",
  },
];

const LIVE_SERVICES = [
  {
    id: "dns",
    name: "DNS Resolution",
    description: "Resolve a real internet hostname",
    endpoint: "LIVE DNS",
    icon: "◎",
    color: "cyan",
  },
  {
    id: "latency",
    name: "TCP Latency",
    description: "Measure live TCP connection time",
    endpoint: "LIVE LATENCY",
    icon: "◷",
    color: "blue",
  },
  {
    id: "traceroute",
    name: "Live Traceroute",
    description: "Trace the real network route",
    endpoint: "LIVE TRACE",
    icon: "⌁",
    color: "purple",
  },
  {
    id: "pathmtu",
    name: "Live Path MTU",
    description: "Probe packet size without fragmentation",
    endpoint: "LIVE MTU",
    icon: "◈",
    color: "cyan",
  },
];

const NAV_ITEMS = [
  { id: "dashboard", label: "Dashboard", icon: "▦" },
  { id: "diagnostics", label: "Diagnostics", icon: "⌁" },
  { id: "dns-discovery", label: "DNS Discovery", icon: "◈" },
  { id: "activity-logs", label: "Activity Logs", icon: "▤" },
];

function App() {
  const [backend, setBackend] = useState("checking");
  const [mode, setMode] = useState("lab");

  const [results, setResults] = useState({});
  const [liveResults, setLiveResults] = useState({});

  const [running, setRunning] = useState(null);
  const [host, setHost] = useState("1.1.1.1");
  const [port, setPort] = useState("443");

  const [activeNav, setActiveNav] = useState("dashboard");

  const [logs, setLogs] = useState([
    "AIORI diagnostic dashboard initialized.",
    "Waiting for backend connection...",
  ]);

  useEffect(() => {
    checkBackend();

    const timer = setInterval(checkBackend, 10000);

    return () => clearInterval(timer);
  }, []);

  async function checkBackend() {
    try {
      const response = await fetch("/api/health", {
        cache: "no-store",
      });

      if (!response.ok) {
        throw new Error("Backend unavailable");
      }

      // A successful HTTP response means the API is reachable.
      setBackend("online");
    } catch (error) {
      setBackend("offline");
    }
  }

  // SIDEBAR NAVIGATION
  function navigateTo(section) {
    setActiveNav(section);

    if (section === "dashboard") {
      window.scrollTo({
        top: 0,
        behavior: "smooth",
      });
      return;
    }

    if (section === "dns-discovery") {
      setMode("lab");
    }

    const target = document.getElementById(section);

    if (target) {
      target.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }
  }

  // LAB NETWORK TESTS
  async function runDiagnostic(service) {
    setRunning(`lab-${service.id}`);

    setLogs((previous) => [
      ...previous,
      `Starting Lab Network ${service.name}...`,
    ]);

    try {
      const response = await fetch(
        `/api/diagnostics/${service.id}`,
        { method: "POST" }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : data.detail?.message || "Diagnostic failed"
        );
      }

      const report = {
        ...data,
        executedAt: new Date().toISOString(),
        mode: "Lab Network",
      };

      setResults((previous) => ({
        ...previous,
        [service.id]: report,
      }));

      setLogs((previous) => [
        ...previous,
        ...(data.logs || []),
        `Lab ${service.name}: completed successfully.`,
      ]);
    } catch (error) {
      const report = {
        status: "error",
        message: error.message,
        executedAt: new Date().toISOString(),
        mode: "Lab Network",
      };

      setResults((previous) => ({
        ...previous,
        [service.id]: report,
      }));

      setLogs((previous) => [
        ...previous,
        `LAB ERROR: ${error.message}`,
      ]);
    } finally {
      setRunning(null);
    }
  }

  // LIVE NETWORK TESTS
  async function runLiveDiagnostic(service) {
    if (!host.trim()) {
      alert("Please enter a hostname or IP address.");
      return;
    }

    const portNumber = Number(port);

    if (
      service.id !== "dns" &&
      (!Number.isInteger(portNumber) ||
        portNumber < 1 ||
        portNumber > 65535)
    ) {
      alert("Please enter a valid port between 1 and 65535.");
      return;
    }

    setRunning(`live-${service.id}`);

    setLogs((previous) => [
      ...previous,
      `Starting Live Network ${service.name} for ${host}...`,
    ]);

    try {
      const body = {
        host: host.trim(),
        port: portNumber,
      };

      const response = await fetch(
        `/api/live/${service.id}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(body),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : data.detail?.message ||
              JSON.stringify(data.detail) ||
              "Live diagnostic failed"
        );
      }

      const report = {
        ...data,
        executedAt: new Date().toISOString(),
        mode: "Live Network",
      };

      setLiveResults((previous) => ({
        ...previous,
        [service.id]: report,
      }));

      setLogs((previous) => [
        ...previous,
        `${service.name} completed for ${host}.`,
        ...(data.logs || []),
        ...(data.addresses || []).map(
          (address) => `Resolved address: ${address}`
        ),
        data.message || "",
      ].filter(Boolean));
    } catch (error) {
      const report = {
        status: "error",
        message: error.message,
        executedAt: new Date().toISOString(),
        mode: "Live Network",
      };

      setLiveResults((previous) => ({
        ...previous,
        [service.id]: report,
      }));

      setLogs((previous) => [
        ...previous,
        `LIVE ERROR: ${error.message}`,
      ]);
    } finally {
      setRunning(null);
    }
  }

  // CSV REPORT - BOTH MODES
  function downloadReport() {
    const headers = [
      "Mode",
      "Service",
      "Host",
      "Execution Date",
      "Status",
      "Result",
      "Error Message",
      "Execution Logs",
    ];

    const labRows = SERVICES
      .filter((service) => results[service.id])
      .map((service) => {
        const report = results[service.id];

        return [
          "Lab Network",
          service.name,
          "",
          report.executedAt || "",
          report.status || "",
          JSON.stringify(report.result ?? ""),
          report.message || "",
          (report.logs || []).join(" | "),
        ];
      });

    const liveRows = LIVE_SERVICES
      .filter((service) => liveResults[service.id])
      .map((service) => {
        const report = liveResults[service.id];

        return [
          "Live Network",
          service.name,
          report.host || host,
          report.executedAt || "",
          report.status || "",
          JSON.stringify(report),
          report.message || "",
          (report.logs || []).join(" | "),
        ];
      });

    const rows = [...labRows, ...liveRows];

    if (rows.length === 0) {
      alert("Run at least one diagnostic before downloading.");
      return;
    }

    const escapeCSV = (value) =>
      `"${String(value ?? "").replace(/"/g, '""')}"`;

    const csv = [headers, ...rows]
      .map((row) => row.map(escapeCSV).join(","))
      .join("\r\n");

    const blob = new Blob(
      ["\uFEFF" + csv],
      { type: "text/csv;charset=utf-8;" }
    );

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = `AIORI-PS033-Report-${new Date()
      .toISOString()
      .slice(0, 10)}.csv`;

    document.body.appendChild(link);
    link.click();
    link.remove();

    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  const completed = [
    ...Object.values(results),
    ...Object.values(liveResults),
  ].filter((item) => item.status === "success").length;

  const activeServices =
    mode === "lab" ? SERVICES : LIVE_SERVICES;

  const activeResults =
    mode === "lab" ? results : liveResults;

  return (
    <div className="app-shell" id="dashboard">

      <aside className="sidebar">

        <div className="brand">
          <div className="brand-icon">A</div>
          <div>
            <h2>AIORI<span>.</span></h2>
            <small>NETWORK INTELLIGENCE</small>
          </div>
        </div>

        <div className="nav-label">WORKSPACE</div>

        <nav className="sidebar-nav" aria-label="Main navigation">
          {NAV_ITEMS.map((item) => (
            <button
              type="button"
              key={item.id}
              className={`nav-item ${
                activeNav === item.id ? "active" : ""
              }`}
              onClick={() => navigateTo(item.id)}
              aria-current={
                activeNav === item.id ? "page" : undefined
              }
            >
              <span className="nav-icon">{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">

          <div className="system-card">
            <div className="system-heading">
              <span className="status-dot" />
              SYSTEM STATUS
            </div>

            <h3>
              {backend === "online"
                ? "Operational"
                : backend === "checking"
                ? "Checking..."
                : "Disconnected"}
            </h3>

            <p>Diagnostic API connection</p>
          </div>

          <div className="sidebar-footer">
            AIORI PS-033 · 2026
          </div>

        </div>
      </aside>

      <main className="main-content">

        <header className="topbar">

          <div>
            <div className="breadcrumb">
              WORKSPACE / OVERVIEW
            </div>
            <h1>Network Dashboard</h1>
          </div>

          <div className="topbar-right">

            <div className="live-indicator">
              <span className="status-dot" />
              {backend === "online"
                ? "SYSTEM ONLINE"
                : "API OFFLINE"}
            </div>

            <div className="avatar">A</div>

          </div>
        </header>

        <section className="welcome">

          <div>
            <div className="eyebrow">
              AI-POWERED NETWORK DIAGNOSTICS
            </div>

            <h2>
              Discover. Diagnose. <span>Optimize.</span>
            </h2>

            <p>
              DNS-based discovery and secure invocation of
              network diagnostic services, with real-world
              network testing.
            </p>
          </div>

          <div className="welcome-symbol" aria-hidden="true">⌁</div>

        </section>

        <section className="stats-grid">

          <div className="stat-card">
            <div className="stat-label">
              AVAILABLE SERVICES
            </div>
            <div className="stat-value">
              {mode === "lab" ? "03" : "04"}
            </div>
            <div className="stat-note">
              {mode === "lab"
                ? "Lab diagnostic services"
                : "Live diagnostic services"}
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-label">
              SUCCESSFUL RUNS
            </div>
            <div className="stat-value">
              {completed.toString().padStart(2, "0")}
            </div>
            <div className="stat-note">
              This dashboard session
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-label">
              DNSSEC VALIDATION
            </div>
            <div className="stat-value">
              <span className="small-status">
                {backend === "online" ? "READY" : "WAIT"}
              </span>
            </div>
            <div className="stat-note">
              Lab resolver connection status
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-label">BACKEND</div>
            <div className={`stat-value backend-value ${backend}`}>
              {backend.toUpperCase()}
            </div>
            <div className="stat-note">
              FastAPI connection
            </div>
          </div>

        </section>

        <section className="section-heading" id="diagnostics">

          <div>
            <div className="eyebrow">
              DIAGNOSTIC ENVIRONMENT
            </div>
            <h2>Choose Network Mode</h2>
          </div>

          <span className="module-count">
            {mode === "lab" ? "LAB MODE" : "LIVE MODE"}
          </span>

        </section>

        <div className="mode-switch">
          <button
            type="button"
            className={mode === "lab" ? "mode-button active" : "mode-button"}
            onClick={() => setMode("lab")}
            disabled={running !== null}
          >
            ◈ &nbsp; LAB NETWORK
          </button>

          <button
            type="button"
            className={mode === "live" ? "mode-button active live-active" : "mode-button"}
            onClick={() => setMode("live")}
            disabled={running !== null}
          >
            ◎ &nbsp; LIVE NETWORK
          </button>
        </div>

        {mode === "lab" ? (
          <div className="mode-description">
            <strong>Lab Network:</strong> Runs diagnostics through
            your configured DNSSEC + SVCB service discovery environment.
          </div>
        ) : (
          <>
            <div className="mode-description live-description">
              <strong>Live Network:</strong> Runs tests against a real
              hostname or IP address using your dashboard container's
              outbound network connection.
            </div>

            <section className="live-target-panel">
              <div>
                <label htmlFor="target-host">TARGET HOST / IP ADDRESS</label>
                <input
                  id="target-host"
                  type="text"
                  value={host}
                  onChange={(event) => setHost(event.target.value)}
                  placeholder="Example: 1.1.1.1 or example.com"
                  disabled={running !== null}
                />
              </div>

              <div>
                <label htmlFor="target-port">TCP PORT</label>
                <input
                  id="target-port"
                  type="number"
                  min="1"
                  max="65535"
                  value={port}
                  onChange={(event) => setPort(event.target.value)}
                  disabled={running !== null}
                />
              </div>
            </section>
          </>
        )}

        <section className="section-heading" id="dns-discovery">

          <div>
            <div className="eyebrow">
              DIAGNOSTIC MODULES
            </div>
            <h2>
              {mode === "lab"
                ? "Lab Network Services"
                : "Live Network Services"}
            </h2>
          </div>

          <span className="module-count">
            {activeServices.length.toString().padStart(2, "0")} MODULES
          </span>

        </section>

        <section className="services-grid">

          {activeServices.map((service) => {
            const result = activeResults[service.id];
            const runId = `${mode}-${service.id}`;

            return (
              <article
                className="service-card"
                key={runId}
              >

                <div className="service-top">

                  <div className={`service-icon ${service.color}`}>
                    {service.icon}
                  </div>

                  <span className="service-tag">
                    {service.endpoint}
                  </span>

                </div>

                <h3>{service.name}</h3>
                <p>{service.description}</p>

                <div className="service-result">

                  {result?.status === "success" ? (
                    <span className="result-success">
                      ● Completed
                    </span>
                  ) : result?.status === "partial" ? (
                    <span className="result-idle">
                      ● Partially completed
                    </span>
                  ) : result?.status === "error" ? (
                    <span className="result-error">
                      ● Failed
                    </span>
                  ) : (
                    <span className="result-idle">
                      ● Awaiting execution
                    </span>
                  )}

                </div>

                {result && (
                  <pre className="result-data">
                    {JSON.stringify(
                      mode === "lab"
                        ? result.result ?? result
                        : result,
                      null,
                      2
                    )}
                  </pre>
                )}

                <button
                  type="button"
                  className="run-button"
                  onClick={() =>
                    mode === "lab"
                      ? runDiagnostic(service)
                      : runLiveDiagnostic(service)
                  }
                  disabled={
                    running !== null || backend !== "online"
                  }
                >
                  {running === runId
                    ? "RUNNING..."
                    : mode === "lab"
                    ? "RUN DIAGNOSTIC  →"
                    : "RUN LIVE TEST  →"}
                </button>

              </article>
            );
          })}

        </section>

        <section className="logs-section" id="activity-logs">

          <div className="logs-header">

            <div>
              <div className="eyebrow">
                LIVE MONITORING
              </div>
              <h2>Execution Console</h2>
            </div>

            <div className="logs-actions">

              <button
                type="button"
                className="download-button"
                onClick={downloadReport}
                disabled={
                  Object.keys(results).length === 0 &&
                  Object.keys(liveResults).length === 0
                }
              >
                ↓ DOWNLOAD CSV
              </button>

              <button
                type="button"
                className="clear-button"
                onClick={() => setLogs([])}
              >
                CLEAR LOGS
              </button>

            </div>

          </div>

          <div className="terminal">

            <div className="terminal-top">

              <div className="terminal-dots">
                <i />
                <i />
                <i />
              </div>

              <span>AIORI://diagnostic-console</span>

              <span className="terminal-live">
                ● LIVE
              </span>

            </div>

            <div className="terminal-body">

              {logs.map((log, index) => (
                <div className="log-line" key={index}>

                  <span className="log-number">
                    {String(index + 1).padStart(2, "0")}
                  </span>

                  <span className="log-prompt">›</span>

                  <span>{log}</span>

                </div>
              ))}

              <div className="terminal-cursor">_</div>

            </div>
          </div>

        </section>

        <footer className="page-footer">
          <span>
            AIORI PS-033 · DNS-BASED DIAGNOSTIC DISCOVERY
          </span>
          <span>
            SECURE NETWORK INTELLIGENCE
          </span>
        </footer>

      </main>
    </div>
  );
}

export default App;
