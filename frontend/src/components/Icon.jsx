const paths = {
  inbox: <path d="M4 5h16v14H4V5Zm0 9h4l1.5 2h5L16 14h4M12 7v6m0 0 2.5-2.5M12 13 9.5 10.5" />,
  split: <path d="M12 20V5m0 0L8.5 8.5M12 5l3.5 3.5M5 19l3-3m8 0 3 3M5 5l3 3m8 0 3-3" />,
  hash: <path d="M9 3 7 21m10-18-2 18M4 9h16M3 15h16" />,
  plus: <path d="M12 5v14M5 12h14" />,
  list: <path d="M8 6h11M8 12h11M8 18h11M4 6h.01M4 12h.01M4 18h.01" />,
};

export default function Icon({ name }) {
  return <svg className="icon" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">{paths[name]}</svg>;
}
