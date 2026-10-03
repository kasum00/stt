"use client";

import Image from "next/image";
import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth/auth-context";

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (password !== confirmPassword) {
      setError("Mật khẩu nhập lại chưa khớp.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await register(email.trim(), password);
      router.replace("/login?registered=1");
    } catch (reason) {
      setError(reason instanceof ApiError && reason.status === 409
        ? "Email này đã được đăng ký."
        : reason instanceof Error ? reason.message : "Không thể tạo tài khoản.");
    } finally {
      setLoading(false);
    }
  }

  return <div className="auth-page"><div className="auth-layout">
    <aside className="auth-visual auth-visual-register">
      <Image src="/auth/auth-office-style.jpg" alt="Minh hoạ tạo tài khoản HerStyle AI" fill sizes="(max-width: 900px) 100vw, 50vw" priority />
    </aside>
    <div className="auth-card">
    <span className="brand-mark">H</span>
    <h1>Tạo tài khoản HerStyle AI</h1>
    <p>Bắt đầu xây dựng tủ đồ và phong cách cá nhân của bạn.</p>
    <form onSubmit={submit} className="auth-form">
      <label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required autoComplete="email" /></label>
      <label>Mật khẩu<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required minLength={8} autoComplete="new-password" /></label>
      <label>Nhập lại mật khẩu<input type="password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} required minLength={8} autoComplete="new-password" /></label>
      {error ? <p className="error-copy">{error}</p> : null}
      <button className="btn primary full" disabled={loading}>{loading ? "Đang tạo tài khoản…" : "Đăng ký"}</button>
    </form>
    <p className="auth-switch">Đã có tài khoản? <Link href="/login">Đăng nhập</Link></p>
    </div>
  </div></div>;
}
