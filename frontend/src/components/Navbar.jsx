// -----------------------------------------------------------------
// Navbar.jsx
//
// Top bar shown on every page after login: app name, a link to the
// profile page, and a logout button.
// -----------------------------------------------------------------

import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { student, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <header className="navbar">
      <Link to="/chat" className="navbar-brand">
        CampusMate
      </Link>

      <div className="navbar-right">
        {student && <span className="navbar-username">Hi, {student.name}</span>}
        <Link to="/profile" className="navbar-link">
          Profile
        </Link>
        <button className="navbar-logout" onClick={handleLogout}>
          Logout
        </button>
      </div>
    </header>
  );
}
