import { useState, useEffect } from "react";
import { Plus, MessageSquare, LogOut, Loader, Trash2, Pencil, Check, X, Search, PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { removeToken, getToken } from "../utils/auth";
import { hydrateSessionSearchCache, searchSessions } from "../services/sessionSearchService";

export default function Sidebar({ activeSession, setActiveSession }) {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Modal state
  const [sessionToDelete, setSessionToDelete] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [renamingSessionId, setRenamingSessionId] = useState(null);
  const [renameValue, setRenameValue] = useState("");
  const [isRenaming, setIsRenaming] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchCache, setSearchCache] = useState({});
  const [searchResults, setSearchResults] = useState([]);
  const [isSearchLoading, setIsSearchLoading] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(() => localStorage.getItem("sidebar_collapsed") === "1");

  useEffect(() => {
    fetchProfileAndSessions();
  }, [activeSession]);

  useEffect(() => {
    const onEscape = (e) => {
      if (e.key === "Escape") {
        setSearchOpen(false);
      }
    };
    window.addEventListener("keydown", onEscape);
    return () => window.removeEventListener("keydown", onEscape);
  }, []);

  useEffect(() => {
    const q = searchQuery.trim();
    if (!searchOpen || !q) {
      setSearchResults([]);
      return;
    }

    const timeout = setTimeout(async () => {
      setIsSearchLoading(true);
      try {
        const token = getToken();
        if (!token) return;
        const cache = await hydrateSessionSearchCache(sessions, token, searchCache);
        setSearchCache(cache);
        setSearchResults(searchSessions(cache, q));
      } finally {
        setIsSearchLoading(false);
      }
    }, 280);

    return () => clearTimeout(timeout);
  }, [searchQuery, searchOpen, sessions]);

  const fetchProfileAndSessions = async () => {
    try {
      const token = getToken();
      if (!token) { navigate("/login"); return; }
      
      const headers = { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };

      const profileRes = await fetch("http://127.0.0.1:8002/api/v1/dashboard/profile", { headers });
      if (profileRes.ok) {
        setUser(await profileRes.json());
      } else {
        removeToken(); navigate("/login"); return;
      }

      const sessionsRes = await fetch("http://127.0.0.1:8002/api/v1/dashboard/sessions", { headers });
      if (sessionsRes.ok) {
        setSessions(await sessionsRes.json());
      }
      setLoading(false);
    } catch (error) {
      console.error("Error fetching dashboard data", error);
      setLoading(false);
    }
  };

  const handleDeleteClick = (e, sessionId) => {
    e.stopPropagation(); // prevent activating the session
    setSessionToDelete(sessionId);
  };

  const startRename = (e, session) => {
    e.stopPropagation();
    setRenamingSessionId(session.session_id);
    setRenameValue(session.session_name || `Session ${session.session_id.substring(0, 8)}`);
  };

  const cancelRename = (e) => {
    e.stopPropagation();
    setRenamingSessionId(null);
    setRenameValue("");
  };

  const submitRename = async (e, sessionId) => {
    e.stopPropagation();
    const nextName = renameValue.trim();
    if (!nextName || isRenaming) return;

    setIsRenaming(true);
    try {
      const token = getToken();
      const res = await fetch(`http://127.0.0.1:8002/api/v1/dashboard/sessions/${sessionId}/name`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ session_name: nextName })
      });

      if (res.ok) {
        setSessions(prev => prev.map(s => (
          s.session_id === sessionId ? { ...s, session_name: nextName } : s
        )));
        setRenamingSessionId(null);
        setRenameValue("");
      } else {
        console.error("Failed to rename session");
      }
    } catch (error) {
      console.error("Rename error", error);
    } finally {
      setIsRenaming(false);
    }
  };

  const confirmDelete = async () => {
    if (!sessionToDelete) return;
    setIsDeleting(true);
    try {
      const token = getToken();
      const headers = { Authorization: `Bearer ${token}` };
      const res = await fetch(`http://127.0.0.1:8002/api/v1/dashboard/sessions/${sessionToDelete}`, {
        method: "DELETE",
        headers
      });
      if (res.ok) {
        setSessions(sessions.filter(s => s.session_id !== sessionToDelete));
        if (activeSession === sessionToDelete) {
          setActiveSession(null);
        }
      } else {
        console.error("Failed to delete session");
      }
    } catch (error) {
      console.error("Delete error", error);
    } finally {
      setIsDeleting(false);
      setSessionToDelete(null);
    }
  };

  const handleLogout = () => { removeToken(); navigate("/login"); };
  const toggleSidebar = () => {
    const next = !isCollapsed;
    setIsCollapsed(next);
    localStorage.setItem("sidebar_collapsed", next ? "1" : "0");
  };

  const handleSearchResultClick = (sessionId) => {
    setActiveSession(sessionId);
    setSearchOpen(false);
    setSearchQuery("");
  };

  return (
    <>
      <div className={`sidebar-custom d-flex flex-column ${isCollapsed ? "collapsed" : ""}`}>
        {/* Collapse Toggle */}
        <div className={`d-flex ${isCollapsed ? "justify-content-center" : "justify-content-end"} px-2 pt-2`}>
          <button
            className="btn btn-sm btn-link text-muted-custom border-0 sidebar-toggle-btn"
            onClick={toggleSidebar}
            title={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
            style={{ textDecoration: "none" }}
          >
            {isCollapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
          </button>
        </div>

        {/* New Chat */}
        <div className="p-3 pb-2">
          <button
            className={`btn btn-white w-100 d-flex align-items-center justify-content-center gap-2 py-2 ${isCollapsed ? "sidebar-icon-btn" : ""}`}
            onClick={() => setActiveSession(null)}
            title="New Incident"
          >
            <Plus size={16} strokeWidth={2.5} />
            {!isCollapsed && <span className="fw-semibold" style={{ fontSize: "0.85rem" }}>New Incident</span>}
          </button>
        </div>

        {/* Search */}
        <div className="px-3 pb-2">
          <button
            className={`btn btn-dark border-secondary w-100 d-flex align-items-center gap-2 py-2 ${isCollapsed ? "justify-content-center sidebar-icon-btn" : "justify-content-start"}`}
            onClick={() => setSearchOpen(true)}
            title="Search Sessions"
          >
            <Search size={14} />
            {!isCollapsed && <span style={{ fontSize: "0.8rem" }} className="text-muted-custom">Search Sessions</span>}
          </button>
        </div>

        {/* Label */}
        {!isCollapsed && (
          <div className="px-3 py-1">
            <small className="text-uppercase fw-bold text-muted-custom" style={{ fontSize: "0.65rem", letterSpacing: "0.1em" }}>
              Recent
            </small>
          </div>
        )}

        {/* Sessions */}
        <div className="sidebar-sessions px-2 flex-grow-1">
          {loading ? (
            <div className="d-flex justify-content-center py-4">
              <Loader className="spin" size={18} color="#555" />
            </div>
          ) : sessions.length === 0 ? (
            <p className="text-center text-muted-custom small px-3 py-4">
              No conversations yet. Start a new incident.
            </p>
          ) : (
            <div className="d-flex flex-column gap-1 py-1">
              {sessions.map((s) => (
                <div 
                  key={s.session_id} 
                  className={`session-btn ${activeSession === s.session_id ? "active" : ""}`}
                  onClick={() => setActiveSession(s.session_id)}
                  title={s.session_name || `Session ${s.session_id.substring(0, 8)}`}
                >
                  <MessageSquare size={14} className="flex-shrink-0" />
                  {!isCollapsed && renamingSessionId === s.session_id ? (
                    <input
                      value={renameValue}
                      onChange={(e) => setRenameValue(e.target.value)}
                      onClick={(e) => e.stopPropagation()}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") submitRename(e, s.session_id);
                        if (e.key === "Escape") cancelRename(e);
                      }}
                      className="form-control form-control-sm bg-dark text-white border-secondary"
                      style={{ minWidth: 0, height: 28 }}
                      maxLength={120}
                      autoFocus
                    />
                  ) : !isCollapsed ? (
                    <span className="text-truncate flex-grow-1">
                      {s.session_name || `Session ${s.session_id.substring(0, 8)}`}
                    </span>
                  ) : null}
                  {!isCollapsed && s.message_count > 0 && (
                    <span className="badge bg-dark text-muted-custom me-1" style={{ fontSize: "0.6rem" }}>
                      {s.message_count}
                    </span>
                  )}
                  {!isCollapsed && renamingSessionId === s.session_id ? (
                    <>
                      <button
                        className="btn btn-link text-success p-1"
                        onClick={(e) => submitRename(e, s.session_id)}
                        title="Save Name"
                        style={{ textDecoration: "none" }}
                        disabled={isRenaming}
                      >
                        {isRenaming ? <Loader size={13} className="spin" /> : <Check size={13} />}
                      </button>
                      <button
                        className="btn btn-link text-secondary p-1"
                        onClick={cancelRename}
                        title="Cancel"
                        style={{ textDecoration: "none" }}
                        disabled={isRenaming}
                      >
                        <X size={13} />
                      </button>
                    </>
                  ) : !isCollapsed ? (
                    <button
                      className="btn btn-link text-secondary p-1"
                      onClick={(e) => startRename(e, s)}
                      title="Rename Chat"
                      style={{ textDecoration: "none" }}
                    >
                      <Pencil size={13} className="text-muted-custom" />
                    </button>
                  ) : null}
                  {!isCollapsed && (
                    <button 
                      className="btn btn-link text-secondary p-1 ms-auto"
                      onClick={(e) => handleDeleteClick(e, s.session_id)}
                      title="Delete Chat"
                      style={{textDecoration: "none"}}
                    >
                      <Trash2 size={13} className="text-muted-custom" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer / User Info */}
        <div 
          className={`border-top border-dark p-3 d-flex align-items-center ${isCollapsed ? "justify-content-center" : "gap-2"}`} 
          style={{ borderColor: "#1a1a1a !important", cursor: "pointer" }}
          onClick={() => navigate("/profile")}
          title="View Profile"
        >
          <div className="d-flex align-items-center justify-content-center rounded-2 fw-bold" style={{ width: 32, height: 32, background: "#fff", color: "#000", fontSize: "0.8rem", flexShrink: 0 }}>
            {user ? user.first_name.charAt(0).toUpperCase() : "U"}
          </div>
          {!isCollapsed && (
            <div className="flex-grow-1 overflow-hidden pointer-event">
              <div className="text-truncate fw-medium hover-text-white transition" style={{ fontSize: "0.82rem" }}>
                {user ? `${user.first_name} ${user.last_name}` : "Loading..."}
              </div>
              <div className="text-muted-custom text-capitalize" style={{ fontSize: "0.7rem" }}>
                {user ? user.role : "—"}
              </div>
            </div>
          )}
          <button 
            className="btn btn-sm p-1 text-muted-custom border-0" 
            onClick={(e) => { e.stopPropagation(); handleLogout(); }} 
            title="Sign Out" 
            style={{ background: "transparent" }}
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>

      {/* Bootstrap Native Confirmation Modal Overlay */}
      {sessionToDelete && (
        <div className="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center" style={{ zIndex: 1050, background: "rgba(0,0,0,0.8)", backdropFilter: "blur(4px)" }}>
          <div className="bg-dark text-center p-4 rounded-4 shadow-lg border border-secondary" style={{ maxWidth: "380px", width: "90%" }}>
            <h5 className="text-white mb-2 fw-bold">Delete Conversation</h5>
            <p className="text-secondary small mb-4">
              Are you sure you want to permanently delete this chat history? This action cannot be undone.
            </p>
            <div className="d-flex justify-content-center gap-3">
              <button 
                className="btn btn-outline-light px-4 py-2 fw-medium rounded-3" 
                onClick={() => setSessionToDelete(null)}
                disabled={isDeleting}
              >
                Cancel
              </button>
              <button 
                className="btn btn-danger px-4 py-2 fw-medium rounded-3 d-flex align-items-center gap-2" 
                onClick={confirmDelete}
                disabled={isDeleting}
              >
                {isDeleting ? <Loader size={16} className="spin" /> : <Trash2 size={16} />}
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Session Search Overlay */}
      {searchOpen && (
        <div
          className="session-search-overlay position-fixed top-0 start-0 w-100 h-100 d-flex align-items-start justify-content-center"
          style={{ zIndex: 1200, background: "rgba(0,0,0,0.45)", backdropFilter: "blur(2px)", paddingTop: "8vh" }}
          onClick={() => setSearchOpen(false)}
        >
          <div
            className="session-search-panel bg-dark border border-secondary rounded-4 shadow-lg"
            style={{ width: "min(860px, 92vw)", maxHeight: "72vh", overflow: "hidden" }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-3 border-bottom border-secondary d-flex align-items-center gap-2">
              <Search size={16} className="text-muted-custom" />
              <input
                className="form-control bg-dark text-white border-0 session-search-input"
                placeholder="Search by session name or any message keyword..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                autoFocus
              />
              <button
                className="btn btn-sm btn-link text-muted-custom"
                onClick={() => setSearchOpen(false)}
                style={{ textDecoration: "none" }}
              >
                <X size={16} />
              </button>
            </div>

            <div style={{ maxHeight: "58vh", overflowY: "auto" }}>
              {isSearchLoading ? (
                <div className="p-4 d-flex align-items-center gap-2 text-muted-custom">
                  <Loader size={16} className="spin" />
                  Searching sessions...
                </div>
              ) : !searchQuery.trim() ? (
                <div className="p-4 text-muted-custom small">
                  Start typing to search session names and chat history.
                </div>
              ) : searchResults.length === 0 ? (
                <div className="p-4 text-muted-custom small">
                  No sessions found for "{searchQuery}".
                </div>
              ) : (
                <div className="list-group list-group-flush">
                  {searchResults.map((r) => (
                    <button
                      key={r.session_id}
                      className="list-group-item list-group-item-action bg-dark text-white border-secondary text-start session-search-item"
                      onClick={() => handleSearchResultClick(r.session_id)}
                    >
                      <div className="d-flex align-items-center justify-content-between gap-2">
                        <div className="fw-semibold text-truncate">
                          {r.session_name || `Session ${r.session_id.substring(0, 8)}`}
                        </div>
                        <small className="text-muted-custom">{r.message_count} msgs</small>
                      </div>
                      {r.preview && (
                        <div className="text-muted-custom small mt-1 text-truncate">
                          {r.preview}
                        </div>
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
