import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

const api = axios.create({
  baseURL: API_BASE_URL,
});

// ---- Request interceptor ----
// Runs before every request. Attaches the JWT token (if we have one)
// as an "Authorization: Bearer <token>" header.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("campusmate_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ---- Response interceptor ----
// Runs after every response. If the backend says our token is
// invalid/expired (401 Unauthorized), we log the student out and
// send them back to the login page.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem("campusmate_token");
      localStorage.removeItem("campusmate_student");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default api;
