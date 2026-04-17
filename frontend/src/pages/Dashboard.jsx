import { useEffect, useRef } from "react";
import * as d3 from "d3";

export default function Dashboard() {
  const graphRef = useRef();

  useEffect(() => {
    const svg = d3.select(graphRef.current);
    svg.selectAll("*").remove();

    const data = {
      nodes: [
        { id: "U1" },
        { id: "U2" },
        { id: "D1" },
        { id: "D2" }
      ],
      links: [
        { source: "U1", target: "D1" },
        { source: "U2", target: "D1" },
        { source: "U2", target: "D2" }
      ]
    };

    const simulation = d3.forceSimulation(data.nodes)
      .force("link", d3.forceLink(data.links).id(d => d.id))
      .force("charge", d3.forceManyBody().strength(-120))
      .force("center", d3.forceCenter(300, 150));

    const link = svg.append("g")
      .selectAll("line")
      .data(data.links)
      .enter()
      .append("line")
      .attr("stroke", "#ddd");

    const node = svg.append("g")
      .selectAll("circle")
      .data(data.nodes)
      .enter()
      .append("circle")
      .attr("r", 8)
      .attr("fill", "#16a34a");

    simulation.on("tick", () => {
      link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

      node
        .attr("cx", d => d.x)
        .attr("cy", d => d.y);
    });
  }, []);

  return (
    <div className="dashboard">

      {/* SIDEBAR */}
      <div className="sidebar">
        <h2>FraudGuard</h2>

        <div className="section">Menu</div>
        <div className="nav active">🏠 Dashboard</div>
        <div className="nav">💳 Transactions</div>
        <div className="nav">🔗 Graph</div>
        <div className="nav">🧠 Clusters</div>
        <div className="nav">📊 Analytics</div>

        <div className="section">General</div>
        <div className="nav">⚙️ Settings</div>
        <div className="nav">❓ Help</div>
        <div className="nav">🚪 Logout</div>

        <div className="promo">
          <p>Download our Mobile App</p>
          <button>Download</button>
        </div>
      </div>

      {/* MAIN */}
      <div className="main">

        {/* NAVBAR */}
        <div className="navbar">
          <input placeholder="🔍 Search here" />
          <div className="rightNav">
            🔔 ⚙️
            <div className="user">
              <div className="avatar">R</div>
              <div>
                <p>Raman</p>
                <small>raman@email.com</small>
              </div>
            </div>
          </div>
        </div>

        {/* HEADER */}
        <h1>Fraud Detection Dashboard</h1>
        <p className="subtitle">
          Plan, monitor, and respond to fraud with ease
        </p>

        {/* STATS */}
        <div className="stats">
          <div className="card highlight">
            <p>Total Transactions</p>
            <h2>1,200</h2>
            <span>↑ 4 increased</span>
          </div>

          <div className="card">
            <p>Fraud Detected</p>
            <h2>34</h2>
            <span>↑ 2 increased</span>
          </div>

          <div className="card">
            <p>Active Users</p>
            <h2>560</h2>
            <span>Stable</span>
          </div>

          <div className="card">
            <p>High Risk Alerts</p>
            <h2>12</h2>
            <span>↓ 1 decreased</span>
          </div>
        </div>

        {/* MIDDLE */}
        <div className="middle">
          <div className="panel graph">
            <h3>Fraud Graph</h3>
            <svg ref={graphRef} width={600} height={300}></svg>
          </div>

          <div className="right">
            <div className="panel">
              <h3>Reminders</h3>
              <p>Meeting with fraud team</p>
              <button className="btn">Start Meeting</button>
            </div>

            <div className="panel">
              <h3>Insights</h3>
              <ul>
                <li>High fraud activity</li>
                <li>Device sharing detected</li>
                <li>Cluster anomaly found</li>
              </ul>
            </div>
          </div>
        </div>

        {/* BOTTOM */}
        <div className="bottom">

          {/* Transactions */}
          <div className="panel">
            <h3>Recent Transactions</h3>
            <div className="list">
              <div className="item">Aman — Flagged</div>
              <div className="item">Riya — Clear</div>
              <div className="item">John — Pending</div>
              <div className="item">Sara — Flagged</div>
            </div>
          </div>

          {/* Progress */}
          <div className="panel center">
            <h3>Detection Progress</h3>
            <div className="circle">41%</div>
          </div>

          {/* Timer */}
          <div className="panel center">
            <h3>Time Tracker</h3>
            <h2>01:24:08</h2>
            <div>
              <button>⏸</button>
              <button>⏹</button>
            </div>
          </div>

        </div>

      </div>

      {/* CSS */}
      <style>{`
        .dashboard { display:flex; background:#f8fafc; font-family:sans-serif; }

        .sidebar { width:240px; background:white; padding:20px; }
        .sidebar h2 { color:#16a34a; }
        .section { margin-top:20px; font-size:12px; color:gray; }
        .nav { padding:8px; margin:4px 0; color:gray; }
        .nav.active { background:#dcfce7; border-left:4px solid #16a34a; color:#16a34a; }

        .promo { margin-top:20px; background:#065f46; color:white; padding:10px; border-radius:10px; }

        .main { flex:1; padding:25px; }

        .navbar { display:flex; justify-content:space-between; margin-bottom:15px; }
        .rightNav { display:flex; align-items:center; gap:15px; }

        .avatar { background:#16a34a; color:white; padding:8px; border-radius:50%; }

        .stats { display:grid; grid-template-columns:repeat(4,1fr); gap:15px; }
        .card { background:white; padding:15px; border-radius:12px; }
        .card.highlight { background:#16a34a; color:white; }

        .middle { display:flex; gap:20px; margin-top:20px; }
        .panel { background:white; padding:15px; border-radius:12px; }
        .graph { flex:2; }
        .right { flex:1; display:flex; flex-direction:column; gap:20px; }

        .bottom { display:grid; grid-template-columns:repeat(3,1fr); gap:20px; margin-top:20px; }

        .circle {
          width:100px; height:100px;
          border-radius:50%;
          border:8px solid #16a34a;
          display:flex; align-items:center; justify-content:center;
        }

        .center { text-align:center; }
      `}</style>

    </div>
  );
}