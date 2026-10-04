"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Icon } from "@/components/Icon";
import { ProtectedMediaImage } from "@/components/ProtectedMediaImage";
import { api, cacheWeeklyRecommendation, readCachedWeeklyRecommendation, resolveMediaUrl, ScheduleDay, WeeklyResponse, WardrobeItem } from "@/lib/api";
import { outfitTitle, temperatureLabel } from "@/lib/format";

function imageFor(item: WardrobeItem) {
  return resolveMediaUrl([item.transparent_image_url, item.transparent_url, item.model_url, item.image_url, item.image_path].find((value): value is string => typeof value === "string"));
}

function RecommendationImage({ item }: { item: WardrobeItem }) {
  const imagePath = imageFor(item);
  return <ProtectedMediaImage src={imagePath} alt="" fallback={<Icon name="shirt" size={17} />} />;
}

function DayCard({ day, active }: { day: ScheduleDay; active: boolean }) {
  const items = Object.values(day.outfit?.items ?? {});
  const dateLabel = day.weather?.date
    ? new Date(`${day.weather.date}T00:00:00`).toLocaleDateString("vi-VN", { weekday: "short", day: "numeric", month: "numeric" })
    : `Ngày ${day.day}`;
  return <article className={`day-card ${active ? "active" : ""}`}><strong>{dateLabel}</strong><small>Ngày {day.day}</small><span>{day.request_applied ? "Theo yêu cầu" : day.available_structure ? "Tối ưu theo tủ đồ" : "Gợi ý tự động"}</span><div className="day-weather"><Icon name="sun" size={16} />{temperatureLabel(day.weather?.temperature ?? day.weather?.temperature_c)}</div><div className="day-card-items">{items.slice(0, 3).map((item) => <div key={item.item_id}><RecommendationImage item={item} /></div>)}</div><b>{day.outfit ? outfitTitle(day.outfit.structure, items.length) : "Chưa có outfit"}</b></article>;
}

export default function PlannerPage() {
  const [weekly, setWeekly] = useState<WeeklyResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadWeekly = useCallback(() => {
    setLoading(true);
    setError("");
    api.getWeeklyRecommendation({ latitude: 21.0285, longitude: 105.8542, prefer_dress: false, days: 7 }).then((result) => {
      cacheWeeklyRecommendation(result);
      setWeekly(result);
    }).catch((reason) => {
      setWeekly(null);
      setError(reason instanceof Error ? reason.message : "Không thể tạo lịch phối đồ lúc này.");
    }).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const cached = readCachedWeeklyRecommendation();
      if (cached?.schedule.length) {
        setWeekly(cached);
        setLoading(false);
        return;
      }
      loadWeekly();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [loadWeekly]);

  const days = weekly?.schedule ?? [];
  return <div className="content-page">
    <div className="page-heading"><div><h1>Lịch phối đồ tuần này</h1><p>AI đã tạo lịch phối đồ dựa trên thời tiết và tủ đồ của bạn</p></div><Link href="/stylist" className="btn ghost">Tạo lịch mới</Link></div>
    <div className="week-label">‹ <strong>7 ngày sắp tới</strong> ›</div>
    {loading ? <div className="empty-state"><h3>Đang tạo lịch phối đồ…</h3></div> : error ? <div className="planner-error"><Icon name="sparkle" size={22} /><div><strong>Chưa tạo được lịch tuần</strong><p>{error}</p></div><button className="btn ghost" type="button" onClick={loadWeekly}>Thử lại</button></div> : <div className="week-grid">{days.map((day, index) => <DayCard key={day.day} day={day} active={index === 0} />)}</div>}
    <section className="accessory-strip"><h3>Gợi ý phụ kiện theo thời tiết tuần này</h3><div><article><Icon name="sun" size={22} /><span>Ưu tiên lớp nhẹ, dễ cởi khi trời ấm.</span></article><article><Icon name="calendar" size={22} /><span>Lịch được sắp theo cấu trúc outfit đa dạng.</span></article><article><Icon name="sparkle" size={22} /><span>Phản hồi của bạn sẽ giúp gợi ý tốt hơn.</span></article></div></section>
  </div>;
}
