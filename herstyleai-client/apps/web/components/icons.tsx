type IconProps = { size?: number; stroke?: number };

export function Icon({ name, size = 20, stroke = 1.8 }: IconProps & { name: string }) {
  const common = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: stroke,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true,
  };

  switch (name) {
    case "home":
      return <svg {...common}><path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z" /></svg>;
    case "hanger":
      return <svg {...common}><path d="M12 5a2.2 2.2 0 1 0-2.2-2.2" /><path d="M12 5c0 1.5-1.5 2.2-2.7 3.1L3 12.1c-.8.6-.4 1.9.6 1.9h16.8c1 0 1.4-1.3.6-1.9l-6.3-4c-1.2-.9-2.7-1.6-2.7-3.1Z" /><path d="M4 18h16M6 21h12" /></svg>;
    case "sparkle":
      return <svg {...common}><path d="m12 2 1.2 5.2L18 9l-4.8 1.8L12 16l-1.2-5.2L6 9l4.8-1.8z" /><path d="m19 15 .6 2.4L22 18l-2.4.6L19 21l-.6-2.4L16 18l2.4-.6z" /></svg>;
    case "calendar":
      return <svg {...common}><rect x="3" y="4.5" width="18" height="16" rx="2" /><path d="M7 2.5v4M17 2.5v4M3 9h18M8 13h.01M12 13h.01M16 13h.01M8 17h.01M12 17h.01" /></svg>;
    case "plus":
      return <svg {...common}><path d="M12 5v14M5 12h14" /></svg>;
    case "upload":
      return <svg {...common}><path d="M12 16V4M8 8l4-4 4 4M4 16.5V20h16v-3.5" /></svg>;
    case "search":
      return <svg {...common}><circle cx="10.8" cy="10.8" r="6.8" /><path d="m16 16 5 5" /></svg>;
    case "arrow":
      return <svg {...common}><path d="M5 12h14M13 6l6 6-6 6" /></svg>;
    case "chevron":
      return <svg {...common}><path d="m8 10 4 4 4-4" /></svg>;
    case "close":
      return <svg {...common}><path d="m6 6 12 12M18 6 6 18" /></svg>;
    case "check":
      return <svg {...common}><path d="m5 12 4 4L19 6" /></svg>;
    case "heart":
      return <svg {...common}><path d="M20.8 8.9c0 5.5-8.8 10.1-8.8 10.1S3.2 14.4 3.2 8.9A4.7 4.7 0 0 1 12 6.2a4.7 4.7 0 0 1 8.8 2.7Z" /></svg>;
    case "bookmark":
      return <svg {...common}><path d="M6 4.5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2V21l-6-3.5L6 21z" /></svg>;
    case "thumb":
      return <svg {...common}><path d="M7 10v10H4a1 1 0 0 1-1-1v-8a1 1 0 0 1 1-1zM7 20h8.5a2 2 0 0 0 1.9-1.4l2-6A2 2 0 0 0 17.5 10H15l.6-3.6A2 2 0 0 0 13.6 4L8 10" /></svg>;
    case "edit":
      return <svg {...common}><path d="m4 16.5-.8 3.8 3.8-.8L19.5 7a2.1 2.1 0 0 0-3-3zM14.5 5.5l4 4" /></svg>;
    case "trash":
      return <svg {...common}><path d="M4 7h16M10 11v6M14 11v6M6 7l1 14h10l1-14M9 7V4h6v3" /></svg>;
    case "cloud":
      return <svg {...common}><path d="M7 18h10a4 4 0 0 0 .5-8 6 6 0 0 0-11.7 1A3.5 3.5 0 0 0 7 18Z" /></svg>;
    case "sun":
      return <svg {...common}><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></svg>;
    case "menu":
      return <svg {...common}><path d="M4 7h16M4 12h16M4 17h16" /></svg>;
    case "chat":
      return <svg {...common}><path d="M5 5.5h14a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-8l-4.5 3v-3H5a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2Z" /><path d="M7.5 11.5h.01M12 11.5h.01M16.5 11.5h.01" /></svg>;
    case "bell":
      return <svg {...common}><path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9Z" /><path d="M10 21h4" /></svg>;
    case "info":
      return <svg {...common}><circle cx="12" cy="12" r="9" /><path d="M12 11v5M12 8h.01" /></svg>;
    case "refresh":
      return <svg {...common}><path d="M20 11a8 8 0 0 0-14.8-4L3 10M3 5v5h5M4 13a8 8 0 0 0 14.8 4L21 14M21 19v-5h-5" /></svg>;
    default:
      return <svg {...common}><circle cx="12" cy="12" r="8" /></svg>;
  }
}

