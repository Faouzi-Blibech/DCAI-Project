// data.jsx — LIVE version. Replaces the original static-seed data.jsx.
// Fetches from the Flask API at /api/* and populates window.HIDE_DATA in
// the exact shape the rest of the React design expects, then dispatches
// a "hide-data-ready" event so app.jsx can render.

const API = '/api';

async function fetchAll() {
  const [overview, researchers, clusters, collabs, agents, logs, labs, expertise] =
    await Promise.all([
      fetch(`${API}/overview`).then(r => r.json()),
      fetch(`${API}/researchers`).then(r => r.json()),
      fetch(`${API}/clusters`).then(r => r.json()),
      fetch(`${API}/collaborations`).then(r => r.json()),
      fetch(`${API}/agents`).then(r => r.json()),
      fetch(`${API}/logs?n=50`).then(r => r.json()),
      fetch(`${API}/labs`).then(r => r.json()),
      fetch(`${API}/expertise`).then(r => r.json()),
    ]);

  window.HIDE_DATA = {
    LABS: labs.map((name, i) => ({
      id: `L${String(i + 1).padStart(2, '0')}`,
      name,
      head: '',
      members: 0,
    })),
    CLUSTERS: clusters,
    EXPERTISE: expertise,
    RESEARCHERS: researchers,
    PUBLICATIONS: overview.recent_publications,
    PUBS_PER_YEAR: overview.pubs_per_year,
    COLLABS: collabs,
    AGENTS: agents,
    LOG_LINES: logs,
    _stats: {
      researchers_count:  overview.researchers_count,
      labs_count:         overview.labs_count,
      publications_count: overview.publications_count,
      avg_h_index:        overview.avg_h_index,
      clusters_count:     overview.clusters_count,
    },
    _top_labs: overview.top_labs,
  };

  window.dispatchEvent(new Event('hide-data-ready'));
}

window._hideRefresh = fetchAll;

fetchAll().catch(err => {
  console.error('HIDE API fetch failed:', err);
  document.getElementById('root').innerHTML = `
    <div style="display:grid;place-items:center;height:100vh;background:#0D1117;color:#F85149;
      font-family:'IBM Plex Mono',monospace;text-align:center;gap:12px;">
      <div>
        <div style="font-size:18px;margin-bottom:8px;">⚠ API connection failed</div>
        <div style="color:#8B949E;font-size:12px;">Make sure Flask is running: python -m observatory.web.api</div>
        <div style="color:#636d78;font-size:11px;margin-top:8px;">${(err && err.message) || err}</div>
        <button onclick="location.reload()"
          style="margin-top:16px;background:#161B22;border:1px solid #30363D;
          color:#E6EDF3;padding:8px 16px;border-radius:6px;cursor:pointer;
          font-family:inherit;">Retry</button>
      </div>
    </div>`;
});
