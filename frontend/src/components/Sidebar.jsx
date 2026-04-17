import "../styles/dashboard.css";

export default function Sidebar() {
  return (
    <div className="sidebar">
      <h2>FraudGuard</h2>

      <ul>
        <li className="active">Dashboard</li>
        <li>Transactions</li>
        <li>Graph</li>
        <li>Clusters</li>
        <li>Analytics</li>
      </ul>
    </div>
  );
}