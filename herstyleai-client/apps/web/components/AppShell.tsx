"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import Icon from "./Icon";
import type { ReactNode } from "react";
import { useAuth } from "@/lib/auth/auth-context";

const nav = [
  ["/home","home","Trang chủ"],
  ["/wardrobe","wardrobe","Tủ đồ"],
  ["/recommend","sparkle","Gợi ý phối đồ"],
  ["/calendar","calendar","Lịch của tôi"],
  ["/chat","chat","AI Stylist"],
] as const;

export function Brand() {
  return (
    <Link className="brand" href="/">
      <span className="brand-symbol">✦</span>
      <span>HerStyle AI</span>
    </Link>
  );
}

export default function AppShell({ children }: { children: ReactNode }) {
  const path = usePathname();
  const router = useRouter();
  const { user, status, logout } = useAuth();

  useEffect(() => {
    if (status === "unauthenticated") router.replace("/login");
  }, [router, status]);

  if (status !== "authenticated") {
    return <div className="app-loading">Đang khôi phục phiên đăng nhập…</div>;
  }

  const displayName = user?.email?.split("@")[0] || "Bạn";
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand"><Brand /></div>
        <nav className="sidebar-nav">
          {nav.map(([href,icon,label])=>{
            const active = path === href || (href !== "/home" && path.startsWith(href));
            return (
              <Link className={`nav-item ${active?"active":""}`} href={href} key={href}>
                <Icon name={icon}/><span>{label}</span>
              </Link>
            );
          })}
        </nav>
        <div className="sidebar-footer">
          <Link className={`nav-item ${path==="/profile"?"active":""}`} href="/profile"><Icon name="user"/><span>Hồ sơ</span></Link>
          <button className="nav-item"><Icon name="settings"/><span>Cài đặt</span></button>
        </div>
      </aside>

      <div className="workspace">
        <header className="topbar">
          <div className="global-search"><Icon name="search" size={17}/><input placeholder="Tìm kiếm trang phục, gợi ý..." /></div>
          <div className="topbar-right">
            <button className="notification"><Icon name="bell" size={18}/><i></i></button>
            <Link href="/profile" className="user-box">
              <div className="avatar">{displayName.slice(0, 1).toUpperCase()}</div>
              <div><strong>{displayName}</strong><span>{user?.email}</span></div>
              <b>⌄</b>
            </Link>
            <button className="button button-white topbar-logout" type="button" onClick={() => void logout()}>Đăng xuất</button>
          </div>
        </header>
        <main className="workspace-content">{children}</main>
      </div>
    </div>
  );
}
