// App shell — sidebar, topbar, page routing, tweaks.

const { useState: useStateA, useEffect: useEffectA } = React;

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "accent": "#2F81F7",
  "density": "regular",
  "network": "force",
  "showLog": true
}/*EDITMODE-END*/;

const PAGES = [
  { id: 'overview',    label: 'Overview',       kbd:'1', icon: icons.overview },
  { id: 'researchers', label: 'Researchers',    kbd:'2', icon: icons.researchers },
  { id: 'clusters',    label: 'Clusters',       kbd:'3', icon: icons.clusters },
  { id: 'collabs',     label: 'Collaborations', kbd:'4', icon: icons.collab },
  { id: 'agents',      label: 'Agents',         kbd:'5', icon: icons.agents },
];

function Ticker(){
  const [t, setT] = useStateA(new Date());
  useEffectA(()=>{
    const id = setInterval(()=>setT(new Date()), 1000);
    return () => clearInterval(id);
  },[]);
  const p = n => String(n).padStart(2,'0');
  return `${p(t.getUTCHours())}:${p(t.getUTCMinutes())}:${p(t.getUTCSeconds())} UTC`;
}

function App(){
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [page, setPage] = useStateA('overview');
  const [running, setRunning] = useStateA(false);
  const [data, setData] = useStateA(window.HIDE_DATA || null);

  // ALL hooks run unconditionally before any early return — Rules of Hooks.
  useEffectA(() => {
    if (window.HIDE_DATA) { setData(window.HIDE_DATA); return; }
    const onReady = () => setData(window.HIDE_DATA);
    window.addEventListener('hide-data-ready', onReady);
    return () => window.removeEventListener('hide-data-ready', onReady);
  }, []);

  // Apply accent + density to :root
  useEffectA(()=>{
    document.documentElement.style.setProperty('--accent', t.accent);
    document.body.classList.toggle('compact', t.density==='compact');
    document.body.classList.toggle('comfy',   t.density==='comfy');
  },[t.accent, t.density]);

  // Keyboard shortcuts
  useEffectA(()=>{
    const onKey = e=>{
      if (e.target.tagName === 'INPUT' || e.target.tagName==='SELECT') return;
      const hit = PAGES.find(p=>p.kbd===e.key);
      if (hit) setPage(hit.id);
    };
    window.addEventListener('keydown', onKey);
    return ()=>window.removeEventListener('keydown', onKey);
  },[]);

  // Now safe to conditionally render — no hooks below this point.
  if (!data) return (
    <div style={{display:'grid',placeItems:'center',height:'100vh',
      background:'#0D1117',color:'#8B949E',
      fontFamily:"'IBM Plex Mono',monospace",fontSize:13}}>
      <div style={{textAlign:'center'}}>
        <svg width="32" height="32" viewBox="0 0 32 32"
          style={{marginBottom:12,animation:'spin 1s linear infinite'}}>
          <circle cx="16" cy="16" r="12" fill="none" stroke="#2F81F7"
            strokeWidth="2" strokeDasharray="40 20"/>
        </svg>
        <div>Loading HIDE Observatory…</div>
        <div style={{color:'#636d78',fontSize:11,marginTop:6}}>Connecting to backend</div>
      </div>
    </div>
  );

  const runCycle = async () => {
    setRunning(true);
    try {
      const res = await fetch('/api/run', { method: 'POST' });
      const json = await res.json();
      if (!json.ok) console.error('Cycle error:', json.message);
      if (typeof window._hideRefresh === 'function') {
        await window._hideRefresh();
        setData({ ...window.HIDE_DATA });
      }
    } catch (e) {
      console.error('Run cycle failed:', e);
    } finally {
      setRunning(false);
    }
  };

  const cur = PAGES.find(p=>p.id===page);

  return (
    <div className="app">
      {/* ═══ Sidebar ═══ */}
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><BrandMark/></div>
          <div>
            <div className="brand-name">HIDE Observatory</div>
            <div className="brand-sub">v2.4 · Cycle 248</div>
          </div>
        </div>

        <nav className="nav">
          <div className="nav-section">Navigation</div>
          {PAGES.map(p=>(
            <div key={p.id} className={`nav-item ${p.id===page?'active':''}`}
                 onClick={()=>setPage(p.id)}>
              <Icon d={p.icon} size={15}/>
              <span>{p.label}</span>
              <span className="kbd">{p.kbd}</span>
            </div>
          ))}

          <div className="nav-section">System</div>
          <div className="nav-item"><Icon d={icons.bell} size={15}/><span>Alerts</span><span className="kbd" style={{background:'rgba(248,81,73,.1)',color:'#ff7b72',borderColor:'#4a1d1d'}}>2</span></div>
          <div className="nav-item"><Icon d={icons.settings} size={15}/><span>Settings</span></div>
        </nav>

        <div className="sidebar-foot">
          <button className={`run-btn ${running?'running':''}`} onClick={runCycle} disabled={running}>
            {running ? <>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                strokeWidth="2" style={{animation:'spin 1s linear infinite'}}>
                <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
              </svg>
              Running cycle…
            </> : <>
              <Icon d={icons.play} size={12}/> Run MAS Cycle
            </>}
          </button>
          <div className="sync"><span className="dot"/><b>Last sync</b> <span style={{color:'var(--muted-2)'}}>12s ago</span></div>
        </div>
      </aside>

      {/* ═══ Main ═══ */}
      <main className="main">
        <div className="topbar">
          <div className="crumbs">
            <span>OBSERVATORY</span><span className="sep">/</span>
            <span className="cur">{cur.label.toUpperCase()}</span>
          </div>
          <div className="top-right">
            <span className="stat-pill"><span className="d"/>7 of 8 agents healthy</span>
            <span className="ticker"><Ticker/></span>
            <div className="avatar">AK</div>
          </div>
        </div>

        <div className="content">
          {page==='overview'    && <PageOverview data={data}/>}
          {page==='researchers' && <PageResearchers data={data}/>}
          {page==='clusters'    && <PageClusters data={data}/>}
          {page==='collabs'     && <PageCollabs data={data} networkStyle={t.network}/>}
          {page==='agents'      && <PageAgents data={data} showLog={t.showLog}/>}
        </div>
      </main>

      <TweaksPanel>
        <TweakSection label="Theme"/>
        <TweakColor label="Accent" value={t.accent} onChange={v=>setTweak('accent',v)}/>
        <TweakRadio label="Density" value={t.density}
          options={['compact','regular','comfy']}
          onChange={v=>setTweak('density',v)}/>
        <TweakSection label="Collaborations"/>
        <TweakRadio label="Network layout" value={t.network}
          options={['force','arc']}
          onChange={v=>setTweak('network',v)}/>
        <TweakSection label="Agents"/>
        <TweakToggle label="Show live log" value={t.showLog}
          onChange={v=>setTweak('showLog',v)}/>
      </TweaksPanel>
    </div>
  );
}

const style = document.createElement('style');
style.textContent = '@keyframes spin{to{transform:rotate(360deg)}}';
document.head.appendChild(style);

ReactDOM.createRoot(document.getElementById('root')).render(<App/>);
