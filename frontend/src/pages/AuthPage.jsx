import { useState } from "react";
import "../styles/dashboard.css";

const initialState = {
  name: "",
  email: "",
  password: "",
};

function FraudGuardMark() {
  return (
    <div className="fraudguard-mark">
      <span className="fraudguard-mark-icon" />
      <span className="fraudguard-mark-text">FraudGuard</span>
    </div>
  );
}

export default function AuthPage({ onSubmit }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState(initialState);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const payload = mode === "signup"
        ? form
        : { email: form.email, password: form.password };
      await onSubmit(mode, payload);
      setForm(initialState);
    } catch (submitError) {
      setError(submitError.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-shell auth-shell-compact">
      <div className="auth-hero auth-hero-compact">
        <div className="auth-hero-panel">
          <div className="auth-topbar">
            <FraudGuardMark />
            <span className="auth-topbar-arrow">‹</span>
          </div>

          <div className="auth-hero-content auth-hero-content-compact">
            <span className="auth-badge">Live Demo Dashboard</span>
            <h1>Real-time fraud detection for your presentation.</h1>
            <p>Log in, run a prediction, and the dashboard, transactions, and graph all update from the live database.</p>
          </div>
        </div>
      </div>

      <div className="auth-panel">
        <form className="auth-card auth-card-compact" onSubmit={handleSubmit}>
          <div className="auth-card-header auth-card-header-compact">
            <FraudGuardMark />
            <div>
              <p className="auth-title">{mode === "login" ? "Welcome back" : "Create your account"}</p>
              <p className="auth-subtitle">
                {mode === "login"
                  ? "Access the FraudGuard dashboard."
                  : "Set up an account to use the dashboard."}
              </p>
            </div>
          </div>

          {mode === "signup" && (
            <div className="form-group">
              <label>Full Name</label>
              <input
                type="text"
                placeholder="Your name"
                value={form.name}
                onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
                required
              />
            </div>
          )}

          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              placeholder="name@example.com"
              value={form.email}
              onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
              required
            />
          </div>

          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              placeholder="Minimum 6 characters"
              value={form.password}
              onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
              required
            />
          </div>

          {error && <div className="error-banner">{error}</div>}

          <button type="submit" className="btn-predict" disabled={loading}>
            {loading && <span className="spinner" />}
            {loading ? "Please wait..." : mode === "login" ? "Log In" : "Sign Up"}
          </button>

          <button
            type="button"
            className="auth-switch"
            onClick={() => {
              setMode((current) => (current === "login" ? "signup" : "login"));
              setError("");
            }}
          >
            {mode === "login" ? "Need an account? Create one" : "Already registered? Log in"}
          </button>
        </form>
      </div>
    </div>
  );
}
