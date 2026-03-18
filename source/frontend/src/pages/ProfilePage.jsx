import { useState, useEffect } from "react";
import { User, Lock, Mail, Save, ArrowLeft, Loader } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { getToken, removeToken } from "../utils/auth";

export default function ProfilePage() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState({ first_name: "", last_name: "", email: "", role: "" });
  const [passwords, setPasswords] = useState({ newPassword: "", confirmPassword: "" });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const token = getToken();
      if (!token) { navigate("/login"); return; }
      const headers = { Authorization: `Bearer ${token}` };
      const res = await fetch("http://127.0.0.1:8002/api/v1/dashboard/profile", { headers });
      if (res.ok) {
        const data = await res.json();
        setProfile({
          first_name: data.first_name || "",
          last_name: data.last_name || "",
          email: data.email || "",
          role: data.role || ""
        });
      } else {
        removeToken(); navigate("/login"); return;
      }
    } catch (err) {
      console.error(err);
      setError("Failed to load profile.");
    } finally {
      setLoading(false);
    }
  };

  const handleProfileChange = (e) => {
    setProfile({ ...profile, [e.target.name]: e.target.value });
  };

  const handlePasswordChange = (e) => {
    setPasswords({ ...passwords, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (passwords.newPassword && passwords.newPassword !== passwords.confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setSaving(true);
    try {
      const token = getToken();
      const payload = {
        first_name: profile.first_name,
        last_name: profile.last_name,
        email: profile.email
      };

      if (passwords.newPassword) {
        payload.password = passwords.newPassword;
      }

      const res = await fetch("http://127.0.0.1:8001/api/v1/auth/me", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.detail || "Failed to update profile");
      } else {
        setSuccess("Profile updated successfully");
        setPasswords({ newPassword: "", confirmPassword: "" });

        if (data.relogin_required) {
          setTimeout(() => {
            removeToken();
            navigate("/login");
          }, 2000);
        }
      }
    } catch (err) {
      console.error(err);
      setError("An error occurred while updating profile");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="d-flex align-items-center justify-content-center bg-black min-vh-100 w-100 text-white">
        <Loader className="spin" size={32} />
      </div>
    );
  }

  return (
    <div className="bg-black min-vh-100 w-100 d-flex flex-column align-items-center justify-content-center p-4">

      <div className="w-100 mb-4" style={{ maxWidth: "500px" }}>
        <button
          onClick={() => navigate("/dashboard")}
          className="btn btn-dark text-white d-flex align-items-center gap-2 border border-secondary"
        >
          <ArrowLeft size={16} /> Back to Chat
        </button>
      </div>

      <div className="bg-dark rounded-4 border border-secondary p-4 p-md-5 shadow-lg w-100" style={{ maxWidth: "500px" }}>
        <div className="text-center mb-4">
          <div className="d-inline-flex bg-black p-3 rounded-circle border border-secondary mb-3">
            <User size={32} className="text-white" />
          </div>
          <h2 className="text-white fw-bold">My Profile</h2>
          <p className="text-secondary small">Manage your account settings and preferences.</p>
        </div>

        {error && (
          <div className="alert bg-black border border-danger text-danger p-3 rounded-3 small mb-4">
            {error}
          </div>
        )}

        {success && (
          <div className="alert bg-black border border-success text-success p-3 rounded-3 small mb-4">
            {success} {success.includes("rel") && "You will be redirected to login shortly."}
          </div>
        )}

        <form onSubmit={handleSubmit}>

          <div className="row g-3 mb-3">
            <div className="col-sm-6">
              <label className="form-label text-secondary small fw-medium text-uppercase mb-1" style={{ letterSpacing: "0.5px" }}>First Name</label>
              <input
                type="text"
                className="form-control bg-black text-white border-secondary rounded-3"
                name="first_name"
                value={profile.first_name}
                onChange={handleProfileChange}
                required
              />
            </div>
            <div className="col-sm-6">
              <label className="form-label text-secondary small fw-medium text-uppercase mb-1" style={{ letterSpacing: "0.5px" }}>Last Name</label>
              <input
                type="text"
                className="form-control bg-black text-white border-secondary rounded-3"
                name="last_name"
                value={profile.last_name}
                onChange={handleProfileChange}
                required
              />
            </div>
          </div>

          <div className="mb-4">
            <label className="form-label text-secondary small fw-medium text-uppercase mb-1 d-flex gap-2 align-items-center" style={{ letterSpacing: "0.5px" }}>
              <Mail size={14} /> Email Address
            </label>
            <input
              type="email"
              className="form-control bg-black text-white border-secondary rounded-3"
              name="email"
              value={profile.email}
              onChange={handleProfileChange}
              required
            />
            <div className="form-text text-muted mt-2" style={{ fontSize: "0.75rem" }}>
              Changing your email will require you to log in again.
            </div>
          </div>

          <hr className="border-secondary my-4" />

          <div className="mb-4">
            <h5 className="text-white fw-semibold mb-3 d-flex align-items-center gap-2">
              <Lock size={16} /> Change Password
            </h5>
            <div className="mb-3">
              <input
                type="password"
                className="form-control bg-black text-white border-secondary rounded-3"
                placeholder="New Password (leave blank to keep current)"
                name="newPassword"
                value={passwords.newPassword}
                onChange={handlePasswordChange}
                minLength="6"
              />
            </div>
            <div>
              <input
                type="password"
                className="form-control bg-black text-white border-secondary rounded-3"
                placeholder="Confirm New Password"
                name="confirmPassword"
                value={passwords.confirmPassword}
                onChange={handlePasswordChange}
                minLength="6"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={saving}
            className="btn btn-light w-100 fw-bold py-2 rounded-3 d-flex align-items-center justify-content-center gap-2"
          >
            {saving ? <Loader size={18} className="spin" /> : <Save size={18} />}
            {saving ? "Saving Changes..." : "Save Changes"}
          </button>
        </form>
      </div>
    </div>
  );
}
