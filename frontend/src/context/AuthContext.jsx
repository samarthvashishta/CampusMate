// -----------------------------------------------------------------
// AuthContext.jsx
//
// Holds the logged-in student's info (and JWT token) in one place,
// so any component can read/update it with useAuth() instead of
// passing props around everywhere. We use React's built-in Context
// API here - no Redux needed for a project this size.
// -----------------------------------------------------------------

import { createContext, useContext, useState } from "react";
import * as authService from "../services/authService";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  // Read any saved login info from localStorage so a page refresh
  // doesn't log the student out.
  const [token, setToken] = useState(() =>
    localStorage.getItem("campusmate_token")
  );
  const [student, setStudent] = useState(() => {
    const saved = localStorage.getItem("campusmate_student");
    return saved ? JSON.parse(saved) : null;
  });

  function saveSession(newToken, newStudent) {
    localStorage.setItem("campusmate_token", newToken);
    localStorage.setItem("campusmate_student", JSON.stringify(newStudent));
    setToken(newToken);
    setStudent(newStudent);
  }

  async function login(rollNumber, password) {
    const data = await authService.login({
      roll_number: rollNumber,
      password,
    });
    saveSession(data.access_token, data.student);
  }

  async function signup(signupData) {
    const data = await authService.signup(signupData);
    saveSession(data.access_token, data.student);
  }

  function logout() {
    localStorage.removeItem("campusmate_token");
    localStorage.removeItem("campusmate_student");
    setToken(null);
    setStudent(null);
  }

  function updateStudent(newStudent) {
    localStorage.setItem("campusmate_student", JSON.stringify(newStudent));
    setStudent(newStudent);
  }

  const value = {
    token,
    student,
    isAuthenticated: Boolean(token),
    login,
    signup,
    logout,
    updateStudent,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// Small helper hook so components can just call useAuth() instead of
// importing useContext + AuthContext every time.
export function useAuth() {
  return useContext(AuthContext);
}
