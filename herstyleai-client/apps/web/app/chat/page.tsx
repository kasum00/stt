"use client";

import { FormEvent, useMemo, useState } from "react";
import AppShell from "@/components/AppShell";
import Icon from "@/components/Icon";
import { api, resolveMediaUrl, type Outfit } from "@/lib/api";
import { ProtectedMediaImage } from "@/components/ProtectedMediaImage";

type Message = { role: "user" | "ai"; text: string; outfit?: Outfit | null };

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([{ role: "ai", text: "Chào bạn! Hãy nói cho mình biết hoàn cảnh hoặc món đồ bạn muốn phối, mình sẽ lấy dữ liệu từ tủ đồ để gợi ý." }]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const latestOutfit = useMemo(() => [...messages].reverse().find((message) => message.outfit)?.outfit ?? null, [messages]);

  async function send(event?: FormEvent) {
    event?.preventDefault();
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    setMessages((current) => [...current, { role: "user", text }]);
    setLoading(true);
    try {
      const result = await api.getWeeklyRecommendation({ latitude: 21.0285, longitude: 105.8542, prefer_dress: false, days: 1, styling_request: text });
      const outfit = result.schedule?.[0]?.outfit ?? null;
      setMessages((current) => [...current, { role: "ai", text: outfit ? "Mình đã chọn một outfit từ tủ đồ phù hợp với yêu cầu của bạn." : "Mình chưa tìm thấy outfit phù hợp trong tủ đồ.", outfit }]);
    } catch (reason) {
      setMessages((current) => [...current, { role: "ai", text: reason instanceof Error ? reason.message : "Không thể kết nối AI Stylist." }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell>
      <section className="chat-screen">
        <header className="chat-head"><div className="ai-badge"><Icon name="sparkle" /></div><div><h1>HerStyle AI Stylist</h1><p><i /> Online · Kết nối tủ đồ của bạn</p></div></header>
        <div className="messages">{messages.map((message, index) => <div className={`msg ${message.role}`} key={`${message.role}-${index}`}>{message.role === "ai" && <div className="ai-small"><Icon name="sparkle" size={16} /></div>}<div className="bubble">{message.text}{message.outfit && <div className="chat-outfit"><div className="chat-images">{Object.entries(message.outfit.items ?? {}).slice(0, 4).map(([slot, item]) => <ProtectedMediaImage key={slot} src={resolveMediaUrl(item.transparent_image_url ?? item.transparent_url ?? item.image_url ?? item.image_path)} alt={slot} fallback={<img src="/assets/shirt-white.png" alt={slot} />} />)}</div><strong>{message.outfit.structure ?? "Outfit đề xuất"}</strong><span>{message.outfit.compatibility_score ? `${Math.round(message.outfit.compatibility_score * 100)}% phù hợp` : "Đã chọn từ tủ đồ"}</span></div>}</div></div>)}</div>
        <div className="suggested-prompts"><button type="button" onClick={() => { setInput("Phối đồ đi làm"); }}>Phối đồ đi làm</button><button type="button" onClick={() => { setInput("Outfit thuyết trình"); }}>Outfit thuyết trình</button><button type="button" onClick={() => { setInput("Chọn màu phù hợp"); }}>Chọn màu phù hợp</button></div>
        <form className="chat-input" onSubmit={send}><input value={input} onChange={(event) => setInput(event.target.value)} placeholder="Hỏi HerStyle AI bất cứ điều gì về phong cách..." /><button type="submit" disabled={loading} aria-label="Gửi">{loading ? "…" : "→"}</button></form>
        {latestOutfit && <p className="chat-status">Outfit trên được tạo từ tủ đồ hiện tại của bạn.</p>}
      </section>
    </AppShell>
  );
}
