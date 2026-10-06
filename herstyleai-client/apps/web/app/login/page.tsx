"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { Brand } from "@/components/AppShell";
import { useAuth } from "@/lib/auth/auth-context";

export default function LoginPage(){
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email.trim(), password);
      router.push("/home");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Đăng nhập không thành công.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-layout">
      <section className="auth-side">
        <img className="auth-side-image" src="/assets/auth-pastel-mint.png" alt="Bảng phối đồ thanh lịch pastel xanh mint" />
        <Brand/>
        <div className="auth-side-text"><h1>Chào mừng<br/>quay trở lại</h1><p>Đăng nhập để tiếp tục hành trình thời trang thông minh cùng HerStyle AI.</p></div>
      </section>
      <section className="auth-main">
        <form className="auth-card" onSubmit={submit}>
          <h2>Đăng nhập</h2>
          <label>Email<input value={email} onChange={(event) => setEmail(event.target.value)} required type="email" placeholder="Nhập email của bạn"/></label>
          <label>Mật khẩu<input value={password} onChange={(event) => setPassword(event.target.value)} required type="password" placeholder="Nhập mật khẩu"/></label>
          <Link className="forgot" href="/forgot-password">Quên mật khẩu?</Link>
          {error && <p className="form-error">{error}</p>}
          <button className="button button-primary auth-button" type="submit" disabled={loading}>{loading ? "Đang đăng nhập…" : "Đăng nhập"}</button>
          <div className="divider"><span>Hoặc đăng nhập với</span></div>
          <div className="socials"><button>G</button><button>●</button><button>f</button></div>
          <p className="switch-auth">Chưa có tài khoản? <Link href="/register">Đăng ký ngay</Link></p>
        </form>
      </section>
    </main>
  );
}
