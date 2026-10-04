"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { Icon } from "@/components/Icon";
import { ProtectedMediaImage } from "@/components/ProtectedMediaImage";
import { api, cacheWeeklyRecommendation, CalendarEvent, readCachedWeeklyRecommendation, resolveMediaUrl, ScheduleDay, WeeklyResponse, WardrobeItem } from "@/lib/api";
import { categoryLabel, colorLabel, outfitTitle, patternLabel, temperatureLabel, titleCase } from "@/lib/format";

function imageFor(item: WardrobeItem) {
  return resolveMediaUrl([item.transparent_image_url, item.transparent_url, item.model_url, item.image_url, item.image_path].find((value): value is string => typeof value === "string"));
}

function RecommendationImage({ item }: { item: WardrobeItem }) {
  const imagePath = imageFor(item);
  return <ProtectedMediaImage src={imagePath} alt="" fallback={<Icon name="shirt" size={17} />} />;
}

function dayDateLabel(day: ScheduleDay) {
  return day.weather?.date
    ? new Date(`${day.weather.date}T00:00:00`).toLocaleDateString("vi-VN", { weekday: "short", day: "numeric", month: "numeric" })
    : `Ngày ${day.day}`;
}

function itemTitle(item: WardrobeItem) {
  return titleCase(item.subcategory ?? item.category ?? "Món đồ");
}

function DayCard({ day, active, onOpen }: { day: ScheduleDay; active: boolean; onOpen: () => void }) {
  const items = Object.values(day.outfit?.items ?? {});
  return <article className={`day-card ${active ? "active" : ""}`}><strong>{dayDateLabel(day)}</strong><small>Ngày {day.day}</small><span>{day.request_applied ? "Theo yêu cầu" : day.available_structure ? "Tối ưu theo tủ đồ" : "Gợi ý tự động"}</span><div className="day-weather"><Icon name="sun" size={16} />{temperatureLabel(day.weather?.temperature ?? day.weather?.temperature_c)}</div><button className="day-card-items" type="button" onClick={onOpen} disabled={!items.length} aria-label={`Xem món đồ phối cho ${dayDateLabel(day)}`}>{items.slice(0, 3).map((item) => <div key={item.item_id}><RecommendationImage item={item} /></div>)}</button><b>{day.outfit ? outfitTitle(day.outfit.structure, items.length) : "Chưa có outfit"}</b></article>;
}

function DayOutfitDialog({ day, onClose }: { day: ScheduleDay; onClose: () => void }) {
  const items = Object.values(day.outfit?.items ?? {});
  return <div className="outfit-dialog-backdrop" role="presentation"><div className="outfit-dialog" role="dialog" aria-modal="true" aria-labelledby="outfit-dialog-title"><div className="outfit-dialog-head"><div><small>{dayDateLabel(day)} · Ngày {day.day}</small><h2 id="outfit-dialog-title">{day.outfit ? outfitTitle(day.outfit.structure, items.length) : "Gợi ý phối đồ"}</h2></div><button className="icon-btn" type="button" onClick={onClose} aria-label="Đóng">×</button></div><p className="outfit-dialog-caption">Các món đồ được phối trong ngày này</p><div className="outfit-item-list">{items.map((item) => <article key={item.item_id}><div className="outfit-item-image"><RecommendationImage item={item} /></div><div><strong>{itemTitle(item)}</strong><span>{categoryLabel(item.category)} · {colorLabel(item.color)} · {patternLabel(item.pattern)}</span></div></article>)}</div></div></div>;
}

export default function PlannerPage() {
  const [request, setRequest] = useState("Đi làm thanh lịch");
  const [weekly, setWeekly] = useState<WeeklyResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedDay, setSelectedDay] = useState<ScheduleDay | null>(null);
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [eventId, setEventId] = useState("");
  const [variation, setVariation] = useState(0);

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
    api.listCalendarEvents({ limit: 50 }).then((result) => setEvents(result.items)).catch(() => undefined);
    const timer = window.setTimeout(() => {
      api.getLatestWeeklyRecommendation().then((latest) => {
        if (latest.schedule.length) {
          cacheWeeklyRecommendation(latest);
          setWeekly(latest);
          setLoading(false);
          return;
        }
        const cached = readCachedWeeklyRecommendation();
        if (cached?.schedule.length) {
          setWeekly(cached);
          setLoading(false);
          return;
        }
        loadWeekly();
      }).catch(() => {
        const cached = readCachedWeeklyRecommendation();
        if (cached?.schedule.length) {
          setWeekly(cached);
          setLoading(false);
          return;
        }
        loadWeekly();
      });
    }, 0);
    return () => window.clearTimeout(timer);
  }, [loadWeekly]);

  async function generate(event?: FormEvent) {
    event?.preventDefault();
    const nextVariation = variation + 1;
    setVariation(nextVariation);
    setLoading(true);
    setError("");
    try {
      const result = await api.getWeeklyRecommendation({
        latitude: 21.0285,
        longitude: 105.8542,
        prefer_dress: false,
        days: 7,
        variation: nextVariation,
        styling_request: request.trim() || null,
        event_id: eventId || null,
      });
      cacheWeeklyRecommendation(result);
      setWeekly(result);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể tạo lịch phối đồ lúc này.");
    } finally {
      setLoading(false);
    }
  }

  const days = weekly?.schedule ?? [];
  return <div className="content-page">
    <div className="page-heading"><div><h1>Lịch phối đồ tuần này</h1><p>AI đã tạo lịch phối đồ dựa trên thời tiết và tủ đồ của bạn</p></div></div>
    <form className="stylist-request" onSubmit={generate}>
      <input value={request} onChange={(event) => setRequest(event.target.value)} placeholder="Ví dụ: Mai đi làm, tone sáng, không đi sneaker" aria-label="Yêu cầu phối đồ" />
      <select value={eventId} onChange={(event) => setEventId(event.target.value)} aria-label="Sự kiện lịch">
        <option value="">Không gắn sự kiện</option>
        {events.map((item) => <option key={item.id} value={item.id}>{item.title} · {new Date(item.start_at).toLocaleDateString("vi-VN")}</option>)}
      </select>
      <button className="btn primary" disabled={loading} aria-busy={loading}>{loading ? "Đang đổi bộ…" : weekly ? "Đổi bộ phối" : "Tạo lịch phối đồ"}<Icon name="sparkle" size={16} /></button>
    </form>
    <div className="tabs planner-tabs"><button className="active" type="button">Hằng ngày</button><button type="button" onClick={() => setRequest("Đi làm thanh lịch")}>Đi làm</button><button type="button" onClick={() => setRequest("Đi dự tiệc, tone sáng")}>Dự tiệc</button><button type="button" onClick={() => setRequest("Hẹn hò, nữ tính")}>Hẹn hò</button><button type="button" onClick={() => setRequest("Đi du lịch thoải mái")}>Du lịch</button></div>
    <div className="week-label">‹ <strong>7 ngày sắp tới</strong> ›</div>
    {loading ? <div className="empty-state"><h3>Đang tải lịch phối đồ…</h3></div> : error ? <div className="planner-error"><Icon name="sparkle" size={22} /><div><strong>Chưa tạo được lịch tuần</strong><p>{error}</p></div><button className="btn ghost" type="button" onClick={loadWeekly}>Thử lại</button></div> : <div className="week-grid">{days.map((day, index) => <DayCard key={day.day} day={day} active={index === 0} onOpen={() => setSelectedDay(day)} />)}</div>}
    {selectedDay ? <DayOutfitDialog day={selectedDay} onClose={() => setSelectedDay(null)} /> : null}
  </div>;
}
