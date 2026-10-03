"use client";

/* eslint-disable @next/next/no-img-element */

import Link from "next/link";
import { useEffect, useState } from "react";
import { Icon } from "@/components/Icon";
import { api, Outfit, resolveMediaUrl } from "@/lib/api";
import { categoryLabel, colorLabel, outfitTitle, patternLabel, titleCase } from "@/lib/format";

function imageFor(item: Record<string, unknown>) {
  return resolveMediaUrl([item.transparent_image_url, item.transparent_url, item.model_url, item.image_url, item.image_path].find((value): value is string => typeof value === "string"));
}

export default function OutfitPage() {
  const [outfit, setOutfit] = useState<Outfit | null>(null);
  const [saved, setSaved] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    api.getWeeklyRecommendation({ latitude: 21.0285, longitude: 105.8542, prefer_dress: false, days: 1 })
      .then((result) => setOutfit(result.schedule?.[0]?.outfit ?? null))
      .catch(() => undefined);
  }, []);

  const entries = Object.entries(outfit?.items ?? {});
  const gallery = entries.map(([, item]) => imageFor(item)).filter((value): value is string => Boolean(value));

  async function sendFeedback(eventType: "outfit_saved" | "outfit_liked" | "outfit_disliked") {
    if (!outfit?.recommendation_id) return;
    try {
      if (eventType === "outfit_saved") await api.saveOutfit(outfit.recommendation_id);
      await api.sendFeedback({ event_type: eventType, recommendation_id: outfit.recommendation_id, structure: outfit.structure, items: Object.fromEntries(entries.map(([slot, item]) => [slot, item.item_id])) });
      setSaved(eventType === "outfit_saved" ? true : saved);
      setMessage(eventType === "outfit_saved" ? "Outfit đã được lưu." : eventType === "outfit_liked" ? "Đã ghi nhận bạn thích outfit này." : "Đã ghi nhận phản hồi của bạn.");
    } catch (reason) {
      setMessage(reason instanceof Error ? reason.message : "Không thể gửi phản hồi.");
    }
  }

  return <div className="content-page outfit-detail">
    {!outfit ? <div className="empty-state"><Icon name="sparkle" size={30} /><h3>Đang chuẩn bị outfit cho bạn…</h3><p>HerStyle AI đang chọn một bộ từ chính tủ đồ.</p></div> : <><div className="outfit-gallery"><div className="thumbs">{gallery.map((src) => <img src={src} alt="" key={src} />)}</div>{gallery[0] ? <img className="outfit-main-img" src={gallery[0]} alt="Outfit được gợi ý" /> : <div className="outfit-main-img" />}</div><section className="outfit-info"><div className="page-heading"><div><h1>{outfitTitle(outfit.structure, entries.length)}</h1><p>Một set đồ được chọn từ tủ đồ, thời tiết và phong cách của bạn.</p></div><button className="heart-btn large" type="button" onClick={() => void sendFeedback("outfit_saved")}><Icon name="heart" /></button></div><div className="tag-row"><span>AI Stylist</span><span>{outfit.ranking_method ?? "Phối theo tủ đồ"}</span><span>{saved ? "Đã lưu" : "Gợi ý hôm nay"}</span></div>{message ? <p className="success-copy">{message}</p> : null}<h3>Các item trong outfit</h3><div className="outfit-items">{entries.map(([slot, item]) => <article key={item.item_id}>{imageFor(item) ? <img src={imageFor(item) ?? undefined} alt={titleCase(item.subcategory ?? item.category)} /> : null}<span>{categoryLabel(slot)} · {colorLabel(item.color)} · {patternLabel(item.pattern)}</span></article>)}</div><div className="occasion-line"><strong>Vì sao phù hợp</strong>{(outfit.explanation?.reasons ?? ["Cân bằng màu sắc và kiểu dáng", "Được chọn từ chính tủ đồ của bạn"]).slice(0, 3).map((reason) => <span key={reason}>{reason}</span>)}</div><div className="stack-actions horizontal"><button className="btn primary" type="button" onClick={() => void sendFeedback("outfit_saved")}>Lưu outfit</button><button className="btn ghost" type="button" onClick={() => void sendFeedback("outfit_liked")}>Thích</button><button className="btn white" type="button" onClick={() => void sendFeedback("outfit_disliked")}>Chưa hợp</button><Link href="/stylist" className="btn ghost">Thử gợi ý khác</Link></div></section></>}
  </div>;
}
