"use client";

import Image from "next/image";
import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth/auth-context";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      await login(email.trim(), password);
      const next = new URLSearchParams(window.location.search).get("next");
      router.replace(next?.startsWith("/") ? next : "/stylist");
    } catch (reason) {
      setError(reason instanceof ApiError && reason.status === 401
        ? "Email hoặc mật khẩu không đúng."
        : reason instanceof Error ? reason.message : "Không thể đăng nhập.");
    } finally {
      setLoading(false);
    }
  }

  return <div className="auth-page"><div className="auth-layout">
    <aside className="auth-visual auth-visual-login">
      <Image src="/auth/auth-office-style.jpg" alt="Minh hoạ phong cách HerStyle AI" fill sizes="(max-width: 900px) 100vw, 50vw" priority />
    </aside>
    <div className="auth-card">
    <span className="brand-mark">H</span>
    <h1>Chào mừng bạn trở lại</h1>
    <p>Đăng nhập để tiếp tục hành trình phong cách của bạn.</p>
    <form onSubmit={submit} className="auth-form">
      <label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required autoComplete="email" /></label>
      <label>Mật khẩu<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required autoComplete="current-password" /></label>
      <div className="auth-forgot"><Link href="/forgot-password">Quên mật khẩu?</Link></div>
      {error ? <p className="error-copy">{error}</p> : null}
      <button className="btn primary full" disabled={loading}>{loading ? "Đang đăng nhập…" : "Đăng nhập"}</button>
    </form>
    <p className="auth-switch">Chưa có tài khoản? <Link href="/register">Tạo tài khoản</Link></p>
    </div>
  </div></div>;
}
