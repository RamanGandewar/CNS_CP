import { useEffect, useState } from "react";
import GraphView from "../components/GraphView";
import {
  createDashboardSocket,
  getClusters,
  getDashboardSummary,
  getGraph,
  getHealth,
  getTransactions,
  predict,
  seedDemoTransactions,
} from "../services/api";
import "../styles/dashboard.css";

function formatNumber(value, suffix = "") {
  if (typeof value !== "number") {
    return value ?? "-";
  }

  if (suffix === "%") {
    return `${value.toFixed(1)}%`;
  }

  return value.toLocaleString();
}

function RiskBarChart({ data }) {
  const max = Math.max(
    1,
    ...data.map((item) => item.high + item.med + item.low),
  );

  return (
    <div className="bar-chart">
      {data.map((item) => (
        <div key={item.label} className="bar-col">
          <div className="bars-stack">
            <div className="bar bar-high" style={{ height: `${(item.high / max) * 100}%` }} />
            <div className="bar bar-med" style={{ height: `${(item.med / max) * 100}%` }} />
            <div className="bar bar-low" style={{ height: `${(item.low / max) * 100}%` }} />
          </div>
          <span className="bar-label">{item.label}</span>
        </div>
      ))}
    </div>
  );
}

function DonutChart({ breakdown }) {
  const high = breakdown?.high ?? 0;
  const med = breakdown?.med ?? 0;
  const low = breakdown?.low ?? 0;
  const total = high + med + low || 1;
  const r = 46;
  const circ = 2 * Math.PI * r;
  const h = (high / total) * circ;
  const m = (med / total) * circ;
  const l = (low / total) * circ;

  return (
    <div className="donut-wrap">
      <svg viewBox="0 0 120 120" className="donut-svg">
        <circle cx="60" cy="60" r={r} fill="none" stroke="var(--c-track)" strokeWidth="14" />
        <circle
          cx="60"
          cy="60"
          r={r}
          fill="none"
          stroke="var(--c-high)"
          strokeWidth="14"
          strokeDasharray={`${h} ${circ}`}
          strokeDashoffset={0}
          strokeLinecap="round"
          transform="rotate(-90 60 60)"
        />
        <circle
          cx="60"
          cy="60"
          r={r}
          fill="none"
          stroke="var(--c-med)"
          strokeWidth="14"
          strokeDasharray={`${m} ${circ}`}
          strokeDashoffset={-h}
          strokeLinecap="round"
          transform="rotate(-90 60 60)"
        />
        <circle
          cx="60"
          cy="60"
          r={r}
          fill="none"
          stroke="var(--c-low)"
          strokeWidth="14"
          strokeDasharray={`${l} ${circ}`}
          strokeDashoffset={-(h + m)}
          strokeLinecap="round"
          transform="rotate(-90 60 60)"
        />
        <text x="60" y="55" textAnchor="middle" className="donut-num">
          {high + med + low}
        </text>
        <text x="60" y="70" textAnchor="middle" className="donut-sub">
          saved scans
        </text>
      </svg>
      <div className="donut-legend">
        <span className="leg-item"><span className="leg-dot" style={{ background: "var(--c-high)" }} />High ({high})</span>
        <span className="leg-item"><span className="leg-dot" style={{ background: "var(--c-med)" }} />Med ({med})</span>
        <span className="leg-item"><span className="leg-dot" style={{ background: "var(--c-low)" }} />Low ({low})</span>
      </div>
    </div>
  );
}

function RiskGauge({ score }) {
  const color = score >= 70 ? "var(--c-high)" : score >= 40 ? "var(--c-med)" : "var(--c-low)";
  const label = score >= 70 ? "High Risk" : score >= 40 ? "Medium Risk" : "Low Risk";
  const r = 50;
  const circ = Math.PI * r;
  const fill = (score / 100) * circ;

  return (
    <div className="gauge-wrap">
      <svg viewBox="0 0 120 75" className="gauge-svg">
        <path d="M 10 70 A 50 50 0 0 1 110 70" fill="none" stroke="var(--c-track)" strokeWidth="10" strokeLinecap="round" />
        <path
          d="M 10 70 A 50 50 0 0 1 110 70"
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={`${fill} ${circ}`}
        />
        <text x="60" y="62" textAnchor="middle" className="gauge-num" style={{ fill: color }}>
          {score}
        </text>
      </svg>
      <p className="gauge-label" style={{ color }}>{label}</p>
    </div>
  );
}

