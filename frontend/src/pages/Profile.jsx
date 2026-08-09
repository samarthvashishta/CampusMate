import { useEffect, useState } from "react";
import Navbar from "../components/Navbar";
import { useAuth } from "../context/AuthContext";
import * as authService from "../services/authService";

function toList(commaSeparatedText) {
  return commaSeparatedText
    .split(",")
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
}

export default function Profile() {
  const { updateStudent } = useAuth();

  const [form, setForm] = useState(null); // profile fields being edited
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    authService.getMyProfile().then((profile) => {
      setForm({
        name: profile.name,
        email: profile.email,
        department: profile.department,
        semester: profile.semester,
        skills: profile.skills.join(", "),
        interests: profile.interests.join(", "),
      });
    });
  }, []);

  function handleChange(field) {
    return (event) => setForm({ ...form, [field]: event.target.value });
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    setIsSaving(true);

    try {
      const updated = await authService.updateMyProfile({
        name: form.name,
        email: form.email,
        department: form.department,
        semester: Number(form.semester),
        skills: toList(form.skills),
        interests: toList(form.interests),
      });
      updateStudent(updated);
      setMessage("Profile updated successfully.");
    } catch (err) {
      setError(err.response?.data?.detail || "Could not update profile.");
    } finally {
      setIsSaving(false);
    }
  }

  if (!form) {
    return (
      <div className="page-with-navbar">
        <Navbar />
        <div className="profile-page">Loading profile...</div>
      </div>
    );
  }

  return (
    <div className="page-with-navbar">
      <Navbar />
      <div className="profile-page">
        <form className="profile-card" onSubmit={handleSubmit}>
          <h1 className="profile-title">My Profile</h1>

          {message && <p className="auth-success">{message}</p>}
          {error && <p className="auth-error">{error}</p>}

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
            <input value={form.skills} onChange={handleChange("skills")} />
          </label>

          <label className="auth-label">
            Interests (comma separated)
            <input value={form.interests} onChange={handleChange("interests")} />
          </label>

          <button type="submit" className="auth-button" disabled={isSaving}>
            {isSaving ? "Saving..." : "Save Changes"}
          </button>
        </form>
      </div>
    </div>
  );
}
