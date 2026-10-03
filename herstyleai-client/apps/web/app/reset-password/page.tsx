"use client";

import Image from "next/image";
import Link from "next/link";
import { FormEvent, useState } from "react";
import { ApiError, api } from "@/lib/api";

export default function ResetPasswordPage() {
  const [token] = useState(() => {
    if (typeof window === "undefined") return "";
    const hash = window.location.hash.replace(/^#/, "");
    return new URLSearchParams(hash).get("token") ?? "";
  });
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [done, setDone] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!token) {
      setError("Liên kết khôi phục không hợp lệ hoặc đã hết hạn.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Mật khẩu nhập lại chưa khớp.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await api.resetPassword(token, password);
      setDone(true);
    } catch (reason) {
      setError(reason instanceof ApiError && reason.status === 400
        ? "Liên kết khôi phục không hợp lệ hoặc đã hết hạn."
        : "Không thể đặt lại mật khẩu. Vui lòng thử lại sau.");
    } finally {
      setLoading(false);
    }
  }

  return <div className="auth-page"><div className="auth-layout">
    <aside className="auth-visual auth-visual-reset">
      <Image src="/auth/auth-office-style.jpg" alt="Minh hoạ khôi phục tài khoản HerStyle AI" fill sizes="(max-width: 900px) 100vw, 50vw" priority />
    </aside>
    <div className="auth-card">
      <span className="brand-mark">H</span>
      <h1>Đặt mật khẩu mới</h1>
      {done ? <>
        <p>Mật khẩu đã được cập nhật. Tất cả phiên đăng nhập cũ đã được đăng xuất.</p>
        <Link href="/login" className="btn primary full">Đăng nhập</Link>
      </> : <>
        <p>Chọn một mật khẩu mới có ít nhất 8 ký tự.</p>
        <form onSubmit={submit} className="auth-form">
          <label>Mật khẩu mới<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required minLength={8} autoComplete="new-password" /></label>
          <label>Nhập lại mật khẩu<input type="password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} required minLength={8} autoComplete="new-password" /></label>
          {error ? <p className="error-copy">{error}</p> : null}
          <button className="btn primary full" type="submit" disabled={loading}>{loading ? "Đang cập nhật…" : "Đặt lại mật khẩu"}</button>
        </form>
      </>}
      <p className="auth-switch"><Link href="/login">← Quay lại đăng nhập</Link></p>
    </div>
  </div></div>;
}
