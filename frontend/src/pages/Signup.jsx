import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

// Turns "python, sql , ml" into ["python", "sql", "ml"]
function toList(commaSeparatedText) {
  return commaSeparatedText
    .split(",")
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
}

export default function Signup() {
  const { signup } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    roll_number: "",
    name: "",
    email: "",
    department: "",
    semester: "",
    skills: "",
    interests: "",
    password: "",
  });
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  function handleChange(field) {
    return (event) => setForm({ ...form, [field]: event.target.value });
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      await signup({
        roll_number: form.roll_number,
        name: form.name,
        email: form.email,
        department: form.department,
        semester: Number(form.semester),
        skills: toList(form.skills),
        interests: toList(form.interests),
        password: form.password,
      });
      navigate("/chat");
    } catch (err) {
      setError(err.response?.data?.detail || "Signup failed. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={handleSubmit}>
        <h1 className="auth-title">Create your CampusMate account</h1>

        {error && <p className="auth-error">{error}</p>}

        <label className="auth-label">
          Roll Number
          <input value={form.roll_number} onChange={handleChange("roll_number")} required />
        </label>

        <label className="auth-label">
          Name
          <input value={form.name} onChange={handleChange("name")} required />
        </label>

        <label className="auth-label">
          Email
          <input type="email" value={form.email} onChange={handleChange("email")} required />
        </label>

        <label className="auth-label">
          Department
          <input value={form.department} onChange={handleChange("department")} required />
        </label>

        <label className="auth-label">
          Semester
          <input
            type="number"
            min="1"
            max="8"
            value={form.semester}
            onChange={handleChange("semester")}
            required
          />
        </label>

        <label className="auth-label">
          Skills (comma separated)
          <input
            placeholder="e.g. Python, SQL, React"
            value={form.skills}
            onChange={handleChange("skills")}
          />
        </label>

        <label className="auth-label">
          Interests (comma separated)
          <input
            placeholder="e.g. AI, Web Development"
            value={form.interests}
            onChange={handleChange("interests")}
          />
        </label>

        <label className="auth-label">
          Password
          <input
            type="password"
            minLength={6}
            value={form.password}
            onChange={handleChange("password")}
            required
          />
        </label>

        <button type="submit" className="auth-button" disabled={isSubmitting}>
          {isSubmitting ? "Creating account..." : "Sign Up"}
        </button>

        <p className="auth-switch">
          Already have an account? <Link to="/login">Login</Link>
        </p>
      </form>
    </div>
  );
}
