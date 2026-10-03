"use client";

import { FormEvent, useEffect, useState } from "react";
import { Icon } from "@/components/Icon";
import { api, CalendarEvent } from "@/lib/api";

function inputDate(value: Date) {
  const local = new Date(value.getTime() - value.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 16);
}

function localInputToIso(value: string) {
  const date = new Date(value);
  const offsetMinutes = -date.getTimezoneOffset();
  const sign = offsetMinutes >= 0 ? "+" : "-";
  const hours = String(Math.floor(Math.abs(offsetMinutes) / 60)).padStart(2, "0");
  const minutes = String(Math.abs(offsetMinutes) % 60).padStart(2, "0");
  return `${value}:00${sign}${hours}:${minutes}`;
}

export default function CalendarPage() {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [startAt, setStartAt] = useState("");
  const [endAt, setEndAt] = useState("");
  const [location, setLocation] = useState("");
  const [eventType, setEventType] = useState("meeting");
  const [stylingContext, setStylingContext] = useState('{"dress_code":"smart casual"}');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  function fetchEvents() {
    const from = new Date();
    const to = new Date(Date.now() + 90 * 24 * 60 * 60 * 1000);
    return api.listCalendarEvents({ from: from.toISOString(), to: to.toISOString(), limit: 200 })
      .then((result) => setEvents(result.items))
      .catch((reason) => setError(reason instanceof Error ? reason.message : "Không thể tải lịch sự kiện."))
      .finally(() => setLoading(false));
  }

  function loadEvents() {
    setLoading(true);
    void fetchEvents();
  }

  useEffect(() => {
    queueMicrotask(() => setStartAt((current) => current || inputDate(new Date(Date.now() + 60 * 60 * 1000))));
    void fetchEvents();
  }, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true); setError("");
    try {
      const parsedContext = stylingContext.trim() ? JSON.parse(stylingContext) as Record<string, unknown> : null;
      if (parsedContext !== null && (typeof parsedContext !== "object" || Array.isArray(parsedContext))) throw new Error("Styling context phải là JSON object.");
      const created = await api.createCalendarEvent({
        title: title.trim(),
        description: description.trim() || null,
        start_at: localInputToIso(startAt),
        end_at: endAt ? localInputToIso(endAt) : null,
        location: location.trim() || null,
        event_type: eventType.trim() || null,
        styling_context: parsedContext,
      });
      setEvents((current) => [...current, created].sort((a, b) => a.start_at.localeCompare(b.start_at)));
      setTitle(""); setDescription(""); setLocation(""); setEndAt("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể tạo sự kiện.");
    } finally {
      setSaving(false);
    }
  }

  async function rename(item: CalendarEvent) {
    const nextTitle = window.prompt("Tên sự kiện", item.title);
    if (nextTitle === null || !nextTitle.trim()) return;
    try {
      const updated = await api.updateCalendarEvent(item.id, { title: nextTitle.trim() });
      setEvents((current) => current.map((value) => value.id === item.id ? updated : value));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể cập nhật sự kiện.");
    }
  }

  async function remove(item: CalendarEvent) {
    if (!window.confirm(`Xóa sự kiện “${item.title}”?`)) return;
    try {
      await api.deleteCalendarEvent(item.id);
      setEvents((current) => current.filter((value) => value.id !== item.id));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể xóa sự kiện.");
    }
  }

  return <div className="content-page">
    <div className="page-heading"><div><h1>Lịch sự kiện</h1><p>Thêm hoàn cảnh để AI chọn outfit phù hợp cho từng dịp.</p></div></div>
    <div className="calendar-layout"><form className="profile-card event-form" onSubmit={submit}><h2>Thêm sự kiện</h2><label><span>Tiêu đề</span><input value={title} onChange={(event) => setTitle(event.target.value)} required maxLength={200} placeholder="Ví dụ: Thuyết trình với khách hàng" /></label><label><span>Mô tả</span><textarea value={description} onChange={(event) => setDescription(event.target.value)} rows={3} /></label><div className="form-grid"><label><span>Bắt đầu</span><input type="datetime-local" value={startAt} onChange={(event) => setStartAt(event.target.value)} required /></label><label><span>Kết thúc</span><input type="datetime-local" value={endAt} onChange={(event) => setEndAt(event.target.value)} /></label></div><div className="form-grid"><label><span>Địa điểm</span><input value={location} onChange={(event) => setLocation(event.target.value)} placeholder="Văn phòng" /></label><label><span>Loại sự kiện</span><input value={eventType} onChange={(event) => setEventType(event.target.value)} placeholder="meeting" /></label></div><label><span>Styling context JSON</span><textarea value={stylingContext} onChange={(event) => setStylingContext(event.target.value)} rows={4} /></label>{error ? <p className="error-copy">{error}</p> : null}<button className="btn primary" disabled={saving}>{saving ? "Đang lưu…" : "Thêm vào lịch"}</button></form><section className="event-list"><div className="section-heading"><h2>90 ngày sắp tới</h2><button className="btn ghost" type="button" onClick={loadEvents}>Làm mới</button></div>{loading ? <div className="empty-state"><h3>Đang tải lịch…</h3></div> : events.length === 0 ? <div className="empty-state"><Icon name="calendar" size={28} /><h3>Chưa có sự kiện</h3><p>Thêm một dịp quan trọng để bắt đầu.</p></div> : events.map((item) => <article className="event-card" key={item.id}><div className="event-date"><strong>{new Date(item.start_at).toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit" })}</strong><span>{new Date(item.start_at).toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" })}</span></div><div className="event-main"><h3>{item.title}</h3><p>{item.event_type ?? "Sự kiện"}{item.location ? ` · ${item.location}` : ""}</p>{item.description ? <small>{item.description}</small> : null}<div className="event-actions"><button className="text-link" type="button" onClick={() => void rename(item)}>Đổi tên</button><button className="text-link danger-link" type="button" onClick={() => void remove(item)}>Xóa</button></div></div></article>)}</section></div>
  </div>;
}
