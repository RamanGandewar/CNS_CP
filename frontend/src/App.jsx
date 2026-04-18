import { useEffect, useState } from "react";
import Dashboard from "./pages/Dashboard";
import AuthPage from "./pages/AuthPage";
import {
  clearStoredToken,
  getCurrentUser,
  getStoredToken,
  login,
  logout,
  setStoredToken,
  signup,
} from "./services/api";

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = getStoredToken();
    if (!token) {
      setLoading(false);
      return;
    }

    getCurrentUser()
      .then((response) => setUser(response.user))
      .catch(() => clearStoredToken())
      .finally(() => setLoading(false));
  }, []);

  async function handleAuth(mode, payload) {
    const action = mode === "signup" ? signup : login;
    const response = await action(payload);
    setStoredToken(response.token);
    setUser(response.user);
  }

  async function handleLogout() {
    try {
      await logout();
    } catch {
      // Ignore backend logout errors and clear the local session anyway.
    }
    clearStoredToken();
    setUser(null);
  }

  function handleSessionExpired() {
    clearStoredToken();
    setUser(null);
  }

  if (loading) {
    return <div className="app-loading">Loading application...</div>;
  }

  if (!user) {
    return <AuthPage onSubmit={handleAuth} />;
  }

  return <Dashboard user={user} onLogout={handleLogout} onSessionExpired={handleSessionExpired} />;
}

export default App;
