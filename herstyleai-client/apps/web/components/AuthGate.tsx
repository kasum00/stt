"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth/auth-context";

const PUBLIC_ROUTES = new Set(["/", "/login", "/register", "/forgot-password", "/reset-password"]);

export function AuthGate({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { status } = useAuth();
  const isPublic = PUBLIC_ROUTES.has(pathname);

  useEffect(() => {
    if (status === "unauthenticated" && !isPublic) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
    }
    if (status === "authenticated" && (pathname === "/login" || pathname === "/register")) {
      router.replace("/planner");
    }
  }, [isPublic, pathname, router, status]);

  if (!isPublic && status === "loading") {
    return <div className="auth-loading"><h2>Đang khôi phục phiên đăng nhập…</h2></div>;
  }
  if (!isPublic && status !== "authenticated") return null;
  return <>{children}</>;
}
