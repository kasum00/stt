"use client";

import { useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import PageHeader from "@/components/PageHeader";
import Icon from "@/components/Icon";
import { api, cacheWeeklyRecommendation, resolveMediaUrl, type CalendarEvent, type ScheduleDay, type WardrobeItem, type WeeklyResponse } from "@/lib/api";
import { ProtectedMediaImage } from "@/components/ProtectedMediaImage";
import { categoryLabel, colorLabel, outfitTitle, patternLabel, titleCase } from "@/lib/format";

function dateLabel(index: number) {
  const date = new Date();
  date.setDate(date.getDate() + index);
  return new Intl.DateTimeFormat("vi-VN", { weekday: "short", day: "numeric", month: "numeric" }).format(date);
}

function imageSources(item: WardrobeItem) {
  const values = [item.transparent_image_url, item.transparent_url, item.model_url, item.image_url, item.image_path]
    .filter((value): value is string => typeof value === "string" && value.length > 0)
    .map((value) => resolveMediaUrl(value))
    .filter((value): value is string => Boolean(value));
  return Array.from(new Set(values));
}

function fallbackImageFor(item: WardrobeItem) {
  const label = `${item.subcategory ?? ""} ${item.category ?? ""}`.toLowerCase();
  if (label.includes("heel") || label.includes("giày") || label.includes("shoe")) return "/assets/heels.png";
  if (label.includes("quần") || label.includes("pant")) return "/assets/pants-black.png";
  return "/assets/shirt-white.png";
}

function itemTitle(item: WardrobeItem) {
  return titleCase(item.subcategory ?? item.category ?? "Món đồ");
}

function dayDateLabel(day: ScheduleDay) {
  return day.weather?.date
    ? new Date(`${day.weather.date}T00:00:00`).toLocaleDateString("vi-VN", { weekday: "short", day: "numeric", month: "numeric" })
    : `Ngày ${day.day}`;
}

function RecommendationImage({ item }: { item: WardrobeItem }) {
  const sources = imageSources(item);
  const fallback = fallbackImageFor(item);
  const Candidate = ({ index }: { index: number }) => {
    const src = sources[index];
    if (!src) return <img src={fallback} alt={itemTitle(item)} />;
    return <ProtectedMediaImage src={src} alt={itemTitle(item)} fallback={<Candidate index={index + 1} />} />;
  };
  return <Candidate index={0} />;
}

function DayOutfitDialog({ day, onClose, onRegenerate, regenerating }: { day: ScheduleDay; onClose: () => void; onRegenerate: () => void; regenerating: boolean }) {
  const items = Object.values(day.outfit?.items ?? {});
  return <div className="outfit-dialog-backdrop" role="presentation" onClick={onClose}>
    <div className="outfit-dialog" role="dialog" aria-modal="true" aria-labelledby="calendar-outfit-dialog-title" onClick={(event) => event.stopPropagation()}>
      <div className="outfit-dialog-head">
        <div><small>{dayDateLabel(day)} · Ngày {day.day}</small><h2 id="calendar-outfit-dialog-title">{day.outfit ? outfitTitle(day.outfit.structure, items.length) : "Gợi ý phối đồ"}</h2></div>
        <button className="icon-btn" type="button" onClick={onClose} aria-label="Đóng">×</button>
      </div>
      <p className="outfit-dialog-caption">Các món đồ được phối trong ngày này</p>
      <div className="outfit-item-list">{items.map((item) => <article key={item.item_id}><div className="outfit-item-image"><RecommendationImage item={item} /></div><div><strong>{itemTitle(item)}</strong><span>{categoryLabel(item.category)} · {colorLabel(item.color)} · {patternLabel(item.pattern)}</span></div></article>)}</div>
      <div className="outfit-dialog-actions"><button className="button button-primary" type="button" onClick={onRegenerate} disabled={regenerating}>{regenerating ? "Đang tạo outfit khác…" : "Không ưng? Gen outfit khác"}<Icon name="sparkle" size={16} /></button></div>
    </div>
  </div>;
}

export default function Calendar() {
  const [weekly, setWeekly] = useState<WeeklyResponse | null>(null);
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");
  const [selectedDay, setSelectedDay] = useState<ScheduleDay | null>(null);
  const [variation, setVariation] = useState(0);
  const [regeneratingDay, setRegeneratingDay] = useState<number | null>(null);

  async function load() {
    setLoading(true);
    try {
      const [latest, eventResult] = await Promise.all([api.getLatestWeeklyRecommendation(), api.listCalendarEvents({ limit: 20 })]);
      setWeekly(latest);
      setEvents(eventResult.items ?? []);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Chưa có lịch phối đồ.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void Promise.resolve().then(load); }, []);

  async function generate() {
    const nextVariation = variation + 1;
    setVariation(nextVariation);
    setGenerating(true);
    setError("");
    try {
      const result = await api.getWeeklyRecommendation({ latitude: 21.0285, longitude: 105.8542, prefer_dress: false, days: 7, variation: nextVariation });
      setWeekly(result);
      cacheWeeklyRecommendation(result);
      sessionStorage.setItem("herstyleai:last-outfit", JSON.stringify(result));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể tạo lịch phối đồ.");
    } finally {
      setGenerating(false);
    }
  }

  async function regenerateDay(day: ScheduleDay) {
    const nextVariation = variation + 1;
    setVariation(nextVariation);
    setRegeneratingDay(day.day);
    setError("");
    try {
      const result = await api.regenerateWeeklyDay({
        latitude: 21.0285,
        longitude: 105.8542,
        prefer_dress: false,
        days: 7,
        variation: nextVariation,
        regenerate_day: day.day,
        generation_id: weekly?.generation_id ?? null,
      });
      const replacement = result.schedule.find((item) => item.day === day.day);
      if (!replacement) throw new Error("Không tạo được outfit thay thế cho ngày này.");
      setWeekly((current) => {
        if (!current) return current;
        const updated = { ...current, generation_id: result.generation_id ?? current.generation_id, schedule: current.schedule.map((item) => item.day === day.day ? replacement : item) };
        cacheWeeklyRecommendation(updated);
        return updated;
      });
      setSelectedDay(replacement);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể tạo outfit khác cho ngày này.");
    } finally {
      setRegeneratingDay(null);
    }
  }

  return (
    <AppShell>
      <PageHeader title="Kế hoạch mặc đồ tuần này" subtitle="Lịch phối đồ được lưu theo tài khoản của bạn." action={<button type="button" className="button button-primary" onClick={() => void generate()} disabled={generating}><Icon name="sparkle" size={17} /> {generating ? "Đang tạo…" : "Tạo lịch tuần bằng AI"}</button>} />
      {loading ? <div className="empty-state">Đang tải lịch phối đồ…</div> : error && !weekly ? <div className="empty-state"><p>{error}</p><button type="button" className="button button-primary" onClick={() => void generate()}>Tạo lịch mới</button></div> : <>
        <div className="calendar-week">{(weekly?.schedule ?? []).map((day, index) => {
          const items = Object.entries(day.outfit?.items ?? {});
          return <article className={`calendar-day ${index === 0 ? "active" : ""}`} key={day.day}>
            <h3>{dateLabel(index)}</h3>
            <span>Ngày {day.day}</span>
            <button className="calendar-outfit-trigger" type="button" onClick={() => setSelectedDay(day)} disabled={!items.length} aria-label={`Xem chi tiết outfit ${dayDateLabel(day)}`}>
              <div className="calendar-outfit">
              {items.length ? items.map(([slot, item], itemIndex) => {
                return <div className="calendar-item" key={`${day.day}-${slot}-${itemIndex}`}>
                  <RecommendationImage item={item} />
                  <span>{itemTitle(item)}</span>
                </div>;
              }) : <div className="calendar-empty-outfit">Chưa có outfit</div>}
              </div>
            </button>
            <small>☁ {day.weather?.temperature_c ?? day.weather?.temperature ?? "—"}°C</small>
            <button className="calendar-detail-button" type="button" onClick={() => setSelectedDay(day)} disabled={!items.length}>Xem chi tiết outfit →</button>
          </article>;
        })}{!weekly?.schedule?.length && <article className="calendar-day add"><b>＋</b><span>Chưa có lịch</span></article>}</div>
        <section className="events"><div className="panel-heading"><h2>Sự kiện trong tuần</h2><span>{events.length} sự kiện</span></div><div className="events-grid">{events.length ? events.map((event) => <article key={event.id}><div className="event-icon green"><Icon name="calendar" size={17} /></div><div><small>{new Date(event.start_at).toLocaleString("vi-VN")}</small><strong>{event.title}</strong><span>{event.event_type ?? "Sự kiện"}</span></div></article>) : <p className="empty-state">Chưa có sự kiện nào trong lịch.</p>}</div></section>
      </>}
      {error && weekly && <p className="form-error">{error}</p>}
      {selectedDay ? <DayOutfitDialog day={selectedDay} onClose={() => setSelectedDay(null)} onRegenerate={() => void regenerateDay(selectedDay)} regenerating={regeneratingDay === selectedDay.day} /> : null}
    </AppShell>
  );
}
