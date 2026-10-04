/* eslint-disable @next/next/no-img-element */

import Link from "next/link";
import { Icon } from "@/components/Icon";

const hero = "https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?auto=format&fit=crop&w=1200&q=85";

export default function Home() {
  return <div className="home-page">
    <section className="hero-card">
      <div className="hero-copy">
        <span className="pill soft"><Icon name="sparkle" size={15}/> Your Personal AI Stylist</span>
        <h1>Phong cách của bạn<br/>Phiên bản đẹp nhất<br/><em>với AI</em></h1>
        <p>HerStyle AI giúp bạn quản lý tủ đồ, gợi ý phối đồ thông minh và tạo phong cách riêng phù hợp với công việc, thời tiết và cuộc sống hằng ngày.</p>
        <div className="hero-actions"><Link href="/planner" className="btn primary">Bắt đầu ngay →</Link><Link href="/outfit" className="btn ghost">Xem demo</Link></div>
      </div>
      <div className="hero-visual"><div className="hero-blob"></div><img src={hero} alt="HerStyle AI fashion"/><span className="hand-note">Be your own<br/>style ♡</span></div>
    </section>
    <section className="feature-grid">
      <Link href="/wardrobe" className="feature-card"><span className="feature-icon blue"><Icon name="wardrobe"/></span><div><strong>Quản lý tủ đồ</strong><p>Thông minh, trực quan</p></div></Link>
      <Link href="/planner" className="feature-card"><span className="feature-icon blue"><Icon name="sparkle"/></span><div><strong>Gợi ý phối đồ</strong><p>Cá nhân hóa theo bạn</p></div></Link>
      <Link href="/planner" className="feature-card"><span className="feature-icon orange"><Icon name="sun"/></span><div><strong>Phù hợp thời tiết</strong><p>& hoàn cảnh</p></div></Link>
      <Link href="/chat" className="feature-card"><span className="feature-icon pink"><Icon name="clock"/></span><div><strong>Tiết kiệm thời gian</strong><p>Mỗi ngày</p></div></Link>
    </section>
  </div>;
}
