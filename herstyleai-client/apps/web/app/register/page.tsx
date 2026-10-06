"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { Brand } from "@/components/AppShell";
import { useAuth } from "@/lib/auth/auth-context";

export default function RegisterPage(){
  const router = useRouter();
  const { register } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (password !== confirmPassword) {
      setError("Mật khẩu xác nhận không khớp.");
      return;
    }
    setLoading(true);
    try {
      await register(email.trim(), password);
      router.push("/login?registered=1");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Đăng ký không thành công.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-layout">
      <section className="auth-side register-side">
        <img className="auth-side-image" src="/assets/auth-pastel-mint.png" alt="Bảng phối đồ thanh lịch pastel xanh mint" />
        <Brand/>
        <div className="auth-side-text"><h1>Tạo tài khoản</h1><p>Tham gia HerStyle AI để xây dựng tủ đồ số và nhận gợi ý phối đồ phù hợp với phong cách của bạn.</p></div>
      </section>
      <section className="auth-main">
        <form className="auth-card register-card" onSubmit={submit}>
          <h2>Đăng ký</h2>
          <label>Họ và tên<input placeholder="Nhập họ và tên"/></label>
          <label>Email<input value={email} onChange={(event) => setEmail(event.target.value)} required type="email" placeholder="Nhập email của bạn"/></label>
          <label>Mật khẩu<input value={password} onChange={(event) => setPassword(event.target.value)} required type="password" placeholder="Nhập mật khẩu"/></label>
          <label>Xác nhận mật khẩu<input value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} required type="password" placeholder="Nhập lại mật khẩu"/></label>
          {error && <p className="form-error">{error}</p>}
          <button className="button button-primary auth-button" type="submit" disabled={loading}>{loading ? "Đang tạo tài khoản…" : "Tạo tài khoản"}</button>
          <p className="switch-auth">Đã có tài khoản? <Link href="/login">Đăng nhập</Link></p>
        </form>
      </section>
    </main>
  );
}
