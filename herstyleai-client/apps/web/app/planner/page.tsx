"use client";

import { useCallback, useEffect, useState } from "react";
import { Icon } from "@/components/Icon";
import { ProtectedMediaImage } from "@/components/ProtectedMediaImage";
import { api, cacheWeeklyRecommendation, readCachedWeeklyRecommendation, resolveMediaUrl, ScheduleDay, WeeklyResponse, WardrobeItem } from "@/lib/api";
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

function DayOutfitDialog({ day, onClose, onRegenerate, regenerating }: { day: ScheduleDay; onClose: () => void; onRegenerate: () => void; regenerating: boolean }) {
  const items = Object.values(day.outfit?.items ?? {});
  return <div className="outfit-dialog-backdrop" role="presentation"><div className="outfit-dialog" role="dialog" aria-modal="true" aria-labelledby="outfit-dialog-title"><div className="outfit-dialog-head"><div><small>{dayDateLabel(day)} · Ngày {day.day}</small><h2 id="outfit-dialog-title">{day.outfit ? outfitTitle(day.outfit.structure, items.length) : "Gợi ý phối đồ"}</h2></div><button className="icon-btn" type="button" onClick={onClose} aria-label="Đóng">×</button></div><p className="outfit-dialog-caption">Các món đồ được phối trong ngày này</p><div className="outfit-item-list">{items.map((item) => <article key={item.item_id}><div className="outfit-item-image"><RecommendationImage item={item} /></div><div><strong>{itemTitle(item)}</strong><span>{categoryLabel(item.category)} · {colorLabel(item.color)} · {patternLabel(item.pattern)}</span></div></article>)}</div><div className="outfit-dialog-actions"><button className="btn primary" type="button" onClick={onRegenerate} disabled={regenerating}>{regenerating ? "Đang tạo outfit khác…" : "Không ưng? Gen outfit khác"}<Icon name="sparkle" size={16} /></button></div></div></div>;
}

export default function PlannerPage() {
  const [weekly, setWeekly] = useState<WeeklyResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedDay, setSelectedDay] = useState<ScheduleDay | null>(null);
  const [variation, setVariation] = useState(0);
  const [regeneratingDay, setRegeneratingDay] = useState<number | null>(null);

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

  async function generate() {
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
      });
      cacheWeeklyRecommendation(result);
      setWeekly(result);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể tạo lịch phối đồ lúc này.");
    } finally {
      setLoading(false);
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
        const updated = {
          ...current,
          generation_id: result.generation_id ?? current.generation_id,
          schedule: current.schedule.map((item) => item.day === day.day ? replacement : item),
        };
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

  const days = weekly?.schedule ?? [];
  return <div className="content-page planner-page">
    <div className="page-heading"><div><h1>Lịch phối đồ tuần này</h1><p>AI đã tạo lịch phối đồ dựa trên thời tiết và tủ đồ của bạn</p></div><button className="btn primary" type="button" onClick={() => void generate()} disabled={loading} aria-busy={loading}>{loading ? "Đang đổi bộ…" : "Đổi bộ phối"}<Icon name="sparkle" size={16} /></button></div>
    {loading ? <div className="empty-state"><h3>Đang tải lịch phối đồ…</h3></div> : error ? <div className="planner-error"><Icon name="sparkle" size={22} /><div><strong>Chưa tạo được lịch tuần</strong><p>{error}</p></div><button className="btn ghost" type="button" onClick={loadWeekly}>Thử lại</button></div> : <div className="week-grid">{days.map((day, index) => <DayCard key={day.day} day={day} active={index === 0} onOpen={() => setSelectedDay(day)} />)}</div>}
    {selectedDay ? <DayOutfitDialog day={selectedDay} onClose={() => setSelectedDay(null)} onRegenerate={() => void regenerateDay(selectedDay)} regenerating={regeneratingDay === selectedDay.day} /> : null}
  </div>;
}
