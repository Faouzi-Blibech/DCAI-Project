// Shared components for HIDE Observatory
const { useState, useEffect, useMemo, useRef } = React;

// ─── Icons (inline SVG, stroke-based) ──────────────────────────────────────
const Icon = ({ d, size=16, fill='none' }) => (
  <svg className="ico" width={size} height={size} viewBox="0 0 24 24" fill={fill}
    stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
    {typeof d === 'string' ? <path d={d}/> : d}
  </svg>
);
const icons = {
  overview:    'M3 12l9-9 9 9M5 10v10h14V10',
  researchers: <g><circle cx="9" cy="8" r="3.2"/><path d="M3 20c.5-3.4 3-5.5 6-5.5s5.5 2.1 6 5.5"/><circle cx="17" cy="7" r="2.2"/><path d="M15 13c2.5 0 4.5 1.6 5 4"/></g>,
  clusters:    <g><circle cx="7" cy="8" r="2.4"/><circle cx="17" cy="7" r="2"/><circle cx="16" cy="17" r="2.8"/><circle cx="6" cy="16" r="1.8"/><path d="M8.8 9l5.6-.5M16 9l-.2 6M14 16.2l-6 0"/></g>,
  collab:      <g><circle cx="6" cy="7" r="2.2"/><circle cx="18" cy="7" r="2.2"/><circle cx="12" cy="18" r="2.4"/><path d="M7.6 8.5l8.8 0M7.2 8.8l3.8 7.2M16.8 8.8l-3.8 7.2"/></g>,
  agents:      <g><rect x="4" y="4" width="7" height="7" rx="1.5"/><rect x="13" y="4" width="7" height="7" rx="1.5"/><rect x="4" y="13" width="7" height="7" rx="1.5"/><rect x="13" y="13" width="7" height="7" rx="1.5"/></g>,
  play:        'M6 4l14 8-14 8V4z',
  refresh:     'M3 12a9 9 0 0115.5-6.2M21 4v5h-5M21 12a9 9 0 01-15.5 6.2M3 20v-5h5',
  filter:      'M4 5h16M7 12h10M10 19h4',
  search:      <g><circle cx="11" cy="11" r="6"/><path d="M20 20l-4.5-4.5"/></g>,
  chevron:     'M9 6l6 6-6 6',
  download:    'M12 4v12m0 0l-5-5m5 5l5-5M4 20h16',
  bell:        <g><path d="M6 16V11a6 6 0 1112 0v5"/><path d="M4 16h16"/><path d="M10 20a2 2 0 004 0"/></g>,
  settings:    <g><circle cx="12" cy="12" r="3"/><path d="M19 12a7 7 0 00-.1-1.2l2.1-1.6-2-3.4-2.4.9a7 7 0 00-2.1-1.2L14 3h-4l-.5 2.5A7 7 0 007.4 6.7L5 5.8l-2 3.4 2.1 1.6A7 7 0 005 12c0 .4 0 .8.1 1.2L3 14.8l2 3.4 2.4-.9a7 7 0 002.1 1.2L10 21h4l.5-2.5a7 7 0 002.1-1.2l2.4.9 2-3.4-2.1-1.6c.1-.4.1-.8.1-1.2z"/></g>,
};

// ─── Brand mark ────────────────────────────────────────────────────────────
const BrandMark = () => (
  <svg viewBox="0 0 32 32" width="28" height="28">
    <defs>
      <radialGradient id="bm-g" cx="50%" cy="50%" r="50%">
        <stop offset="0%" stopColor="#2F81F7" stopOpacity="0.9"/>
        <stop offset="100%" stopColor="#2F81F7" stopOpacity="0"/>
      </radialGradient>
    </defs>
    <circle cx="16" cy="16" r="14" fill="url(#bm-g)" opacity="0.4"/>
    <circle cx="16" cy="16" r="10" fill="none" stroke="#2F81F7" strokeWidth="1.2"/>
    <circle cx="16" cy="16" r="4" fill="none" stroke="#E6EDF3" strokeWidth="1.2"/>
    <circle cx="16" cy="16" r="1.2" fill="#2F81F7"/>
    <path d="M16 2v4M16 26v4M2 16h4M26 16h4" stroke="#30363D" strokeWidth="1"/>
  </svg>
);

