// All 5 pages.
const { useState: useStateP, useMemo: useMemoP, useEffect: useEffectP, useRef: useRefP } = React;

// ═══ PAGE 1 — OVERVIEW ═════════════════════════════════════════════════════
function PageOverview({ data }) {
  const topLabs = useMemoP(()=>{
    if (data._top_labs && data._top_labs.length) return data._top_labs;
    const counts = {};
    data.RESEARCHERS.forEach(r => counts[r.lab.name] = (counts[r.lab.name]||0)+1);
    return Object.entries(counts).map(([name,v])=>({name, v}))
      .sort((a,b)=>b.v-a.v).slice(0,10);
  },[data]);

  const recent = data.PUBLICATIONS.slice(0,12);
  const avgH = (data._stats ? data._stats.avg_h_index :
    (data.RESEARCHERS.reduce((s,r)=>s+r.h_index,0)/Math.max(data.RESEARCHERS.length,1))
  ).toFixed(1);

  return (
    <>
      <div className="ph">
        <div>
          <h1>Overview</h1>
          <div className="sub">System health · cycle #248 · 2026-04-23 03:41 UTC</div>
        </div>
        <div className="ph-actions">
          <button className="btn" onClick={()=>window._hideRefresh && window._hideRefresh()}>
            <Icon d={icons.refresh} size={13}/> Refresh
          </button>
          <a className="btn" href="/api/researchers/export.csv" download>
            <Icon d={icons.download} size={13}/> Export
          </a>
        </div>
      </div>

      <div className="grid" style={{gridTemplateColumns:'repeat(5,1fr)', marginBottom:16}}>
        <Kpi label="Researchers" tone=""  value={fmt(data._stats?.researchers_count  ?? data.RESEARCHERS.length)} delta="+8 this cycle"  series={[140,145,150,155,160,165,168, data._stats?.researchers_count ?? data.RESEARCHERS.length]}/>
        <Kpi label="Labs"        tone="g" value={data._stats?.labs_count            ?? data.LABS.length}        delta="stable"        deltaKind="flat" dotColor="#3FB950" series={[10,10,10,10,10,10,10, data._stats?.labs_count ?? data.LABS.length]}/>
        <Kpi label="Publications"tone=""  value={fmt(data._stats?.publications_count ?? data.PUBLICATIONS.length)} delta="ingested"   series={[1540,1590,1640,1700,1760,1810,1830, data._stats?.publications_count ?? data.PUBLICATIONS.length]}/>
        <Kpi label="Avg h-index" tone="a" value={avgH} delta="median" deltaKind="flat" dotColor="#D29922" series={[11.2,11.4,11.3,11.6,11.8,12.0,12.1, +avgH]}/>
        <Kpi label="Active clusters" tone="p" value={data._stats?.clusters_count    ?? data.CLUSTERS.length}    delta="current run"   deltaKind="flat" dotColor="#8957E5" series={[4,4,5,5,5,6,6, data._stats?.clusters_count ?? data.CLUSTERS.length]}/>
      </div>

      <div className="grid" style={{gridTemplateColumns:'1.35fr 1fr', marginBottom:16}}>
        <div className="card">
          <h3>Publications over time <span className="meta">2010 – 2024 · bars</span></h3>
          <BarChart data={data.PUBS_PER_YEAR}/>
          <div className="legend" style={{marginTop:8}}>
            <div><span className="d" style={{background:'#2F81F7'}}/>Published</div>
            <div>Total: {fmt(data.PUBS_PER_YEAR.reduce((s,d)=>s+d.n,0))}</div>
            <div>Peak year: 2023 ({Math.max(...data.PUBS_PER_YEAR.map(d=>d.n))})</div>
          </div>
        </div>
        <div className="card">
          <h3>Top 10 labs by headcount <span className="meta">researchers</span></h3>
          <HBarList items={topLabs}/>
        </div>
      </div>

      <div className="card pad-0">
        <div style={{padding:'14px 16px', borderBottom:'1px solid var(--border)', display:'flex',
          alignItems:'center', justifyContent:'space-between'}}>
          <h3 style={{margin:0}}>Recent activity <span className="meta">20 latest publications</span></h3>
          <div style={{display:'flex',gap:8}}>
            <button className="btn"
              onClick={()=>window.dispatchEvent(new CustomEvent('hide-nav', {detail:'researchers'}))}>
              <Icon d={icons.filter} size={13}/> Filter
            </button>
            <button className="btn"
              onClick={()=>window.dispatchEvent(new CustomEvent('hide-nav', {detail:'researchers'}))}>
              View all →
            </button>
          </div>
        </div>
        <table className="t">
          <thead><tr>
            <th style={{width:'48%'}}>Title</th><th>Venue</th><th>Year</th>
            <th className="num">Citations</th><th>Authors</th>
          </tr></thead>
          <tbody>
            {recent.map(p=>(
              <tr key={p.id}>
                <td className="name">{truncate(p.title, 72)}</td>
                <td><Badge kind="blue">{p.venue}</Badge></td>
                <td><span style={{fontFamily:'IBM Plex Mono',color:'var(--muted)'}}>{p.year}</span></td>
                <td className="num">{fmt(p.citations)}</td>
                <td style={{color:'var(--muted)', fontSize:11}}>{p.authors.slice(0,2).join(', ')}{p.authors.length>2?` +${p.authors.length-2}`:''}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

// ═══ PAGE 2 — RESEARCHERS ══════════════════════════════════════════════════
function PageResearchers({ data }) {
  const [lab, setLab] = useStateP('All');
  const [cluster, setCluster] = useStateP('All');
  const [exp, setExp] = useStateP('All');
  const [minH, setMinH] = useStateP(0);
  const [selId, setSelId] = useStateP(data.RESEARCHERS[3]?.id || data.RESEARCHERS[0]?.id);
  const [query, setQuery] = useStateP('');
  const [page, setPage] = useStateP(1);
  const PAGE_SIZE = 20;

  const filtered = useMemoP(()=>data.RESEARCHERS.filter(r =>
    (lab==='All' || r.lab.name===lab) &&
    (cluster==='All' || r.cluster.name===cluster) &&
    (exp==='All' || r.areas.some(a=>a.name===exp)) &&
    r.h_index >= minH &&
    (!query || r.name.toLowerCase().includes(query.toLowerCase()))
  ), [lab, cluster, exp, minH, query, data]);

  useEffectP(()=>{ setPage(1); }, [lab, cluster, exp, minH, query]);
  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const pageRows = filtered.slice((page-1)*PAGE_SIZE, page*PAGE_SIZE);

  const scatterPoints = filtered.map(r => ({
    id:r.id, h_index:r.h_index, citations:r.citations,
    publications:r.publications, color:r.cluster.color,
    name:r.name, lab:r.lab.name, cluster:r.cluster.name
  }));

  const selected = data.RESEARCHERS.find(r=>r.id===selId);

  return (
    <>
      <div className="ph">
        <div>
          <h1>Researchers</h1>
          <div className="sub">{filtered.length} of {data.RESEARCHERS.length} researchers · filtered</div>
        </div>
        <div className="ph-actions">
          <a className="btn" href="/api/researchers/export.csv" download>
            <Icon d={icons.download} size={13}/> Export CSV
          </a>
        </div>
      </div>

      <div className="filters">
        <div className="field"><label>Lab</label>
          <select value={lab} onChange={e=>setLab(e.target.value)}>
            <option>All</option>{data.LABS.map(l=><option key={l.id}>{l.name}</option>)}
          </select>
        </div>
        <div className="field"><label>Cluster</label>
          <select value={cluster} onChange={e=>setCluster(e.target.value)}>
            <option>All</option>{data.CLUSTERS.map(c=><option key={c.id}>{c.name}</option>)}
          </select>
        </div>
        <div className="field"><label>Expertise area</label>
          <select value={exp} onChange={e=>setExp(e.target.value)}>
            <option>All</option>{data.EXPERTISE.map(e=><option key={e}>{e}</option>)}
          </select>
        </div>
        <div className="field"><label>Min h-index <span style={{color:'var(--muted-2)',fontFamily:'var(--mono)'}}>≥ {minH}</span></label>
          <div className="slider">
            <input type="range" min="0" max="50" value={minH} onChange={e=>setMinH(+e.target.value)}/>
            <div className="v">{minH}</div>
          </div>
        </div>
      </div>

      <div className="grid" style={{gridTemplateColumns:'2fr 1fr', gap:16, alignItems:'start'}}>
        <div>
          <div className="card">
            <h3>Researcher landscape <span className="meta">h-index × citations · colored by cluster</span></h3>
            <Scatter points={scatterPoints} xKey="h_index" yKey="citations"
              sizeKey="publications" colorKey="color"
              xLabel="h-index →" yLabel="↑ citations"
              selectedId={selId}
              onClick={p=>setSelId(p.id)} height={340}/>
            <div className="legend" style={{marginTop:6}}>
              {data.CLUSTERS.map(c=>(
                <div key={c.id}><span className="d" style={{background:c.color}}/>{c.name}</div>
              ))}
            </div>
          </div>

          <div className="card pad-0" style={{marginTop:16}}>
            <div style={{padding:'12px 16px',borderBottom:'1px solid var(--border)',
              display:'flex',alignItems:'center',justifyContent:'space-between'}}>
              <h3 style={{margin:0}}>All researchers <span className="meta">{filtered.length} rows · click to inspect</span></h3>
              <div style={{display:'flex',gap:8,alignItems:'center'}}>
                <Icon d={icons.search} size={13}/>
                <input type="text" placeholder="Search by name…"
                  value={query} onChange={e=>setQuery(e.target.value)}
                  style={{background:'var(--surface)',border:'1px solid var(--border)',
                    borderRadius:6,color:'var(--text)',padding:'5px 9px',
                    fontSize:12,fontFamily:'var(--sans)',width:200}}/>
              </div>
            </div>
            <div style={{maxHeight:340, overflow:'auto'}}>
              <table className="t">
                <thead><tr>
                  <th>Name</th><th>Lab</th><th className="num">h-idx</th>
                  <th className="num">Citations</th><th className="num">Pubs</th>
                  <th>Cluster</th><th>Top expertise</th>
                </tr></thead>
                <tbody>
                  {pageRows.map(r=>(
                    <tr key={r.id} className={r.id===selId?'sel':''} onClick={()=>setSelId(r.id)}>
                      <td className="name">{r.name}</td>
                      <td style={{color:'var(--muted)'}}>{r.lab.name}</td>
                      <td className="num">{r.h_index}</td>
                      <td className="num">{fmt(r.citations)}</td>
                      <td className="num">{r.publications}</td>
                      <td><span className="tag" style={{color:r.cluster.color, borderColor:r.cluster.color+'55', background:r.cluster.color+'14'}}>{r.cluster.name}</span></td>
                      <td style={{color:'var(--muted)',fontSize:11}}>{r.areas[0]?.name || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="pager">
              <div>Showing {filtered.length===0?0:((page-1)*PAGE_SIZE+1)}–{Math.min(page*PAGE_SIZE, filtered.length)} of {filtered.length}</div>
              <div className="pg">
                <button onClick={()=>setPage(p=>Math.max(1,p-1))} disabled={page===1}>‹</button>
                {Array.from({length: totalPages}, (_,i)=>i+1)
                  .filter(n => n===1 || n===totalPages || Math.abs(n-page)<=1)
                  .map((n,i,arr)=>{
                    const prev = arr[i-1];
                    const gap = prev !== undefined && n - prev > 1;
                    return (
                      <React.Fragment key={n}>
                        {gap && <button disabled>…</button>}
                        <button className={n===page?'on':''} onClick={()=>setPage(n)}>{n}</button>
                      </React.Fragment>
                    );
                  })}
                <button onClick={()=>setPage(p=>Math.min(totalPages,p+1))} disabled={page===totalPages}>›</button>
              </div>
            </div>
          </div>
        </div>

        {selected && (
          <div className="profile">
            <div className="profile-hd">
              <div className="av">{selected.initials}</div>
              <div>
                <div className="nm">{selected.name}</div>
                <div className="mt">{selected.id} · {selected.lab.name} · joined {selected.joined}</div>
              </div>
            </div>
            <div className="profile-stats">
              <div><div className="k">h-index</div><div className="v">{selected.h_index}</div></div>
              <div><div className="k">Citations</div><div className="v">{fmt(selected.citations)}</div></div>
              <div><div className="k">Publications</div><div className="v">{selected.publications}</div></div>
            </div>

            <div>
              <div style={{fontFamily:'var(--mono)',fontSize:10,letterSpacing:'.1em',
                textTransform:'uppercase',color:'var(--muted)',marginBottom:8}}>
                Expertise · TF-IDF score
              </div>
              {selected.areas.map((a,i)=>(
                <div key={i} className="expertise-bar">
                  <div className="nm">{a.name}</div>
                  <div className="bar2"><span style={{width:`${a.score*100}%`}}/></div>
                  <div className="sc">{a.score.toFixed(2)}</div>
                </div>
              ))}
            </div>

            <div>
              <div style={{fontFamily:'var(--mono)',fontSize:10,letterSpacing:'.1em',
                textTransform:'uppercase',color:'var(--muted)',marginBottom:8}}>
                Top publications
              </div>
              {data.PUBLICATIONS.slice(6,11).map((p,i)=>(
                <div key={i} style={{display:'flex',justifyContent:'space-between',gap:10,padding:'6px 0',
                  borderBottom:'1px solid var(--border-soft)',fontSize:11}}>
                  <div className="ellipsis" style={{flex:1}}>{truncate(p.title,50)}</div>
                  <div style={{color:'var(--muted)',fontFamily:'var(--mono)'}}>{p.year}</div>
                  <div style={{color:'#79b8ff',fontFamily:'var(--mono)',width:44,textAlign:'right'}}>{fmt(p.citations)}</div>
                </div>
              ))}
            </div>

            <div>
              <div style={{fontFamily:'var(--mono)',fontSize:10,letterSpacing:'.1em',
                textTransform:'uppercase',color:'var(--muted)',marginBottom:8}}>
                Collaboration recs
              </div>
              {data.COLLABS.filter(c=>c.a.id===selected.id||c.b.id===selected.id).slice(0,3).map((c,i)=>{
                const other = c.a.id===selected.id ? c.b : c.a;
                return (
                  <div key={i} style={{display:'flex',alignItems:'center',gap:8,padding:'6px 0',fontSize:11,
                    borderBottom:'1px solid var(--border-soft)'}}>
                    <div style={{flex:1}}>
                      <div>{other.name}</div>
                      <div style={{color:'var(--muted-2)',fontSize:10,fontFamily:'var(--mono)'}}>{other.lab.name}</div>
                    </div>
                    <div style={{color:'#79b8ff',fontFamily:'var(--mono)',fontSize:11}}>n={c.nash.toFixed(2)}</div>
                    <Badge kind={c.status==='accepted'?'green':c.status==='pending'?'amber':'red'}>{c.status}</Badge>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </>
  );
}

// ═══ PAGE 3 — CLUSTERS ═════════════════════════════════════════════════════
function PageClusters({ data }) {
  // Fake PCA: spread each researcher roughly by cluster centroid + jitter.
  // Build centroids dynamically so any number of clusters works (after reseed
  // the cluster count can be 6, 10, etc.).
  const seed = (n)=>{let x=Math.sin(n)*10000;return x-Math.floor(x);};
  const centroids = useMemoP(()=>{
    const map = {};
    const ids = data.CLUSTERS.map(c=>c.id);
    ids.forEach((id, i) => {
      const ang = (i / Math.max(ids.length,1)) * Math.PI * 2;
      const r = 3.2;
      map[id] = [Math.cos(ang)*r, Math.sin(ang)*r];
    });
    return map;
  }, [data.CLUSTERS]);

  const pcaPoints = data.RESEARCHERS.map((r,i)=>{
    const c = centroids[r.cluster.id] || [0, 0];
    return { id:r.id, px: c[0] + (seed(i+1)-0.5)*2.4,
             py: c[1] + (seed(i*3+7)-0.5)*2.4, color: r.cluster.color,
             name: r.name, lab: r.lab.name };
  });

  // Heatmap: cluster × expertise
  const rows = data.CLUSTERS.map(c=>c.name);
  const cols = data.EXPERTISE.slice(0,12);
  const values = data.CLUSTERS.map((c, ci)=>
    cols.map((_, ei) => {
      const v = Math.abs(Math.sin((ci+1)*(ei+3)*1.17)) * 0.95;
      return v;
    })
  );

  return (
    <>
      <div className="ph">
        <div>
          <h1>Clusters</h1>
          <div className="sub">HDBSCAN + KMeans · avg silhouette 0.452 · last run 03m ago</div>
        </div>
        <div className="ph-actions">
          <button className="btn" onClick={()=>window._hideRefresh && window._hideRefresh()}>
            <Icon d={icons.refresh} size={13}/> Refresh
          </button>
          <button className="btn primary" onClick={()=>window._hideAction('/recluster')}>
            <Icon d={icons.refresh} size={13}/> Re-cluster
          </button>
        </div>
      </div>

      <div className="cluster-grid" style={{marginBottom:16}}>
        {data.CLUSTERS.map(c=>{
          const silCls = c.silhouette > 0.5 ? 'sil-g' : c.silhouette > 0.3 ? 'sil-a' : 'sil-r';
          const idNum = parseInt(c.id.replace(/\D/g,''),10) || 0;
          const top = (c.top_areas && c.top_areas.length)
            ? c.top_areas.slice(0,3)
            : data.EXPERTISE.slice((idNum*3)%Math.max(data.EXPERTISE.length-3,1),
                                   (idNum*3)%Math.max(data.EXPERTISE.length-3,1)+3);
          return (
            <div key={c.id} className="cluster-card">
              <div className={`c-sil ${silCls}`}>σ {c.silhouette.toFixed(2)}</div>
              <div className="c-name"><span className="c-swatch" style={{background:c.color}}/>{c.name}</div>
              <div className="c-size">{c.size} researchers · {c.alg}</div>
              <div className="c-top">
                {top.map(t=><Badge key={t} kind="blue">{t}</Badge>)}
              </div>
            </div>
          );
        })}
      </div>

      <div className="grid" style={{gridTemplateColumns:'1.4fr 1fr', marginBottom:16}}>
        <div className="card">
          <h3>Researcher clusters <span className="meta">2D PCA projection · {data.RESEARCHERS.length} points</span></h3>
          <div style={{position:'relative'}}>
            <Scatter points={pcaPoints.map(p=>({...p,h_index:p.px+6,citations:p.py+6,publications:4}))}
              xKey="h_index" yKey="citations" colorKey="color" sizeKey="publications"
              xLabel="PC1" yLabel="PC2" height={360}/>
          </div>
          <div className="legend" style={{marginTop:6}}>
            {data.CLUSTERS.map(c=>(
              <div key={c.id}><span className="d" style={{background:c.color}}/>{c.name} ({c.size})</div>
            ))}
          </div>
        </div>

        <div className="card pad-0">
          <div style={{padding:'14px 16px', borderBottom:'1px solid var(--border)'}}>
            <h3 style={{margin:0}}>Cluster comparison <span className="meta">ranked by silhouette</span></h3>
          </div>
          <table className="t">
            <thead><tr>
              <th>Cluster</th><th>Alg</th><th className="num">Size</th>
              <th className="num">h-avg</th><th className="num">Cite-avg</th><th className="num">σ</th>
            </tr></thead>
            <tbody>
              {[...data.CLUSTERS].sort((a,b)=>b.silhouette-a.silhouette).map((c,i)=>(
                <tr key={c.id} style={i===0?{background:'rgba(63,185,80,.05)'}:{}}>
                  <td><span className="c-swatch" style={{background:c.color,display:'inline-block',marginRight:6}}/>{c.name}</td>
                  <td style={{color:'var(--muted)',fontSize:11}}>{c.alg}</td>
                  <td className="num">{c.size}</td>
                  <td className="num">{(8 + (c.silhouette*20)).toFixed(1)}</td>
                  <td className="num">{fmt(Math.round(1200 + c.silhouette*4200))}</td>
                  <td className="num" style={{color: c.silhouette>0.5?'#6fda7e':c.silhouette>0.3?'#e3b341':'#ff7b72'}}>
                    {c.silhouette.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card">
        <h3>Expertise distribution across clusters <span className="meta">% of members in cluster with area</span></h3>
        <Heatmap rows={rows} cols={cols} values={values}/>
      </div>
    </>
  );
}

// ═══ PAGE 4 — COLLABORATIONS ═══════════════════════════════════════════════
function PageCollabs({ data, networkStyle }) {
  const [filter, setFilter] = useStateP('All');
  const [pairIdx, setPairIdx] = useStateP(0);

  if (!data.COLLABS || data.COLLABS.length === 0) {
    return (
      <>
        <div className="ph">
          <div>
            <h1>Collaborations</h1>
            <div className="sub">No collaborations yet · run a MAS cycle to populate</div>
          </div>
        </div>
        <div className="card" style={{textAlign:'center',padding:40,color:'var(--muted)'}}>
          <div style={{fontSize:14,marginBottom:8}}>No collaboration data</div>
          <div style={{fontSize:12}}>Click <b>Run MAS Cycle</b> in the sidebar to generate recommendations.</div>
        </div>
      </>
    );
  }

  const top = data.COLLABS.slice(0,50);
  const nodesMap = new Map();
  top.forEach(c=>{
    if (!nodesMap.has(c.a.id)) nodesMap.set(c.a.id, c.a);
    if (!nodesMap.has(c.b.id)) nodesMap.set(c.b.id, c.b);
  });
  const nodes = [...nodesMap.values()];

  // layout positions on demand
  const layout = useMemoP(()=>{
    if (networkStyle === 'arc') {
      return nodes.map((n,i)=>({...n, x: 40 + (i/(nodes.length-1))*(720), y: 280}));
    }
    // Force-ish seeded layout (stable)
    const W=760, H=420;
    return nodes.map((n,i)=>{
      const ang = (i / nodes.length) * Math.PI * 2 + (n.cluster.id.charCodeAt(1)*0.5);
      const r = 120 + (i%4)*40 + (n.h_index%30)*2;
      return {...n, x: W/2 + Math.cos(ang)*r, y: H/2 + Math.sin(ang)*r*0.85};
    });
  },[networkStyle, nodes.length]);

  const posById = Object.fromEntries(layout.map(n=>[n.id,n]));

  const filtered = data.COLLABS.filter(c => filter==='All' || c.status===filter.toLowerCase());
  const sel = top[pairIdx] || top[0];

  // Accept = both cooperate. Construct game theory payoffs
  const payoff = {
    CC: [sel.ua, sel.ub],
    CD: [sel.ua*0.3, sel.ub*1.1],
    DC: [sel.ua*1.1, sel.ub*0.3],
    DD: [sel.ua*0.4, sel.ub*0.4],
  };

  const totalAccepted = data.COLLABS.filter(c=>c.status==='accepted').length;
  const totalPending  = data.COLLABS.filter(c=>c.status==='pending').length;
  const avgNash = (data.COLLABS.reduce((s,c)=>s+c.nash,0)/data.COLLABS.length);

  return (
    <>
      <div className="ph">
        <div>
          <h1>Collaborations</h1>
          <div className="sub">AgentCollabAdvisor · AgentNegotiator · Nash equilibrium acceptance</div>
        </div>
        <div className="ph-actions">
          <button className="btn" onClick={()=>window._hideAction('/recommendations')}>
            <Icon d={icons.refresh} size={13}/> Re-evaluate
          </button>
          <button className="btn primary"
            onClick={()=>window._hideAction('/collaborations/accept_pending',
              { confirm: 'Accept ALL pending collaborations?' })}>
            Accept all pending
          </button>
        </div>
      </div>

      <div className="grid" style={{gridTemplateColumns:'repeat(4,1fr)', marginBottom:16}}>
        <Kpi label="Pairs evaluated" value={fmt(data.COLLABS.length)} delta="+12" series={[92,98,104,108,112,118,120]}/>
        <Kpi label="Accepted" tone="g" value={totalAccepted} delta={`${Math.round(totalAccepted/data.COLLABS.length*100)}%`} dotColor="#3FB950" series={[20,26,30,34,38,41,totalAccepted]}/>
        <Kpi label="Pending"  tone="a" value={totalPending}  delta="awaiting review" deltaKind="flat" dotColor="#D29922" series={[70,68,66,64,62,61,totalPending]}/>
        <Kpi label="Avg Nash value" value={avgNash.toFixed(3)} delta="+0.02" series={[0.31,0.33,0.34,0.36,0.37,0.38,avgNash]}/>
      </div>

      <div className="card" style={{marginBottom:16}}>
        <h3>Collaboration network <span className="meta">top 50 pairs · nodes = researchers · edges = similarity</span></h3>
        <svg viewBox="0 0 760 420" style={{width:'100%',height:420,background:'#0d1218',borderRadius:6}}>
          <defs>
            <radialGradient id="node-glow">
              <stop offset="0%" stopColor="#fff" stopOpacity="0.3"/>
              <stop offset="100%" stopColor="#fff" stopOpacity="0"/>
            </radialGradient>
          </defs>
          {top.map((e,i)=>{
            const a=posById[e.a.id], b=posById[e.b.id];
            if (!a||!b) return null;
            const color = e.status==='accepted'?'#3FB950':e.status==='pending'?'#D29922':'#F85149';
            return <line key={i} x1={a.x} y1={a.y} x2={b.x} y2={b.y}
              stroke={color} strokeOpacity={0.15 + e.sim*0.5} strokeWidth={0.6 + e.sim*2.2}/>;
          })}
          {layout.map(n=>(
            <g key={n.id}>
              <circle cx={n.x} cy={n.y} r={4 + n.h_index*0.35 + 6} fill="url(#node-glow)"/>
              <circle cx={n.x} cy={n.y} r={3 + n.h_index*0.28} fill={n.cluster.color}
                stroke="#0d1218" strokeWidth="1"/>
              <text x={n.x} y={n.y - 10 - n.h_index*0.28} fill="#8B949E" fontSize="9"
                textAnchor="middle" fontFamily="IBM Plex Mono"
                style={{opacity: n.h_index > 25 ? 1 : 0}}>
                {n.name.split(' ')[1]}
              </text>
            </g>
          ))}
        </svg>
        <div className="legend" style={{marginTop:8}}>
          {data.CLUSTERS.map(c=><div key={c.id}><span className="d" style={{background:c.color,borderRadius:'50%'}}/>{c.name}</div>)}
          <div style={{marginLeft:'auto'}}>
            <span style={{color:'#3FB950'}}>━</span> accepted
            <span style={{color:'#D29922',marginLeft:12}}>━</span> pending
            <span style={{color:'#F85149',marginLeft:12}}>━</span> rejected
          </div>
        </div>
      </div>

      <div className="grid" style={{gridTemplateColumns:'1fr 1fr', marginBottom:16, gap:16}}>
        <div className="card">
          <h3>Payoff matrix <span className="meta">game-theoretic · Nash marked</span></h3>
          <div className="field" style={{marginBottom:10}}>
            <label>Pair (top 20 by Nash)</label>
            <select value={pairIdx} onChange={e=>setPairIdx(+e.target.value)}>
              {top.slice(0,20).map((c,i)=><option key={i} value={i}>{c.a.name} ↔ {c.b.name} · n={c.nash.toFixed(3)}</option>)}
            </select>
          </div>
          <div className="payoff">
            <div className="hd"></div>
            <div className="hd">B: Cooperate</div>
            <div className="hd">B: Defect</div>
            <div className="hd" style={{alignItems:'flex-end'}}>A: Coop</div>
            <div className="cell nash">
              <span className="nash-mark">◆ NASH</span>
              <div className="pr"><span>A</span><span>B</span></div>
              <div className="pv"><span>{payoff.CC[0].toFixed(2)}</span><span>{payoff.CC[1].toFixed(2)}</span></div>
            </div>
            <div className="cell">
              <div className="pr"><span>A</span><span>B</span></div>
              <div className="pv"><span>{payoff.CD[0].toFixed(2)}</span><span>{payoff.CD[1].toFixed(2)}</span></div>
            </div>
            <div className="hd">A: Defect</div>
            <div className="cell">
              <div className="pr"><span>A</span><span>B</span></div>
              <div className="pv"><span>{payoff.DC[0].toFixed(2)}</span><span>{payoff.DC[1].toFixed(2)}</span></div>
            </div>
            <div className="cell">
              <div className="pr"><span>A</span><span>B</span></div>
              <div className="pv"><span>{payoff.DD[0].toFixed(2)}</span><span>{payoff.DD[1].toFixed(2)}</span></div>
            </div>
          </div>
          <div style={{display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:12,marginTop:14,fontSize:11}}>
            <div><div style={{color:'var(--muted)',fontFamily:'var(--mono)',fontSize:10,textTransform:'uppercase',letterSpacing:'.08em'}}>Nash value</div>
              <div style={{fontFamily:'var(--mono)',fontSize:18,color:'#6fda7e'}}>{sel.nash.toFixed(3)}</div></div>
            <div><div style={{color:'var(--muted)',fontFamily:'var(--mono)',fontSize:10,textTransform:'uppercase',letterSpacing:'.08em'}}>Similarity</div>
              <div style={{fontFamily:'var(--mono)',fontSize:18}}>{sel.sim.toFixed(3)}</div></div>
            <div><div style={{color:'var(--muted)',fontFamily:'var(--mono)',fontSize:10,textTransform:'uppercase',letterSpacing:'.08em'}}>Recommended</div>
              <div style={{fontFamily:'var(--mono)',fontSize:13,color:'#79b8ff',paddingTop:3}}>COOP, COOP</div></div>
          </div>
        </div>

        <div className="card pad-0">
          <div style={{padding:'14px 16px',borderBottom:'1px solid var(--border)',display:'flex',alignItems:'center',justifyContent:'space-between'}}>
            <h3 style={{margin:0}}>All collaborations</h3>
            <div style={{display:'flex',gap:4,fontFamily:'var(--mono)',fontSize:11}}>
              {['All','Accepted','Pending','Rejected'].map(f=>(
                <button key={f} onClick={()=>setFilter(f)}
                  className="btn"
                  style={filter===f?{borderColor:'var(--accent)',background:'rgba(47,129,247,.1)',color:'#79b8ff'}:{}}>
                  {f}
                </button>
              ))}
            </div>
          </div>
          <div style={{maxHeight:400, overflow:'auto'}}>
            <table className="t">
              <thead><tr>
                <th>Pair</th><th className="num">Sim</th>
                <th className="num">U_a</th><th className="num">U_b</th>
                <th className="num">Nash</th><th>Status</th>
              </tr></thead>
              <tbody>
                {filtered.slice(0,30).map((c,i)=>(
                  <tr key={i}>
                    <td>
                      <div style={{fontSize:12}}>{c.a.name} <span style={{color:'var(--muted-2)'}}>↔</span> {c.b.name}</div>
                      <div style={{color:'var(--muted-2)',fontSize:10,fontFamily:'var(--mono)'}}>{c.a.lab.name} / {c.b.lab.name}</div>
                    </td>
                    <td className="num">{c.sim.toFixed(3)}</td>
                    <td className="num">{c.ua.toFixed(2)}</td>
                    <td className="num">{c.ub.toFixed(2)}</td>
                    <td className="num" style={{color:'#6fda7e'}}>{c.nash.toFixed(3)}</td>
                    <td><Badge kind={c.status==='accepted'?'green':c.status==='pending'?'amber':'red'}>{c.status}</Badge></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </>
  );
}

// ═══ PAGE 5 — AGENTS ═══════════════════════════════════════════════════════
function PageAgents({ data, showLog }) {
  const [logIdx, setLogIdx] = useStateP(data.LOG_LINES.length);
  const logRef = useRefP(null);

  useEffectP(()=>{
    if (logIdx >= data.LOG_LINES.length) return;
    const t = setTimeout(()=>setLogIdx(i=>Math.min(i+1, data.LOG_LINES.length)), 400);
    return () => clearTimeout(t);
  },[logIdx, data.LOG_LINES.length]);

  useEffectP(()=>{
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  },[logIdx]);

  return (
    <>
      <div className="ph">
        <div>
          <h1>Agents</h1>
          <div className="sub">Mission control · 8 agents · cycle #248 complete</div>
        </div>
        <div className="ph-actions">
          <button className="btn" onClick={()=>window._hideAction('/recluster')}>
            <Icon d={icons.refresh} size={13}/> Re-run clustering
          </button>
          <button className="btn" onClick={()=>window._hideAction('/recommendations')}>
            <Icon d={icons.refresh} size={13}/> Re-run recs
          </button>
          <button className="btn" style={{color:'#ff7b72',borderColor:'#4a1d1d'}}
            onClick={()=>window._hideAction('/reseed',
              { confirm: 'This will WIPE and reseed the database. Continue?' })}>
            Reset + reseed DB
          </button>
          <button className="btn primary" onClick={()=>window._hideAction('/run')}>
            <Icon d={icons.play} size={13}/> Run full MAS cycle
          </button>
        </div>
      </div>

      <div className="agent-grid" style={{marginBottom:16}}>
        {data.AGENTS.map((a,i)=>{
          const cls = a.status==='idle'?'idle':a.status==='error'?'err':'';
          const bdg = a.status==='idle'?'idle':a.status==='error'?'error':'active';
          const [pre, ...rest] = a.name.match(/^Agent/) ? ['Agent', a.name.slice(5)] : ['', a.name];
          const color = a.status==='error'?'#F85149':a.status==='idle'?'#636d78':'#2F81F7';
          return (
            <div key={i} className={`agent-card ${cls}`}>
              <div className="top">
                <div className="nm"><span className="pre">{pre}</span>{rest}</div>
                <div className={`bdg ${bdg}`}>{a.status.toUpperCase()}</div>
              </div>
              <div className="st">
                <span className="dot"/>
                <span style={{fontFamily:'var(--mono)',fontSize:11,color:'var(--muted)'}}>
                  {a.status==='error' ? 'Fallback heuristic engaged' :
                   a.status==='idle' ? 'Awaiting trigger' : 'Processing batch'}
                </span>
              </div>
              <div className="mini">
                {a.series.map((v,k)=><i key={k} style={{height:`${(v/Math.max(...a.series))*100}%`, background: color}}/>)}
              </div>
              <div className="rows">
                <div className="k">Last run</div><div className="v">{a.last}</div>
                <div className="k">Records</div><div className="v">{fmt(a.records)}</div>
              </div>
            </div>
          );
        })}
      </div>

      {showLog && (
        <div className="card pad-0" style={{marginBottom:16}}>
          <div style={{padding:'14px 16px',borderBottom:'1px solid var(--border)',
            display:'flex',alignItems:'center',justifyContent:'space-between'}}>
            <h3 style={{margin:0}}>Agent log <span className="meta">logs/mas.log · cycle #248</span></h3>
            <div style={{display:'flex',gap:8,alignItems:'center'}}>
              <span style={{fontFamily:'var(--mono)',fontSize:11,color:'var(--muted)'}}>
                <span className="stat-pill"><span className="d"/>auto-refresh 5s</span>
              </span>
              <a className="btn" href="/api/logs/download" download>
                <Icon d={icons.download} size={13}/> Download
              </a>
            </div>
          </div>
          <div className="log" ref={logRef}>
            {data.LOG_LINES.slice(0,logIdx).map((l,i)=>{
              const [ts, lvl, agent, msg] = l;
              return (
                <div key={i}>
                  <span className="ts">{ts}</span>
                  <span className={`lvl ${lvl.trim()}`}>{lvl}</span>
                  <span className="a">[{agent}]</span> {msg}
                </div>
              );
            })}
            {logIdx >= data.LOG_LINES.length && <span className="cursor"/>}
          </div>
        </div>
      )}
    </>
  );
}

Object.assign(window, { PageOverview, PageResearchers, PageClusters, PageCollabs, PageAgents });
