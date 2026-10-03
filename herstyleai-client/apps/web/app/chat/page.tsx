"use client";

/* eslint-disable @next/next/no-img-element */

import { FormEvent, useState } from "react";
import { Icon } from "@/components/Icon";
import { api, Outfit, resolveMediaUrl, WeeklyResponse } from "@/lib/api";
import { outfitTitle } from "@/lib/format";

function imageFor(item: Record<string, unknown>) {
  return resolveMediaUrl([item.transparent_image_url, item.transparent_url, item.model_url, item.image_url, item.image_path].find((value): value is string => typeof value === "string"));
}

export default function ChatPage() {
  const [text, setText] = useState("");
  const [messages, setMessages] = useState<string[]>([]);
  const [weekly, setWeekly] = useState<WeeklyResponse | null>(null);
  const [loading, setLoading] = useState(false);

  async function send(event: FormEvent) {
    event.preventDefault();
    const message = text.trim();
    if (!message) return;
    setMessages((current) => [...current, message]); setText(""); setLoading(true);
    try {
      const result = await api.getWeeklyRecommendation({ latitude: 21.0285, longitude: 105.8542, prefer_dress: false, days: 1, styling_request: message });
      setWeekly(result);
    } finally {
      setLoading(false);
    }
  }

  const outfit = weekly?.schedule?.[0]?.outfit as Outfit | undefined;
  return <div className="content-page chat-page">
    <div className="page-heading"><div><h1>Chat với HerStyle AI</h1><p>Hỏi bất cứ điều gì về thời trang, phối đồ, phong cách hay chăm sóc tủ đồ của bạn</p></div></div>
    <div className="chat-layout">
      <aside className="conversation-list"><button className="btn primary full" type="button" onClick={() => { setMessages([]); setWeekly(null); }}>+ Cuộc trò chuyện mới</button>{["Gợi ý outfit đi phỏng vấn", "Phối đồ đi Đà Lạt", "Trang phục mùa đông", "Phụ kiện phù hợp", "Chăm sóc quần áo"].map((label, index) => <button key={label} className={index === 0 ? "active" : ""} type="button" onClick={() => setText(label)}><Icon name="chat" size={16} /><div><strong>{label}</strong><span>{index === 0 ? "Hôm nay" : "Gần đây"}</span></div></button>)}</aside>
      <section className="chat-main"><div className="chat-topline"><span>HerStyle AI · Trợ lý phong cách</span><div className="weather-inline"><Icon name="sun" size={18} /> Hà Nội · 28°C</div></div><div className="chat-messages">{messages.map((message, index) => <div className="bubble user" key={`${message}-${index}`}>{message}</div>)}{!messages.length ? <div className="bubble ai"><span className="ai-badge">AI</span><p>Chào bạn! Hãy nói cho mình biết bạn sẽ đi đâu, muốn mặc màu gì hoặc món đồ nào cần phối nhé.</p></div> : null}{loading ? <div className="bubble ai"><span className="ai-badge">AI</span><p>HerStyle AI đang xem tủ đồ của bạn…</p></div> : null}{!loading && outfit ? <div className="bubble ai"><span className="ai-badge">AI</span><p>Mình gợi ý <strong>{outfitTitle(outfit.structure, Object.keys(outfit.items ?? {}).length)}</strong> cho bạn:</p><div className="chat-outfit">{Object.values(outfit.items ?? {}).map((item) => imageFor(item) ? <img key={item.item_id} src={imageFor(item) ?? undefined} alt="" /> : null)}</div><button className="text-link" type="button">Xem chi tiết outfit này</button></div> : null}</div><form className="chat-input" onSubmit={send}><input value={text} onChange={(event) => setText(event.target.value)} placeholder="Nhập câu hỏi của bạn..." /><button aria-label="Gửi"><Icon name="send" size={19} /></button></form></section>
    </div>
  </div>;
}
