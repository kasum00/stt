"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import AppShell from "@/components/AppShell";
import PageHeader from "@/components/PageHeader";
import Icon from "@/components/Icon";
import { api, resolveMediaUrl, type WeeklyResponse } from "@/lib/api";
import { ProtectedMediaImage } from "@/components/ProtectedMediaImage";

export default function Result() {
  const router = useRouter();
  const [weekly, setWeekly] = useState<WeeklyResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    let active = true;
    const cached = sessionStorage.getItem("herstyleai:last-outfit");
    const load = cached ? Promise.resolve(JSON.parse(cached) as WeeklyResponse) : api.getLatestWeeklyRecommendation();
    void load.then((result) => { if (active) setWeekly(result); }).catch((reason) => { if (active) setMessage(reason instanceof Error ? reason.message : "Chưa có gợi ý outfit."); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const outfit = weekly?.schedule?.[0]?.outfit ?? null;
  const items = useMemo(() => Object.entries(outfit?.items ?? {}), [outfit]);
  const score = outfit?.compatibility_score ?? outfit?.score;

  async function saveOutfit() {
    const id = outfit?.recommendation_id;
    if (!id) { setMessage("Gợi ý này chưa có mã để lưu."); return; }
    setSaving(true);
    try {
      await api.saveOutfit(id);
      await api.sendFeedback({ event_type: "outfit_saved", recommendation_id: id, structure: outfit.structure, items: Object.fromEntries(items.map(([slot, item]) => [slot, item.item_id])) });
      setMessage("Đã lưu outfit vào mục Đã lưu.");
    } catch (reason) {
      setMessage(reason instanceof Error ? reason.message : "Không thể lưu outfit.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <AppShell><div className="empty-state">Đang tải gợi ý outfit…</div></AppShell>;
  if (!outfit) return <AppShell><PageHeader title="Gợi ý phối đồ cho bạn" subtitle="Chưa có dữ liệu outfit." /><div className="empty-state"><p>{message || "Hãy tạo một gợi ý mới từ tủ đồ của bạn."}</p><Link className="button button-primary" href="/recommend">Tạo gợi ý mới</Link></div></AppShell>;

  return (
    <AppShell>
      <PageHeader title="Gợi ý phối đồ cho bạn" subtitle="Dựa trên tủ đồ, phong cách và thời tiết hôm nay." />
      <section className="result-layout">
        <div className="result-main">
          <div className="result-title"><h2>{outfit.structure ?? "Outfit được cá nhân hóa cho bạn"}</h2><span className="match">● {typeof score === "number" ? `${Math.round(score * (score <= 1 ? 100 : 1))}%` : "AI phù hợp"}</span></div>
          <div className="outfit-items">{items.map(([slot, item]) => <article key={slot}><ProtectedMediaImage src={resolveMediaUrl(item.transparent_image_url ?? item.transparent_url ?? item.image_url ?? item.image_path)} alt={slot} fallback={<img src="/assets/shirt-white.png" alt={slot} />} /><strong>{item.subcategory ?? item.category ?? slot}</strong><span>{item.color ?? ""} {item.pattern ? `· ${item.pattern}` : ""}</span></article>)}</div>
        </div>
        <aside className="reason-box"><h2>Lý do gợi ý</h2><ul>{(outfit.explanation?.reasons ?? ["Phù hợp với các món đồ trong tủ", "Cân bằng theo thời tiết và hoàn cảnh", "Các item có màu sắc hài hòa"]).map((reason) => <li key={reason}>✓ {reason}</li>)}</ul></aside>
      </section>
      {message && <p className="form-success">{message}</p>}
      <div className="result-buttons"><button type="button" className="button button-white" onClick={() => void saveOutfit()} disabled={saving}><Icon name="heart" size={16} /> {saving ? "Đang lưu…" : "Lưu outfit"}</button><button type="button" className="button button-white" onClick={() => router.push("/recommend")}>Thay item</button><Link href="/recommend" className="button button-white"><Icon name="refresh" size={16} /> Tạo lại</Link><Link href="/calendar" className="button button-primary">Mặc hôm nay</Link></div>
    </AppShell>
  );
}