function PredictForm({ onResult }) {
  const [form, setForm] = useState({ TransactionAmt: "", card1: "", device: "desktop", addr1: "" });
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);

    try {
      const result = await predict({
        TransactionAmt: Number(form.TransactionAmt) || 0,
        card1: Number(form.card1) || 0,
        device: form.device,
        addr1: Number(form.addr1) || 0,
      });
      setForm({ TransactionAmt: "", card1: "", device: "desktop", addr1: "" });
      onResult(result);
    } catch (error) {
      onResult({ error: error.message });
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="predict-form" onSubmit={handleSubmit}>
      <div className="form-row">
        <div className="form-group">
          <label>Transaction Amount ($)</label>
          <input
            type="number"
            placeholder="e.g. 500"
            value={form.TransactionAmt}
            onChange={(event) => setForm((current) => ({ ...current, TransactionAmt: event.target.value }))}
          />
        </div>
        <div className="form-group">
          <label>Card ID</label>
          <input
            type="number"
            placeholder="e.g. 1234"
            value={form.card1}
            onChange={(event) => setForm((current) => ({ ...current, card1: event.target.value }))}
          />
        </div>
      </div>
      <div className="form-row">
        <div className="form-group">
          <label>Device Type</label>
          <select
            value={form.device}
            onChange={(event) => setForm((current) => ({ ...current, device: event.target.value }))}
          >
            <option value="desktop">Desktop</option>
            <option value="mobile">Mobile</option>
            <option value="tablet">Tablet</option>
            <option value="unknown">Unknown</option>
          </select>
        </div>
        <div className="form-group">
          <label>Address (ZIP)</label>
          <input
            type="number"
            placeholder="e.g. 330"
            value={form.addr1}
            onChange={(event) => setForm((current) => ({ ...current, addr1: event.target.value }))}
          />
        </div>
      </div>
      <button type="submit" className="btn-predict" disabled={loading}>
        {loading && <span className="spinner" />}
        {loading ? "Analyzing..." : "Analyze Transaction ->".replace(">", "\u203a")}
      </button>
    </form>
  );
}

function EmptyState({ title, subtitle }) {
  return (
    <div className="empty-state">
      <p className="empty-title">{title}</p>
      <p className="empty-sub">{subtitle}</p>
    </div>
  );
}

