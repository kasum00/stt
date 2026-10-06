import Link from "next/link";
import { Brand } from "@/components/AppShell";
import Icon from "@/components/Icon";

const features = [
  ["wardrobe","Quản lý tủ đồ số","Lưu trữ, phân loại và tìm kiếm trang phục dễ dàng."],
  ["camera","Nhận diện quần áo bằng AI","Tự động nhận diện loại trang phục, màu sắc, chất liệu và phong cách."],
  ["sparkle","Gợi ý phối đồ thông minh","Đề xuất outfit phù hợp với phong cách, hoàn cảnh và thời tiết."],
  ["calendar","Lên kế hoạch mặc đồ","Tạo kế hoạch outfit cho cả tuần dựa trên lịch trình cá nhân."],
  ["chat","Trợ lý AI thời trang","Trò chuyện, tư vấn phong cách và gợi ý outfit theo yêu cầu."],
];

export default function LandingPage(){
  return (
    <main className="landing-page">
      <header className="landing-nav">
        <Brand/>
        <nav><a href="#home" className="current">Trang chủ</a><a href="#features">Tính năng</a><a href="#team">Về chúng tôi</a></nav>
        <div className="landing-nav-actions"><Link className="button button-white" href="/login">Đăng nhập</Link><Link className="button button-primary" href="/register">Đăng ký</Link></div>
      </header>

      <section className="hero" id="home">
        <div className="hero-copy">
          <span className="eyebrow">✦ YOUR SMART PERSONAL STYLIST</span>
          <h1>HerStyle AI</h1>
          <h2>Tủ quần áo số<br/>thông minh cho<br/>phụ nữ công sở</h2>
          <p>Quản lý trang phục, nhận diện bằng AI, gợi ý phối đồ phù hợp với phong cách, lịch trình và thời tiết. Giúp bạn luôn tự tin và thanh lịch mỗi ngày.</p>
          <div className="hero-actions"><Link className="button button-primary button-lg" href="/register">Bắt đầu ngay <span>→</span></Link><a className="button button-outline button-lg" href="#features">Tìm hiểu thêm ↓</a></div>
          <div className="hero-stats">
            <div><strong>10K+</strong><span>Người dùng tiềm năng</span></div>
            <div><strong>95%</strong><span>Hài lòng với gợi ý</span></div>
            <div><strong>70%</strong><span>Tiết kiệm thời gian chọn đồ</span></div>
          </div>
        </div>

        <div className="hero-visual">
          <div className="hero-model"><img src="/assets/hero-model.png" alt="HerStyle AI"/></div>
          <div className="handwriting">Dress<br/>Smarter<br/>Everyday ♡</div>
          <div className="hero-widget outfit-widget"><div className="widget-head"><strong>Today&apos;s Outfit</strong><span>92% Match</span></div><div className="widget-products"><img src="/assets/blazer.png" alt="blazer"/><img src="/assets/shirt-white.png" alt="shirt"/><img src="/assets/pants-black.png" alt="pants"/><img src="/assets/heels.png" alt="heels"/></div><Link href="/recommend/result">View Outfit →</Link></div>
          <div className="hero-widget weather-widget"><small>Hà Nội</small><strong>27°C</strong><span>☁ Có mây</span></div>
          <div className="hero-widget week-widget"><strong>Your Week</strong><small>6 – 12 Tháng 10, 2026</small><div className="week-mini">{["T2","T3","T4","T5","T6","T7","CN"].map((x,i)=><div className={i===2?"sel":""} key={x}><span>{x}</span><b>{6+i}</b><img src={["/assets/blazer.png","/assets/shirt-white.png","/assets/blazer.png","/assets/shirt-white.png","/assets/pants-black.png","/assets/blazer-beige.png","/assets/pants-black.png"][i]}/></div>)}</div></div>
        </div>
      </section>

      <section className="features-section" id="features">
        <div className="section-title"><span>HerStyle AI có gì đặc biệt?</span><h2>Các tính năng nổi bật</h2><p>Tất cả những gì bạn cần để xây dựng phong cách riêng, chỉ trong một ứng dụng.</p></div>
        <div className="features-grid">
          {features.map(([icon,title,desc])=><article className="feature-card" key={title}><div className="feature-icon"><Icon name={icon}/></div><h3>{title}</h3><p>{desc}</p></article>)}
        </div>
      </section>

      <section className="how-section">
        <div className="how-copy"><span>✦ TRẢI NGHIỆM ỨNG DỤNG</span><h2><span>Từ tủ đồ của bạn</span><br/>đến những<br/>outfit hoàn hảo</h2><p>HerStyle AI giúp bạn biến tủ quần áo thường ngày thành những gợi ý phối đồ thông minh, phù hợp với phong cách, lịch trình và thời tiết.</p><Link className="button button-primary button-lg" href="/home">Khám phá các tính năng →</Link></div>
        <div className="how-flow">
          {[
            ["Thêm quần áo","/assets/shirt-white.png","Chụp ảnh hoặc tải lên trang phục của bạn."],
            ["AI nhận diện","/assets/shirt-white.png","AI tự động phân tích thuộc tính trang phục."],
            ["Gợi ý phối đồ","/assets/blazer.png","Đề xuất outfit phù hợp hoàn cảnh."],
            ["Lịch mặc đồ","/assets/blazer-beige.png","Lên kế hoạch outfit cho cả tuần."],
          ].map((x,i)=><div className="flow-wrap" key={x[0]}><article className="flow-card"><h3>{x[0]}</h3><img src={x[1]}/><p>{x[2]}</p></article>{i<3 && <b>→</b>}</div>)}
          <article className="flow-card chat-flow"><h3>Trợ lý AI</h3><div className="chat-demo"><span>Tôi có buổi họp quan trọng ngày mai.</span><span>Đây là outfit mình gợi ý cho bạn ✨</span></div><p>Tư vấn nhanh theo nhu cầu của bạn.</p></article>
        </div>
      </section>

      <section className="team-section" id="team">
        <div className="section-title"><span>ĐỘI NGŨ THỰC HIỆN</span><h2>Người tạo nên HerStyle AI</h2><p>Chúng tôi là nhóm sinh viên yêu công nghệ và thời trang, mong muốn mang AI vào trải nghiệm thời trang hàng ngày.</p></div>
        <div className="team-grid">
          {[
            ["Vũ Thu Huyền","Thành viên nhóm"],
            ["Nguyễn Thùy Linh","Thành viên nhóm"],
            ["Nguyễn Hoàng Tùng","Thành viên nhóm"],
            ["Vũ Ngọc Thu Nga","Thành viên nhóm"],
            ["Hà Minh Hiền","Thành viên nhóm"],
          ].map(([name,role],i)=><article key={name}><div className={`team-avatar team-${i+1}`}>{name.split(" ").slice(-1)[0][0]}</div><h3>{name}</h3><p>{role}</p></article>)}
        </div>
        <div className="team-mentors">Dưới sự hướng dẫn của <strong>cô Lã Thị Ngọc Anh</strong> và <strong>cô Lê Tiểu Thanh</strong></div>
      </section>
    </main>
  );
}
