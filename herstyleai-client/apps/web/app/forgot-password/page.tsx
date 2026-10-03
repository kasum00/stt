"use client";

import Image from "next/image";
import Link from "next/link";
import { FormEvent, useState } from "react";
import { api } from "@/lib/api";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [devResetLink, setDevResetLink] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const result = await api.requestPasswordReset(email.trim());
      if (result.reset_token) {
        setDevResetLink(`${window.location.origin}/reset-password#token=${encodeURIComponent(result.reset_token)}`);
      }
      setSent(true);
    } catch {
      setError("Không thể gửi yêu cầu lúc này. Vui lòng thử lại sau.");
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
    <h1>Khôi phục mật khẩu</h1>
    {sent ? <>
      <p>Hãy kiểm tra email của bạn. Nếu địa chỉ này đã đăng ký, bạn sẽ nhận được hướng dẫn khôi phục mật khẩu.</p>
      {devResetLink ? <a href={devResetLink} className="btn ghost full">Mở link reset local</a> : null}
      <Link href="/login" className="btn primary full">Quay lại đăng nhập</Link>
    </> : <>
      <p>Nhập email đã dùng để đăng ký, chúng tôi sẽ hướng dẫn bạn lấy lại quyền truy cập.</p>
      <form onSubmit={submit} className="auth-form">
        <label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required autoComplete="email" placeholder="ban@example.com" /></label>
        {error ? <p className="error-copy">{error}</p> : null}
        <button className="btn primary full" type="submit" disabled={loading}>{loading ? "Đang gửi…" : "Gửi hướng dẫn"}</button>
      </form>
    </>}
    <p className="auth-switch"><Link href="/login">← Quay lại đăng nhập</Link></p>
    </div>
  </div></div>;
}
