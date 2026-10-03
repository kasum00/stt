"use client";

/* eslint-disable @next/next/no-img-element */

import Link from "next/link";
import { useEffect, useState } from "react";
import { Icon } from "@/components/Icon";
import { api, resolveMediaUrl, SavedOutfit } from "@/lib/api";

function snapshotImages(snapshot: Record<string, unknown>) {
  const items = snapshot.items;
  if (!items || typeof items !== "object" || Array.isArray(items)) return [];
  return Object.values(items as Record<string, unknown>).map((item) => {
    if (!item || typeof item !== "object" || Array.isArray(item)) return null;
    const value = item as Record<string, unknown>;
    return resolveMediaUrl([value.transparent_image_url, value.transparent_url, value.model_url, value.image_url, value.image_path].find((candidate): candidate is string => typeof candidate === "string"));
  }).filter((value): value is string => Boolean(value));
}

export default function SavedOutfitsPage() {
  const [items, setItems] = useState<SavedOutfit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  function fetchSavedOutfits() {
    return api.listSavedOutfits().then((result) => setItems(result.items)).catch((reason) => setError(reason instanceof Error ? reason.message : "Không thể tải outfit đã lưu.")).finally(() => setLoading(false));
  }

  function load() {
    setLoading(true);
    void fetchSavedOutfits();
  }

  useEffect(() => { void fetchSavedOutfits(); }, []);

  async function rename(item: SavedOutfit) {
    const title = window.prompt("Tên cho outfit này", item.title ?? "");
    if (title === null) return;
    try {
      const updated = await api.updateSavedOutfit(item.id, title.trim() || null);
      setItems((current) => current.map((value) => value.id === item.id ? updated : value));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể đổi tên outfit.");
    }
  }

  async function remove(item: SavedOutfit) {
    if (!window.confirm("Xóa outfit này khỏi danh sách đã lưu?")) return;
    try {
      await api.deleteSavedOutfit(item.id);
      setItems((current) => current.filter((value) => value.id !== item.id));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể xóa outfit.");
    }
  }

  return <div className="content-page">
    <div className="page-heading"><div><h1>Outfit đã lưu</h1><p>Các bộ đồ bạn muốn giữ lại để xem và mặc lại sau.</p></div><div className="hero-actions"><button className="btn ghost" type="button" onClick={load}>Làm mới</button><Link href="/stylist" className="btn primary"><Icon name="sparkle" size={16} /> Tạo gợi ý mới</Link></div></div>
    {error ? <p className="error-copy">{error}</p> : null}
    {loading ? <div className="empty-state"><h3>Đang tải outfit đã lưu…</h3></div> : items.length === 0 ? <div className="empty-state"><Icon name="heart" size={28} /><h3>Chưa có outfit nào</h3><p>Lưu một gợi ý từ AI Stylist để xem lại ở đây.</p></div> : <div className="saved-grid">{items.map((item) => <article className="saved-card" key={item.id}><div className="saved-card-head"><div><h3>{item.title || "Outfit từ HerStyle AI"}</h3><p>{new Date(item.saved_at).toLocaleString("vi-VN")}</p></div><button className="icon-btn" type="button" onClick={() => void remove(item)} aria-label="Xóa outfit">×</button></div><div className="saved-preview">{snapshotImages(item.snapshot).map((src) => <img key={src} src={src} alt="" />)}</div><div className="saved-tags"><span>Recommendation</span><span>{item.recommendation_id.slice(0, 10)}…</span></div><p className="muted-copy">Snapshot này được lưu độc lập, vẫn có thể xem dù gợi ý gốc đã thay đổi.</p><div className="stack-actions horizontal"><button className="btn ghost" type="button" onClick={() => void rename(item)}>Đổi tên</button><Link href="/stylist" className="btn white">Phối lại</Link></div></article>)}</div>}
  </div>;
}
