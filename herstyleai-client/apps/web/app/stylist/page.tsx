"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { Icon } from "@/components/Icon";
import { ProtectedMediaImage } from "@/components/ProtectedMediaImage";
import { api, cacheWeeklyRecommendation, CalendarEvent, Outfit, resolveMediaUrl, WeeklyResponse } from "@/lib/api";
import { outfitTitle, titleCase } from "@/lib/format";

function itemImage(item: Record<string, unknown>) {
  return resolveMediaUrl([item.transparent_image_url, item.transparent_url, item.model_url, item.image_url, item.image_path].find((value): value is string => typeof value === "string"));
}

function OutfitCard({ outfit, day }: { outfit: Outfit; day: number }) {
  const entries = Object.values(outfit.items ?? {});
  return <article className="outfit-card"><div className="outfit-stack">{entries.slice(0, 4).map((item) => <div className="outfit-stack-item" key={item.item_id}><ProtectedMediaImage src={itemImage(item)} alt={titleCase(item.subcategory ?? item.category ?? "Món đồ")} fallback={<Icon name="shirt" size={27} />} /></div>)}<button className="heart-btn" type="button" aria-label="Lưu outfit"><Icon name="heart" size={17} /></button></div><h3>{outfitTitle(outfit.structure, entries.length)}</h3><p><span>Ngày {day}</span><span>AI Stylist</span></p></article>;
}

export default function StylistPage() {
  const [request, setRequest] = useState("Đi làm thanh lịch");
  const [weekly, setWeekly] = useState<WeeklyResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [eventId, setEventId] = useState("");

  useEffect(() => {
    api.listCalendarEvents({ limit: 50 }).then((result) => setEvents(result.items)).catch(() => undefined);
    api.getLatestWeeklyRecommendation().then((result) => {
      if (result.schedule.length) {
        setWeekly(result);
        cacheWeeklyRecommendation(result);
      }
    }).catch(() => undefined);
  }, []);

  async function generate(event?: FormEvent) {
    event?.preventDefault();
    setLoading(true); setError("");
    try {
      const result = await api.getWeeklyRecommendation({ latitude: 21.0285, longitude: 105.8542, prefer_dress: false, days: 7, styling_request: request.trim() || null, event_id: eventId || null });
      setWeekly(result);
      cacheWeeklyRecommendation(result);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không tạo được gợi ý.");
    } finally {
      setLoading(false);
    }
  }

  const outfits = weekly?.schedule?.filter((day) => day.outfit).map((day) => ({ day: day.day, outfit: day.outfit as Outfit })) ?? [];
  return <div className="content-page">
    <div className="stylist-header"><div><h1>Gợi ý phối đồ cho bạn</h1><p>Dựa trên tủ đồ, thời tiết và phong cách yêu thích</p></div></div>
    <form className="stylist-request" onSubmit={generate}><input value={request} onChange={(event) => setRequest(event.target.value)} placeholder="Ví dụ: Mai đi làm, tone sáng, không đi sneaker" /><select value={eventId} onChange={(event) => setEventId(event.target.value)} aria-label="Sự kiện lịch"><option value="">Không gắn sự kiện</option>{events.map((item) => <option key={item.id} value={item.id}>{item.title} · {new Date(item.start_at).toLocaleDateString("vi-VN")}</option>)}</select><button className="btn primary" disabled={loading} aria-busy={loading}>{loading ? "Đang phân tích…" : "Tạo gợi ý"}<Icon name="sparkle" size={16} /></button></form>
    <div className="tabs"><button className="active" type="button">Hằng ngày</button><button type="button" onClick={() => setRequest("Đi làm thanh lịch")}>Đi làm</button><button type="button" onClick={() => setRequest("Đi dự tiệc, tone sáng")}>Dự tiệc</button><button type="button" onClick={() => setRequest("Hẹn hò, nữ tính")}>Hẹn hò</button><button type="button" onClick={() => setRequest("Đi du lịch thoải mái")}>Du lịch</button><button className="outline" type="button">⚙ Tùy chỉnh</button></div>
    {error ? <div className="stylist-error"><p className="error-copy">{error}</p><button className="btn ghost" type="button" onClick={() => void generate()}>Thử lại</button></div> : null}
    {outfits.length ? <div className="outfit-grid">{outfits.slice(0, 8).map(({ outfit, day }) => <OutfitCard key={outfit.recommendation_id ?? day} outfit={outfit} day={day} />)}</div> : <div className={`stylist-empty${loading ? " is-loading" : ""}`} aria-live="polite"><Icon name="sparkle" size={28} /><h3>{loading ? "HerStyle AI đang phân tích tủ đồ…" : "Bắt đầu với một yêu cầu nhỏ"}</h3><p>{loading ? "Lần chạy đầu có thể mất khoảng một phút để AI chấm điểm các món đồ. Bạn cứ để trang mở, outfit sẽ tự hiện ở đây." : "Hãy nhập hoàn cảnh hoặc chọn một tab ở trên, AI sẽ chọn outfit từ chính tủ đồ của bạn."}</p><button className="btn primary" type="button" disabled={loading} onClick={() => void generate()}>{loading ? "Đang xử lý…" : "Tạo gợi ý đầu tiên"}</button></div>}
    {outfits.length ? <div className="center"><Link href="/planner" className="btn primary">Xem lịch phối đồ tuần</Link></div> : null}
  </div>;
}
