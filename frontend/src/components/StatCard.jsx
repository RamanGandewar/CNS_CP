import "../styles/dashboard.css";

export default function StatCard({ title, value, highlight }) {
  return (
    <div className={`card ${highlight ? "highlight" : ""}`}>
      <h4>{title}</h4>
      <h2>{value}</h2>
    </div>
  );
}