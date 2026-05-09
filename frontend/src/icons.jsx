import React from 'react';

/* Icons — minimal stroke icons, 16x16 by default */
export const Icon = ({ d, size = 16, fill = "none", stroke = "currentColor", sw = 1.5, ...rest }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill={fill} stroke={stroke}
       strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" {...rest}>
    {d}
  </svg>
);

export const I = {
  dashboard: (p) => <Icon {...p} d={<><rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/></>}/>,
  doc: (p) => <Icon {...p} d={<><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/><path d="M9 13h6M9 17h4"/></>}/>,
  debt: (p) => <Icon {...p} d={<><rect x="3" y="6" width="18" height="13" rx="2"/><path d="M3 10h18"/><path d="M7 15h3"/></>}/>,
  savings: (p) => <Icon {...p} d={<><path d="M12 3v18"/><path d="M5 8h11a3 3 0 0 1 0 6H6a3 3 0 0 0 0 6h13"/></>}/>,
  budget: (p) => <Icon {...p} d={<><circle cx="12" cy="12" r="9"/><path d="M12 3 a9 9 0 0 1 9 9 h-9z" fill="currentColor" stroke="none"/></>}/>,
  payoff: (p) => <Icon {...p} d={<><path d="M3 17l6-6 4 4 8-8"/><path d="M14 7h7v7"/></>}/>,
  chat: (p) => <Icon {...p} d={<><path d="M21 12a8 8 0 0 1-11.5 7.2L3 21l1.8-6.5A8 8 0 1 1 21 12z"/></>}/>,
  settings: (p) => <Icon {...p} d={<><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.6 1.6 0 0 0 .3 1.8l.1.1a2 2 0 0 1-2.8 2.8l-.1-.1a1.6 1.6 0 0 0-1.8-.3 1.6 1.6 0 0 0-1 1.5V21a2 2 0 0 1-4 0v-.1a1.6 1.6 0 0 0-1-1.5 1.6 1.6 0 0 0-1.8.3l-.1.1a2 2 0 0 1-2.8-2.8l.1-.1a1.6 1.6 0 0 0 .3-1.8 1.6 1.6 0 0 0-1.5-1H3a2 2 0 0 1 0-4h.1a1.6 1.6 0 0 0 1.5-1 1.6 1.6 0 0 0-.3-1.8l-.1-.1a2 2 0 0 1 2.8-2.8l.1.1a1.6 1.6 0 0 0 1.8.3 1.6 1.6 0 0 0 1-1.5V3a2 2 0 0 1 4 0v.1a1.6 1.6 0 0 0 1 1.5 1.6 1.6 0 0 0 1.8-.3l.1-.1a2 2 0 0 1 2.8 2.8l-.1.1a1.6 1.6 0 0 0-.3 1.8 1.6 1.6 0 0 0 1.5 1H21a2 2 0 0 1 0 4h-.1a1.6 1.6 0 0 0-1.5 1z"/></>}/>,
  lock: (p) => <Icon {...p} d={<><rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 1 1 8 0v4"/></>}/>,
  shield: (p) => <Icon {...p} d={<><path d="M12 3l8 3v6c0 5-3.4 8.5-8 9-4.6-.5-8-4-8-9V6z"/><path d="M9 12l2 2 4-4"/></>}/>,
  bell: (p) => <Icon {...p} d={<><path d="M6 8a6 6 0 1 1 12 0c0 7 3 7 3 9H3c0-2 3-2 3-9z"/><path d="M10 21a2 2 0 0 0 4 0"/></>}/>,
  search: (p) => <Icon {...p} d={<><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></>}/>,
  upload: (p) => <Icon {...p} d={<><path d="M12 16V4"/><path d="m6 10 6-6 6 6"/><path d="M4 18v2a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-2"/></>}/>,
  send: (p) => <Icon {...p} d={<><path d="m4 12 16-8-4 16-4-7-8-1z"/></>}/>,
  panel: (p) => <Icon {...p} d={<><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M15 4v16"/></>}/>,
  arrow_up: (p) => <Icon {...p} d={<><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></>}/>,
  trend_up: (p) => <Icon {...p} d={<><path d="M3 17l6-6 4 4 8-8"/><path d="M14 7h7v7"/></>}/>,
  trend_dn: (p) => <Icon {...p} d={<><path d="M3 7l6 6 4-4 8 8"/><path d="M14 17h7v-7"/></>}/>,
  check: (p) => <Icon {...p} d={<path d="m5 12 5 5L20 7"/>}/>,
  alert: (p) => <Icon {...p} d={<><path d="M12 9v4"/><path d="M12 17h.01"/><path d="M10.3 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/></>}/>,
  plus: (p) => <Icon {...p} d={<><path d="M12 5v14M5 12h14"/></>}/>,
  x: (p) => <Icon {...p} d={<><path d="M18 6 6 18M6 6l12 12"/></>}/>,
  spark: (p) => <Icon {...p} d={<><path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M5.6 18.4l2.8-2.8M15.6 8.4l2.8-2.8"/></>}/>,
  filter: (p) => <Icon {...p} d={<><path d="M3 5h18l-7 9v6l-4-2v-4z"/></>}/>,
  more: (p) => <Icon {...p} d={<><circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/></>}/>,
  link: (p) => <Icon {...p} d={<><path d="M10 14a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1"/><path d="M14 10a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1"/></>}/>,
  sparkle: (p) => <Icon {...p} d={<><path d="M12 3l1.5 5L18 9.5 13.5 11 12 16l-1.5-5L6 9.5 10.5 8z"/></>}/>,
  refresh: (p) => <Icon {...p} d={<><path d="M3 12a9 9 0 0 1 15-6.7L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-15 6.7L3 16"/><path d="M3 21v-5h5"/></>}/>,
};

