const DASHBOARD_BASE = "http://127.0.0.1:8002/api/v1/dashboard";

const normalize = (text = "") =>
  text.toString().toLowerCase().replace(/\s+/g, " ").trim();

const createPreview = (messages = []) => {
  const firstText = messages
    .map((m) => (m?.content || "").trim())
    .find((t) => t.length > 0);
  if (!firstText) return "";
  return firstText.length > 140 ? `${firstText.slice(0, 140)}...` : firstText;
};

const buildSearchDocument = (session, messages = []) => {
  const title = session.session_name || "";
  const text = messages.map((m) => m.content || "").join(" ");
  return normalize(`${title} ${text}`);
};

export async function hydrateSessionSearchCache(sessions, token, existingCache = {}) {
  const cache = { ...existingCache };
  const missing = sessions.filter((s) => !cache[s.session_id]);

  await Promise.all(
    missing.map(async (session) => {
      try {
        const res = await fetch(`${DASHBOARD_BASE}/sessions/${session.session_id}/history`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (!res.ok) return;
        const data = await res.json();
        const messages = data.messages || [];
        cache[session.session_id] = {
          session_id: session.session_id,
          session_name: session.session_name || "",
          message_count: session.message_count || 0,
          created_at: session.created_at,
          preview: createPreview(messages),
          searchable_text: buildSearchDocument(session, messages)
        };
      } catch (error) {
        console.error("Session history fetch failed for search:", session.session_id, error);
      }
    })
  );

  return cache;
}

export function searchSessions(cache, query, limit = 20) {
  const q = normalize(query);
  if (!q) return [];

  const records = Object.values(cache);
  const scored = records
    .map((r) => {
      const title = normalize(r.session_name);
      const doc = r.searchable_text || "";
      const inTitle = title.includes(q);
      const inDoc = doc.includes(q);
      if (!inTitle && !inDoc) return null;
      const score = (inTitle ? 2 : 0) + (inDoc ? 1 : 0) + (r.message_count > 0 ? 0.2 : 0);
      return { ...r, score };
    })
    .filter(Boolean)
    .sort((a, b) => b.score - a.score || new Date(b.created_at) - new Date(a.created_at));

  return scored.slice(0, limit);
}