export default function Dashboard({ user, onLogout, onSessionExpired }) {
  const [page, setPage] = useState("overview");
  const [collapsed, setCollapsed] = useState(false);
  const [apiStatus, setApiStatus] = useState("checking");
  const [summary, setSummary] = useState(null);
  const [graphData, setGraphData] = useState({ nodes: [], links: [], stats: [] });
  const [clusters, setClusters] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [predictResult, setPredictResult] = useState(null);
  const [riskFilter, setRiskFilter] = useState("all");
  const [deviceFilter, setDeviceFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [loadingState, setLoadingState] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState("");
  const [seedLoading, setSeedLoading] = useState(false);
  const [seedMessage, setSeedMessage] = useState("");

  const navItems = [
    { key: "overview", label: "Overview", icon: "◦" },
    { key: "predict", label: "Predict", icon: "⌁" },
    { key: "graph", label: "Graph View", icon: "◎" },
    { key: "transactions", label: "Transactions", icon: "≡" },
    { key: "analytics", label: "Analytics", icon: "∿" },
  ];

  async function loadCoreData({ silent = false } = {}) {
    if (!silent) {
      setLoadingState(true);
    } else {
      setIsRefreshing(true);
    }
    try {
      const [summaryData, graph, clusterData] = await Promise.all([
        getDashboardSummary(),
        getGraph(),
        getClusters(),
      ]);
      setSummary(summaryData);
      setGraphData(graph);
      setClusters(clusterData.clusters || []);
      setLastUpdated(summaryData.last_updated || "");
      setApiStatus("online");
    } catch (error) {
      if (error.message.toLowerCase().includes("session")) {
        onSessionExpired();
        return;
      }
      setApiStatus("offline");
    } finally {
      if (!silent) {
        setLoadingState(false);
      } else {
        setIsRefreshing(false);
      }
    }
  }

  async function loadTransactions() {
    try {
      const data = await getTransactions({ risk: riskFilter, device: deviceFilter, limit: 100 });
      setTransactions(data.transactions || []);
    } catch (error) {
      if (error.message.toLowerCase().includes("session")) {
        onSessionExpired();
      }
    }
  }

  useEffect(() => {
    getHealth().then(() => setApiStatus("online")).catch(() => setApiStatus("offline"));
    loadCoreData();
  }, []);

  useEffect(() => {
    loadTransactions();
  }, [riskFilter, deviceFilter]);

  useEffect(() => {
    let reconnectTimerId = null;
    let socket = null;

    function connectSocket() {
      socket = createDashboardSocket({
        onOpen: () => {
          setApiStatus("online");
        },
        onMessage: async (message) => {
          if (message.type === "dashboard_update") {
            setLastUpdated(message.last_updated || "");
            await loadCoreData({ silent: true });
            await loadTransactions();
          }
        },
        onClose: () => {
          setApiStatus("offline");
          reconnectTimerId = window.setTimeout(connectSocket, 3000);
        },
      });
    }

    connectSocket();

    return () => {
      if (reconnectTimerId) {
        window.clearTimeout(reconnectTimerId);
      }
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.close();
      }
    };
  }, [riskFilter, deviceFilter]);

  async function handlePredictResult(result) {
    setPredictResult(result);
    if (!result.error) {
      await loadCoreData();
      await loadTransactions();
    }
  }

  async function handleSeedDemo() {
    setSeedLoading(true);
    setSeedMessage("");

    try {
      const response = await seedDemoTransactions(8);
      setSeedMessage(response.message);
      await loadCoreData();
      await loadTransactions();
    } catch (error) {
      if (error.message.toLowerCase().includes("session")) {
        onSessionExpired();
        return;
      }
      setSeedMessage(error.message);
    } finally {
      setSeedLoading(false);
    }
  }

  function formatLastUpdated(value) {
    if (!value) {
      return "No live updates yet";
    }

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return "Live data active";
    }

    return `Last update ${date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}`;
  }

  const filteredTransactions = transactions.filter((item) => {
    if (!search.trim()) {
      return true;
    }
    const query = search.toLowerCase();
    return (
      item.id.toLowerCase().includes(query) ||
      item.device.toLowerCase().includes(query) ||
      String(item.card1 ?? "").includes(query)
    );
  });

  return (
    <div className={`dash-root${collapsed ? " sidebar-collapsed" : ""}`}>
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="brand">
            <span className="brand-icon">⬡</span>
            {!collapsed && <span className="brand-name">FraudGuard</span>}
          </div>
          <button className="collapse-btn" onClick={() => setCollapsed((current) => !current)}>
            {collapsed ? "›" : "‹"}
          </button>
        </div>

        {!collapsed && <p className="sidebar-section-label">Menu</p>}
        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <button
              key={item.key}
              className={`nav-item${page === item.key ? " nav-active" : ""}`}
              onClick={() => setPage(item.key)}
            >
              <span className="nav-icon">{item.icon}</span>
              {!collapsed && <span className="nav-label">{item.label}</span>}
            </button>
          ))}
        </nav>

        {!collapsed && (
          <div className="sidebar-user-card">
            <p className="sidebar-user-name">{user.name}</p>
            <p className="sidebar-user-email">{user.email}</p>
            <button className="btn-outline-sm sidebar-logout" onClick={onLogout}>Log out</button>
          </div>
        )}

        <div className="api-status-pill">
          <span className={`status-dot ${apiStatus}`} />
          {!collapsed && <span>API {apiStatus === "online" ? "Online" : apiStatus === "offline" ? "Offline" : "..."}</span>}
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <h1 className="page-title">{navItems.find((item) => item.key === page)?.label}</h1>
            <p className="page-sub">Dynamic fraud monitoring backed by your trained models and SQLite</p>
            <p className="page-live-status">
              <span className={`live-dot${isRefreshing ? " live-dot-pulse" : ""}`} />
              {formatLastUpdated(lastUpdated)}
            </p>
          </div>
          <div className="topbar-right">
            <div className="search-box">
              <span className="search-icon">⌕</span>
              <input
                type="text"
                placeholder="Search transactions..."
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
            </div>
            <button className="btn-outline-sm" onClick={handleSeedDemo} disabled={seedLoading}>
              {seedLoading ? "Seeding..." : "Seed Demo Data"}
            </button>
            <button className="btn-primary" onClick={() => setPage("predict")}>+ New Scan</button>
            <div className="avatar">{user.name.slice(0, 2).toUpperCase()}</div>
          </div>
        </header>

        <div className="content-body">
          {seedMessage && (
            <div className="seed-banner">
              {seedMessage}
            </div>
          )}
          {loadingState && !summary ? (
            <EmptyState title="Loading dashboard data" subtitle="Pulling saved scans, graph activity, and analytics from SQLite." />
          ) : (
            <>
              {page === "overview" && (
                <>
                  <div className="stat-grid">
                    {(summary?.stats || []).map((item) => (
                      <div key={item.label} className="stat-card">
                        <span className="stat-label">{item.label}</span>
                        <div className="stat-value">
                          {item.label === "Detection Rate"
                            ? formatNumber(Number(item.value), "%")
                            : formatNumber(Number(item.value))}
                        </div>
                        <div className={`stat-delta ${item.up === true ? "up" : item.up === false ? "down" : "neutral"}`}>
                          {item.delta}
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="charts-row">
                    <div className="card chart-card">
                      <div className="card-header">
                        <span className="card-title">Risk Distribution - Last 7 Days</span>
                        <span className="card-badge">Live from SQLite</span>
                      </div>
                      <RiskBarChart data={summary?.risk_over_time || []} />
                      <div className="chart-legend">
                        <span className="leg-item"><span className="leg-dot" style={{ background: "var(--c-high)" }} />High</span>
                        <span className="leg-item"><span className="leg-dot" style={{ background: "var(--c-med)" }} />Medium</span>
                        <span className="leg-item"><span className="leg-dot" style={{ background: "var(--c-low)" }} />Low</span>
                      </div>
                    </div>
                    <div className="card donut-card">
                      <div className="card-header"><span className="card-title">Saved Breakdown</span></div>
                      <DonutChart breakdown={summary?.breakdown} />
                    </div>
                  </div>

                  <div className="bottom-row">
                    <div className="card txn-card">
                      <div className="card-header">
                        <span className="card-title">Recent Transactions</span>
                        <button className="btn-link" onClick={() => setPage("transactions")}>View all {"\u203a"}</button>
                      </div>
                      {summary?.recent_transactions?.length ? (
                        <table className="txn-table">
                          <thead>
                            <tr><th>ID</th><th>Amount</th><th>Device</th><th>Score</th><th>Status</th></tr>
                          </thead>
                          <tbody>
                            {summary.recent_transactions.map((item) => (
                              <tr key={item.id}>
                                <td className="txn-id">{item.id}</td>
                                <td>${Number(item.amount).toLocaleString()}</td>
                                <td><span className="device-pill">{item.device}</span></td>
                                <td>
                                  <div className="score-bar-wrap">
                                    <div
                                      className="score-bar"
                                      style={{
                                        width: `${Math.round(item.risk_score)}%`,
                                        background: item.risk_score >= 70 ? "var(--c-high)" : item.risk_score >= 40 ? "var(--c-med)" : "var(--c-low)",
                                      }}
                                    />
                                    <span className="score-num">{Math.round(item.risk_score)}</span>
                                  </div>
                                </td>
                                <td><span className={`status-badge status-${item.status}`}>{item.status}</span></td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      ) : (
                        <EmptyState title="No saved transactions yet" subtitle="Run a prediction from the Predict page and it will appear here." />
                      )}
                    </div>

                    <div className="card alerts-card">
                      <div className="card-header">
                        <span className="card-title">Active Alerts</span>
                        <span className="card-badge">Auto generated</span>
                      </div>
                      {summary?.alerts?.length ? (
                        <div className="alert-list">
                          {summary.alerts.map((alert, index) => (
                            <div key={`${alert.title}-${index}`} className={`alert-item${alert.urgent ? " urgent" : ""}`}>
                              <div className={`alert-dot${alert.urgent ? " alert-dot-urgent" : ""}`} />
                              <div className="alert-body">
                                <p className="alert-title">{alert.title}</p>
                                <p className="alert-sub">{alert.sub}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <EmptyState title="No active alerts" subtitle="Alerts will appear after you log more scans." />
                      )}
                    </div>
                  </div>
                </>
              )}

              {page === "predict" && (
                <div className="predict-layout">
                  <div className="card predict-card">
                    <div className="card-header">
                      <span className="card-title">Submit Transaction for Analysis</span>
                      <span className="card-badge">XGBoost + Graph + Rules</span>
                    </div>
                    <PredictForm onResult={handlePredictResult} />
                  </div>

                  {predictResult ? (
                    <div className="card result-card">
                      <div className="card-header"><span className="card-title">Risk Assessment</span></div>
                      {predictResult.error ? (
                        <div className="error-banner">{predictResult.error}</div>
                      ) : (
                        <>
                          <RiskGauge score={Math.round((predictResult.fraud_probability || 0) * 100)} />
                          <div className="result-details">
                            <div className="result-row"><span>Transaction ID</span><strong>{predictResult.transaction_id}</strong></div>
                            <div className="result-row"><span>Fraud Probability</span><strong>{((predictResult.fraud_probability || 0) * 100).toFixed(2)}%</strong></div>
                            <div className="result-row"><span>Risk Score</span><strong>{predictResult.risk_score?.toFixed(2) ?? "-"}</strong></div>
                            <div className="result-row">
                              <span>Risk Level</span>
                              <span className={`status-badge status-${predictResult.risk_level?.toLowerCase()}`}>{predictResult.risk_level ?? "-"}</span>
                            </div>
                          </div>
                          {predictResult.reasons?.length > 0 && (
                            <div className="reasons-list">
                              <p className="reasons-title">Triggered Rules</p>
                              {predictResult.reasons.map((reason, index) => (
                                <div key={`${reason}-${index}`} className="reason-item"><span className="reason-dot" />{reason}</div>
                              ))}
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  ) : (
                    <div className="card info-card">
                      <p className="info-title">What gets updated</p>
                      {[
                        ["⬡", "Prediction history", "Each scan is saved into SQLite for later viewing."],
                        ["◎", "Graph database", "User-device links keep growing with every run."],
                        ["≡", "Dashboard metrics", "Overview, alerts, and analytics refresh from real records."],
                        ["∿", "Presentation flow", "You can create new scans live during your demo."],
                      ].map(([icon, title, subtitle]) => (
                        <div key={title} className="layer-item">
                          <span className="layer-icon">{icon}</span>
                          <div>
                            <p className="layer-title">{title}</p>
                            <p className="layer-sub">{subtitle}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {page === "graph" && (
                <>
                  <div className="stat-grid">
                    {graphData.stats.map((item) => (
                      <div key={item.label} className="stat-card">
                        <span className="stat-label">{item.label}</span>
                        <div className="stat-value">{formatNumber(Number(item.value))}</div>
                      </div>
                    ))}
                  </div>

                  <div className="card">
                    <div className="card-header">
                      <span className="card-title">User-Device Relationship Graph</span>
                      <span className="card-badge">Live fraudguard.db</span>
                    </div>
                    {graphData.nodes.length ? (
                      <>
                        <GraphView data={graphData} />
                        <div className="graph-legend">
                          <span className="leg-item"><span className="leg-dot" style={{ background: "var(--c-user-node)" }} />User Node</span>
                          <span className="leg-item"><span className="leg-dot" style={{ background: "var(--c-device-node)" }} />Device Node</span>
                          <span className="leg-item"><span className="leg-dot" style={{ background: "var(--c-high)" }} />High-risk linkage</span>
                        </div>
                        <p className="graph-note">Dashed red edges highlight connections touching a high-risk saved transaction.</p>
                      </>
                    ) : (
                      <EmptyState title="Graph is empty" subtitle="Run a few predictions and the relationship graph will populate automatically." />
                    )}
                  </div>

                  <div className="card" style={{ marginTop: "16px" }}>
                    <div className="card-header"><span className="card-title">Detected Fraud Clusters</span></div>
                    {clusters.length ? (
                      <div className="cluster-list">
                        {clusters.map((cluster) => (
                          <div key={cluster.id} className="cluster-item">
                            <div>
                              <p className="cluster-id">
                                {cluster.id} <span className={`status-badge status-${cluster.risk}`}>{cluster.risk}</span>
                              </p>
                              <p className="cluster-nodes">{cluster.nodes.join(", ")}</p>
                            </div>
                            <div className="cluster-size">{cluster.size} nodes</div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <EmptyState title="No suspicious clusters yet" subtitle="Clusters appear once the graph reaches larger connected groups." />
                    )}
                  </div>
                </>
              )}

              {page === "transactions" && (
                <div className="card">
                  <div className="card-header">
                    <span className="card-title">All Transactions</span>
                    <div className="filter-row">
                      <select className="filter-select" value={riskFilter} onChange={(event) => setRiskFilter(event.target.value)}>
                        <option value="all">All Risk</option>
                        <option value="high">High</option>
                        <option value="medium">Medium</option>
                        <option value="low">Low</option>
                      </select>
                      <select className="filter-select" value={deviceFilter} onChange={(event) => setDeviceFilter(event.target.value)}>
                        <option value="all">All Devices</option>
                        <option value="mobile">Mobile</option>
                        <option value="desktop">Desktop</option>
                        <option value="tablet">Tablet</option>
                        <option value="unknown">Unknown</option>
                      </select>
                    </div>
                  </div>

                  {filteredTransactions.length ? (
                    <table className="txn-table full-table">
                      <thead>
                        <tr><th>ID</th><th>Time</th><th>Amount</th><th>Device</th><th>Risk</th><th>Score</th><th>Status</th></tr>
                      </thead>
                      <tbody>
                        {filteredTransactions.map((item) => (
                          <tr key={item.id}>
                            <td className="txn-id">{item.id}</td>
                            <td className="muted">{item.date}</td>
                            <td>${Number(item.amount).toLocaleString()}</td>
                            <td><span className="device-pill">{item.device}</span></td>
                            <td><span className={`status-badge status-${item.risk.toLowerCase()}`}>{item.risk}</span></td>
                            <td>
                              <div className="score-bar-wrap">
                                <div
                                  className="score-bar"
                                  style={{
                                    width: `${Math.round(item.risk_score)}%`,
                                    background: item.risk_score >= 70 ? "var(--c-high)" : item.risk_score >= 40 ? "var(--c-med)" : "var(--c-low)",
                                  }}
                                />
                                <span className="score-num">{Math.round(item.risk_score)}</span>
                              </div>
                            </td>
                            <td><span className={`status-badge status-${item.status}`}>{item.status}</span></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <EmptyState title="No matching transactions" subtitle="Change the filters or create a few new scans." />
                  )}
                </div>
              )}

              {page === "analytics" && (
                <>
                  <div className="charts-row">
                    <div className="card chart-card">
                      <div className="card-header"><span className="card-title">Weekly Risk Trends</span></div>
                      <RiskBarChart data={summary?.risk_over_time || []} />
                    </div>
                    <div className="card donut-card">
                      <div className="card-header"><span className="card-title">Risk Split</span></div>
                      <DonutChart breakdown={summary?.breakdown} />
                    </div>
                  </div>

                  <div className="stat-grid" style={{ marginTop: "16px" }}>
                    {(summary?.analytics || []).map((item) => (
                      <div key={item.label} className="stat-card">
                        <span className="stat-label">{item.label}</span>
                        <div className="stat-value">
                          {String(item.value).includes(".") ? item.value : formatNumber(Number(item.value))}
                          {item.label.toLowerCase().includes("rate") ? "%" : ""}
                        </div>
                        <div className={`stat-delta ${item.up === true ? "up" : item.up === false ? "down" : "neutral"}`}>{item.delta}</div>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}
