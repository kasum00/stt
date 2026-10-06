"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import AppShell from "@/components/AppShell";
import PageHeader from "@/components/PageHeader";
import Icon from "@/components/Icon";
import { api } from "@/lib/api";

const occasions = [["work", "Đi làm"], ["calendar", "Họp"], ["sparkle", "Thuyết trình"], ["heart", "Hẹn hò"], ["user", "Dạo phố"], ["chat", "Sự kiện khác"]];
const styles = ["Thanh lịch", "Tối giản", "Chuyên nghiệp", "Nữ tính", "Trẻ trung"];

export default function Recommend() {
  const router = useRouter();
  const [occasion, setOccasion] = useState("Đi làm");
  const [style, setStyle] = useState("Chuyên nghiệp");
  const [request, setRequest] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function generate() {
    setLoading(true);
    setError("");
    try {
      const result = await api.getWeeklyRecommendation({
        latitude: 21.0285,
        longitude: 105.8542,
        prefer_dress: false,
        days: 1,
        styling_request: [occasion, style, request.trim()].filter(Boolean).join(" · "),
      });
      sessionStorage.setItem("herstyleai:last-outfit", JSON.stringify(result));
      router.push("/recommend/result");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể tạo gợi ý phối đồ.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell>
      <PageHeader title="Bạn đang cần phối đồ cho dịp gì?" subtitle="Cho HerStyle AI biết hoàn cảnh và phong cách bạn mong muốn." />
      <section className="recommend-card">
        <div className="occasion-grid">{occasions.map(([icon, text]) => <button type="button" className={occasion === text ? "active" : ""} onClick={() => setOccasion(text)} key={text}><Icon name={icon} size={23} /><span>{text}</span></button>)}</div>
        <div className="form-block"><label>Phong cách mong muốn</label><div className="chips big">{styles.map((text) => <button type="button" className={style === text ? "active" : ""} onClick={() => setStyle(text)} key={text}>{text}</button>)}</div></div>
        <div className="form-block"><label>Thời tiết</label><div className="weather-line">☁️ <strong>Hà Nội · hôm nay</strong><span>· AI sẽ lấy dữ liệu thời tiết hiện tại</span></div></div>
        <div className="form-block"><label>Yêu cầu đặc biệt <span>(tùy chọn)</span></label><textarea value={request} onChange={(event) => setRequest(event.target.value)} maxLength={200} placeholder="Ví dụ: Tôi có buổi thuyết trình quan trọng hôm nay..." /><small>{request.length}/200</small></div>
        {error && <p className="form-error">{error}</p>}
        <button type="button" className="button button-primary create-outfit" onClick={() => void generate()} disabled={loading}><Icon name="sparkle" size={18} /> {loading ? "Đang tạo gợi ý…" : "Tạo gợi ý phối đồ"}</button>
      </section>
    </AppShell>
  );
}