// ─── Sparkline ─────────────────────────────────────────────────────────────
const Spark = ({ data, color='#2F81F7', w=64, h=22 }) => {
  const max = Math.max(...data), min = Math.min(...data);
  const pts = data.map((v,i)=>{
    const x = (i/(data.length-1))*w;
    const y = h - ((v-min)/(max-min || 1))*h;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');
  return (
    <svg width={w} height={h}>
      <polyline fill="none" stroke={color} strokeWidth="1.5" points={pts} opacity="0.9"/>
      <polyline fill={color} fillOpacity="0.12" stroke="none"
        points={`0,${h} ${pts} ${w},${h}`}/>
    </svg>
  );
};

// ─── KPI Card ──────────────────────────────────────────────────────────────
const Kpi = ({ label, value, delta, deltaKind='up', tone='', series, dotColor }) => (
  <div className={`card kpi ${tone}`}>
    <div className="rail"/>
    <div className="lbl"><span className="dot"/>{label}</div>
    <div className="val">{value}</div>
    {delta && <div className={`delta ${deltaKind}`}>
      {deltaKind==='up' ? '▲' : deltaKind==='down' ? '▼' : '—'} {delta}
    </div>}
    {series && <div className="spark"><Spark data={series} color={dotColor || '#2F81F7'}/></div>}
  </div>
);

// ─── Bar chart ─────────────────────────────────────────────────────────────
const BarChart = ({ data, maxH=180 }) => {
  const max = Math.max(...data.map(d=>d.n));
  return (
    <div>
      <div className="bar-chart" style={{height:maxH}}>
        {data.map((d,i)=>(
          <div key={i} className="bar" style={{height: `${(d.n/max)*100}%`}}>
            <div className="val">{d.n}</div>
            <div className="lbl">{String(d.year).slice(2)}</div>
          </div>
        ))}
      </div>
      <div style={{height:22}}/>
    </div>
  );
};

// ─── Horizontal bar list ───────────────────────────────────────────────────
const HBarList = ({ items }) => {
  const max = Math.max(...items.map(i=>i.v));
  return (
    <div>
      {items.map((it,i)=>(
        <div key={i} className="hbar-row">
          <div className="name ellipsis">{it.name}</div>
          <div className="hbar"><span style={{width: `${(it.v/max)*100}%`}}/></div>
          <div className="v">{it.v}</div>
        </div>
      ))}
    </div>
  );
};

// ─── Scatter plot (SVG) ────────────────────────────────────────────────────
const Scatter = ({ points, xKey, yKey, xLabel, yLabel, colorKey, sizeKey,
  height=360, onHover, onClick, selectedId }) => {
  const pad = { l: 56, r: 16, t: 16, b: 40 };
  const wrapRef = useRef(null);
  const [w, setW] = useState(800);
  useEffect(()=>{
    if (!wrapRef.current) return;
    const ro = new ResizeObserver(([e])=> setW(e.contentRect.width));
    ro.observe(wrapRef.current);
    return () => ro.disconnect();
  },[]);
  const h = height;
  const xs = points.map(p => p[xKey]), ys = points.map(p => p[yKey]);
  const xMax = Math.max(...xs)*1.05, yMax = Math.max(...ys)*1.1;
  const sMin = Math.min(...points.map(p=>p[sizeKey]||1));
  const sMax = Math.max(...points.map(p=>p[sizeKey]||1));
  const rFor = v => 4 + ((v - sMin)/(sMax - sMin || 1)) * 10;
  const X = v => pad.l + (v / xMax) * (w - pad.l - pad.r);
  const Y = v => h - pad.b - (v / yMax) * (h - pad.t - pad.b);

  const xTicks = [0, 0.25, 0.5, 0.75, 1].map(t => +(t*xMax).toFixed(0));
  const yTicks = [0, 0.25, 0.5, 0.75, 1].map(t => +(t*yMax).toFixed(0));

  return (
    <div className="chart-wrap" ref={wrapRef}>
      <svg viewBox={`0 0 ${w} ${h}`} style={{height:h}}>
        {/* grid */}
        {yTicks.map((t,i)=>(
          <g key={'y'+i}>
            <line x1={pad.l} x2={w-pad.r} y1={Y(t)} y2={Y(t)} stroke="#232a33" strokeDasharray="2 4"/>
            <text x={pad.l-10} y={Y(t)+4} fill="#8B949E" fontSize="10" textAnchor="end" fontFamily="IBM Plex Mono">{t.toLocaleString()}</text>
          </g>
        ))}
        {xTicks.map((t,i)=>(
          <g key={'x'+i}>
            <text x={X(t)} y={h-pad.b+16} fill="#8B949E" fontSize="10" textAnchor="middle" fontFamily="IBM Plex Mono">{t}</text>
          </g>
        ))}
        {/* axes */}
        <line x1={pad.l} x2={pad.l} y1={pad.t} y2={h-pad.b} stroke="#30363D"/>
        <line x1={pad.l} x2={w-pad.r} y1={h-pad.b} y2={h-pad.b} stroke="#30363D"/>
        <text x={pad.l} y={pad.t-4} fill="#8B949E" fontSize="10" fontFamily="IBM Plex Mono">{yLabel}</text>
        <text x={w-pad.r} y={h-8} fill="#8B949E" fontSize="10" textAnchor="end" fontFamily="IBM Plex Mono">{xLabel}</text>
        {/* points */}
        {points.map(p=>{
          const isSel = p.id === selectedId;
          return (
            <g key={p.id}
               onMouseEnter={()=>onHover && onHover(p)}
               onClick={()=>onClick && onClick(p)}
               style={{cursor:'default'}}>
              <circle cx={X(p[xKey])} cy={Y(p[yKey])} r={rFor(p[sizeKey]||1) + (isSel?3:0)}
                fill={p[colorKey]} fillOpacity={isSel?0.95:0.72}
                stroke={isSel ? '#fff' : p[colorKey]}
                strokeWidth={isSel ? 1.5 : 0.5}
                strokeOpacity={isSel ? 1 : 0.6}/>
            </g>
          );
        })}
      </svg>
    </div>
  );
};

// ─── Heatmap ───────────────────────────────────────────────────────────────
const Heatmap = ({ rows, cols, values, colorScale }) => {
  const colWidth = `minmax(24px, 1fr)`;
  return (
    <div>
      <div className="hm-col-labels" style={{gridTemplateColumns:`repeat(${cols.length}, ${colWidth})`}}>
        {cols.map((c,i)=>(<span key={i}>{c}</span>))}
      </div>
      <div className="heatmap">
        {rows.map((r,ri)=>(
          <div key={ri} className="hm-row"
               style={{gridTemplateColumns:`100px repeat(${cols.length}, ${colWidth})`}}>
            <div className="lbl">{r}</div>
            {cols.map((c,ci)=>{
              const v = values[ri][ci];
              const a = Math.min(1, v);
              const bg = `rgba(47, 129, 247, ${0.08 + a*0.82})`;
              return <div key={ci} className="hm-cell" data-v={`${r} × ${c}: ${Math.round(v*100)}%`} style={{background:bg}}/>;
            })}
          </div>
        ))}
      </div>
    </div>
  );
};

// ─── Status badge ──────────────────────────────────────────────────────────
const Badge = ({ kind='blue', children }) => <span className={`tag ${kind}`}>{children}</span>;

// ─── Modal ─────────────────────────────────────────────────────────────────
function Modal({ title, onClose, children }) {
  return (
    <div onClick={onClose}
      style={{position:'fixed',inset:0,background:'rgba(8,11,16,.7)',
        backdropFilter:'blur(4px)',display:'grid',placeItems:'center',zIndex:50}}>
      <div onClick={e=>e.stopPropagation()}
        style={{background:'var(--surface)',border:'1px solid var(--border)',
          borderRadius:8,minWidth:380,maxWidth:560,maxHeight:'80vh',overflow:'auto',
          padding:18,boxShadow:'0 20px 60px rgba(0,0,0,.5)'}}>
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',
          marginBottom:12,borderBottom:'1px solid var(--border-soft)',paddingBottom:10}}>
          <div style={{fontWeight:600,fontSize:14}}>{title}</div>
          <button onClick={onClose}
            style={{background:'transparent',border:0,color:'var(--muted)',
              cursor:'pointer',fontSize:18,lineHeight:1}}>✕</button>
        </div>
        {children}
      </div>
    </div>
  );
}

// ─── Utils ─────────────────────────────────────────────────────────────────
function truncate(s, n=60){ return s.length > n ? s.slice(0,n-1)+'…' : s; }
function fmt(n){ return (n||0).toLocaleString(); }

// Export
Object.assign(window, {
  Icon, icons, BrandMark, Spark, Kpi, BarChart, HBarList, Scatter, Heatmap, Badge, Modal,
  truncate, fmt,
});
