import React from 'react';

/* Hand-rolled SVG charts — line, area, bar, donut, sparkline. Tabular-figure friendly. */

export function buildPath(points) {
  return points.map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(2)},${p[1].toFixed(2)}`).join(" ");
}

export function Sparkline({ data, width = 80, height = 22, color = "currentColor", fill = false }) {
  if (!data || data.length < 2) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const step = width / (data.length - 1);
  const pts = data.map((v, i) => [i * step, height - ((v - min) / range) * (height - 2) - 1]);
  const linePath = buildPath(pts);
  const areaPath = `${linePath} L${width},${height} L0,${height} Z`;
  return (
    <svg width={width} height={height} style={{ display: "block" }}>
      {fill && <path d={areaPath} fill={color} opacity="0.10"/>}
      <path d={linePath} stroke={color} strokeWidth="1.5" fill="none" strokeLinecap="round"/>
    </svg>
  );
}

export function LineArea({ data, labels, height = 220, accent = "var(--ink)", positive = true }) {
  const padL = 44, padR = 12, padT = 14, padB = 28;
  const ref = React.useRef(null);
  const [w, setW] = React.useState(640);
  React.useEffect(() => {
    if (!ref.current) return;
    const ro = new ResizeObserver(([e]) => setW(e.contentRect.width));
    ro.observe(ref.current);
    return () => ro.disconnect();
  }, []);

  const innerW = Math.max(40, w - padL - padR);
  const innerH = height - padT - padB;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = (max - min) * 1.15 || 1;
  const baseline = min - (max - min) * 0.08;
  const step = innerW / (data.length - 1);

  const pts = data.map((v, i) => [padL + i * step, padT + (1 - (v - baseline) / range) * innerH]);
  const linePath = buildPath(pts);
  const areaPath = `${linePath} L${pts[pts.length-1][0]},${padT + innerH} L${pts[0][0]},${padT + innerH} Z`;

  // Y ticks (4)
  const ticks = [0, 0.33, 0.66, 1].map(t => baseline + range * (1 - t));
  const fmt = (v) => "$" + Math.round(v / 1000) + "k";

  const [hover, setHover] = React.useState(null);

  return (
    <div ref={ref} style={{ width: "100%" }}>
      <svg width={w} height={height} onMouseLeave={() => setHover(null)}
           onMouseMove={(e) => {
             const r = e.currentTarget.getBoundingClientRect();
             const x = e.clientX - r.left;
             const i = Math.max(0, Math.min(data.length - 1, Math.round((x - padL) / step)));
             setHover(i);
           }}>
        <defs>
          <linearGradient id="la-g" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={accent} stopOpacity="0.16"/>
            <stop offset="100%" stopColor={accent} stopOpacity="0"/>
          </linearGradient>
        </defs>
        {ticks.map((v, i) => {
          const y = padT + (i / (ticks.length - 1)) * innerH;
          return (
            <g key={i}>
              <line x1={padL} x2={w - padR} y1={y} y2={y} stroke="var(--line)" strokeDasharray={i === ticks.length - 1 ? "0" : "2 4"}/>
              <text x={padL - 8} y={y + 3} fontSize="10" fill="var(--ink-3)" textAnchor="end" fontFamily="var(--font-mono)">{fmt(v)}</text>
            </g>
          );
        })}
        {labels && labels.map((l, i) => (
          <text key={i} x={padL + i * step} y={height - 8} fontSize="10" fill="var(--ink-3)" textAnchor="middle" fontFamily="var(--font-ui)">
            {l}
          </text>
        ))}
        <path d={areaPath} fill="url(#la-g)"/>
        <path d={linePath} stroke={accent} strokeWidth="1.75" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
        {pts.map((p, i) => (
          <circle key={i} cx={p[0]} cy={p[1]} r={hover === i ? 3.5 : 0} fill={accent} stroke="var(--surface)" strokeWidth="1.5"/>
        ))}
        {hover != null && (
          <g>
            <line x1={pts[hover][0]} x2={pts[hover][0]} y1={padT} y2={padT + innerH} stroke="var(--line-strong)" strokeDasharray="2 3"/>
            <g transform={`translate(${Math.min(w - 110, Math.max(padL, pts[hover][0] - 50))}, ${padT - 4})`}>
              <rect x="0" y="0" width="100" height="36" rx="6" fill="var(--surface)" stroke="var(--line-strong)"/>
              <text x="10" y="14" fontSize="10" fill="var(--ink-3)" fontFamily="var(--font-ui)">{labels?.[hover] ?? ""}</text>
              <text x="10" y="28" fontSize="13" fill="var(--ink)" fontFamily="var(--font-num)" fontWeight="500">
                ${data[hover].toLocaleString()}
              </text>
            </g>
          </g>
        )}
      </svg>
    </div>
  );
}

export function Donut({ slices, size = 160, thickness = 22, centerLabel, centerSub }) {
  const total = slices.reduce((s, x) => s + x.value, 0) || 1;
  const r = size / 2;
  const inner = r - thickness;
  let acc = -Math.PI / 2;
  const arcs = slices.map((s) => {
    const a = (s.value / total) * Math.PI * 2;
    const start = acc;
    const end = acc + a;
    acc = end;
    const large = a > Math.PI ? 1 : 0;
    const x1 = r + Math.cos(start) * (r - 1);
    const y1 = r + Math.sin(start) * (r - 1);
    const x2 = r + Math.cos(end) * (r - 1);
    const y2 = r + Math.sin(end) * (r - 1);
    const x3 = r + Math.cos(end) * inner;
    const y3 = r + Math.sin(end) * inner;
    const x4 = r + Math.cos(start) * inner;
    const y4 = r + Math.sin(start) * inner;
    return {
      d: `M${x1},${y1} A${r-1},${r-1} 0 ${large} 1 ${x2},${y2} L${x3},${y3} A${inner},${inner} 0 ${large} 0 ${x4},${y4} Z`,
      color: s.color,
      label: s.label,
      value: s.value,
    };
  });
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
      <svg width={size} height={size}>
        {arcs.map((a, i) => <path key={i} d={a.d} fill={a.color}/>)}
        {centerLabel && (
          <g>
            <text x={r} y={r - 4} textAnchor="middle" fontSize="10" fill="var(--ink-3)"
                  fontFamily="var(--font-ui)" letterSpacing="1.2">{centerSub}</text>
            <text x={r} y={r + 16} textAnchor="middle" fontSize="20" fill="var(--ink)"
                  fontFamily="var(--font-num)" fontWeight="500">{centerLabel}</text>
          </g>
        )}
      </svg>
      <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 6 }}>
        {slices.map((s, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12 }}>
            <span style={{ width: 8, height: 8, borderRadius: 2, background: s.color, flexShrink: 0 }}/>
            <span style={{ flex: 1, color: "var(--ink-2)" }}>{s.label}</span>
            <span className="num tnum" style={{ fontSize: 13 }}>${s.value.toLocaleString()}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function HBar({ rows, valueFmt = (v) => `$${v.toLocaleString()}`, max }) {
  const m = max ?? Math.max(...rows.map(r => Math.max(r.value, r.target ?? 0)));
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      {rows.map((r, i) => {
        const pct = (r.value / m) * 100;
        const tpct = r.target ? (r.target / m) * 100 : null;
        const over = r.target && r.value > r.target;
        return (
          <div key={i}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 5, fontSize: 12.5 }}>
              <span style={{ color: "var(--ink-2)" }}>{r.label}</span>
              <span style={{ color: "var(--ink-3)" }}>
                <span className="num tnum" style={{ color: over ? "var(--negative)" : "var(--ink)", fontSize: 13.5 }}>{valueFmt(r.value)}</span>
                {r.target ? <span style={{ marginLeft: 4 }}> / {valueFmt(r.target)}</span> : null}
              </span>
            </div>
            <div style={{ position: "relative", height: 8, background: "var(--surface-2)", border: "1px solid var(--line)", borderRadius: 999 }}>
              <div style={{
                position: "absolute", left: 0, top: 0, bottom: 0,
                width: `${Math.min(100, pct)}%`,
                background: over ? "var(--negative)" : (r.color || "var(--ink)"),
                borderRadius: 999,
              }}/>
              {tpct && tpct < 100 && (
                <div style={{
                  position: "absolute", left: `${tpct}%`, top: -3, bottom: -3,
                  width: 1.5, background: "var(--ink-3)", opacity: 0.5,
                }}/>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function StackedTimeline({ months, series, height = 180, palette }) {
  /* series: [{ label, values: [n,n,n] }] — represents debt balances over time */
  const ref = React.useRef(null);
  const [w, setW] = React.useState(420);
  React.useEffect(() => {
    if (!ref.current) return;
    const ro = new ResizeObserver(([e]) => setW(e.contentRect.width));
    ro.observe(ref.current);
    return () => ro.disconnect();
  }, []);
  const padL = 36, padR = 8, padT = 8, padB = 22;
  const innerW = Math.max(40, w - padL - padR);
  const innerH = height - padT - padB;
  const totals = months.map((_, i) => series.reduce((s, sr) => s + sr.values[i], 0));
  const max = Math.max(...totals) || 1;
  const step = innerW / (months.length - 1);

  // Build cumulative paths from bottom up
  const cum = months.map(() => 0);
  const layers = series.map((sr) => {
    const top = sr.values.map((v, i) => {
      const y0 = padT + innerH - (cum[i] / max) * innerH;
      cum[i] += v;
      const y1 = padT + innerH - (cum[i] / max) * innerH;
      return { x: padL + i * step, y0, y1 };
    });
    return { label: sr.label, top };
  });

  return (
    <div ref={ref}>
      <svg width={w} height={height}>
        {[0, 0.5, 1].map((t, i) => {
          const y = padT + t * innerH;
          return <line key={i} x1={padL} x2={w - padR} y1={y} y2={y} stroke="var(--line)" strokeDasharray="2 3"/>;
        })}
        {layers.map((l, i) => {
          const color = palette[i % palette.length];
          const top = l.top.map((p) => [p.x, p.y1]);
          const bot = l.top.map((p) => [p.x, p.y0]).reverse();
          const path = buildPath([...top, ...bot]) + " Z";
          return <path key={i} d={path} fill={color} opacity={0.85}/>;
        })}
        {months.map((m, i) => (
          (i % Math.ceil(months.length / 6) === 0 || i === months.length - 1) && (
            <text key={i} x={padL + i * step} y={height - 6} fontSize="10" fill="var(--ink-3)" textAnchor="middle">{m}</text>
          )
        ))}
        <text x={padL - 6} y={padT + 8} fontSize="10" fill="var(--ink-3)" textAnchor="end" fontFamily="var(--font-mono)">${Math.round(max/1000)}k</text>
        <text x={padL - 6} y={padT + innerH + 2} fontSize="10" fill="var(--ink-3)" textAnchor="end" fontFamily="var(--font-mono)">$0</text>
      </svg>
    </div>
  );
}

