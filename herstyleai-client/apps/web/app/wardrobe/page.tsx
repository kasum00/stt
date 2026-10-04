"use client";

/* eslint-disable @next/next/no-img-element */

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Icon } from "@/components/Icon";
import { getAccessToken } from "@/lib/auth/token-store";
import { api, resolveMediaUrl, WardrobeItem } from "@/lib/api";
import { categoryLabel, colorLabel, patternLabel, titleCase } from "@/lib/format";

const filters = [["all", "Tất cả"], ["top", "Áo"], ["bottom", "Quần"], ["dress", "Váy"], ["outerwear", "Khoác"], ["shoes", "Giày"], ["accessory", "Túi & phụ kiện"]] as const;

function imageFor(item: WardrobeItem) {
  return resolveMediaUrl(item.transparent_image_url ?? item.transparent_url ?? item.model_url ?? item.image_url ?? item.image_path);
}

function WardrobeImage({ item, alt }: { item: WardrobeItem; alt: string }) {
  const imagePath = imageFor(item);
  const [src, setSrc] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    let objectUrl: string | null = null;

    if (!imagePath) return undefined;

    const token = getAccessToken();
    fetch(imagePath, {
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    })
      .then((response) => {
        if (!response.ok) throw new Error("Image request failed");
        return response.blob();
      })
      .then((blob) => {
        if (cancelled) return;
        objectUrl = URL.createObjectURL(blob);
        setSrc(objectUrl);
      })
      .catch(() => {
        if (!cancelled) setSrc(null);
      });

    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [imagePath]);

  if (!src) return <div className="cloth-image-loading"><Icon name="wardrobe" size={34} /></div>;
  return <img src={src} alt={alt} />;
}

function stylingStatus(item: WardrobeItem) {
  if (!item.last_styled_at) {
    return { label: "Chưa sử dụng", tone: "unused", title: "Món đồ này chưa được dùng trong lịch phối đồ." };
  }

  const availableAt = item.styling_available_at
    ? new Date(item.styling_available_at).toLocaleDateString("vi-VN")
    : null;

  return {
    label: "Đã sử dụng",
    tone: "used",
    title: item.styling_cooldown_active && availableAt
      ? `Đã dùng. Có thể phối lại từ ${availableAt}.`
      : "Đã dùng và hiện có thể phối lại.",
  };
}

export default function WardrobePage() {
  const [items, setItems] = useState<WardrobeItem[]>([]);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    api.getWardrobe().then((result) => {
      if (active) setItems(result.items ?? []);
    }).catch((reason) => {
      if (active) setError(reason instanceof Error ? reason.message : "Không tải được tủ đồ.");
    }).finally(() => {
      if (active) setLoading(false);
    });
    return () => { active = false; };
  }, []);

  const visibleItems = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return items.filter((item) => {
      if (filter !== "all" && item.category !== filter) return false;
      if (!needle) return true;
      return [item.category, item.subcategory, item.color, item.pattern, ...(item.style_tags ?? [])].filter(Boolean).some((value) => String(value).toLowerCase().includes(needle));
    });
  }, [filter, items, query]);

  return <div className="content-page">
    <div className="page-heading"><div><h1>Tủ đồ của tôi</h1><p>Quản lý tất cả trang phục của bạn tại đây</p></div><Link href="/recognition" className="btn primary"><Icon name="plus" size={17} /> Thêm trang phục</Link></div>
    <div className="wardrobe-layout">
      <aside className="filter-panel">{filters.map(([value, label]) => <button className={`filter ${filter === value ? "active" : ""}`} onClick={() => setFilter(value)} key={value}><span>{label}</span><b>{value === "all" ? items.length : items.filter((item) => item.category === value).length}</b></button>)}</aside>
      <section>
        <div className="toolbar"><div className="search-box"><Icon name="search" size={17} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Tìm kiếm trang phục..." /></div><select value={filter} onChange={(event) => setFilter(event.target.value)}><option value="all">Tất cả</option><option value="top">Áo</option><option value="bottom">Quần</option><option value="dress">Váy</option><option value="outerwear">Khoác</option><option value="shoes">Giày</option></select></div>
        {loading ? <div className="empty-state"><h3>Đang tải tủ đồ…</h3></div> : error ? <div className="empty-state"><h3>Không tải được tủ đồ</h3><p>{error}</p></div> : visibleItems.length === 0 ? <div className="empty-state"><h3>Chưa có món đồ phù hợp</h3><p>Hãy thêm trang phục hoặc thử bộ lọc khác.</p></div> : <div className="clothes-grid">{visibleItems.map((item) => { const status = stylingStatus(item); return <Link href={`/wardrobe/${item.item_id}`} className="cloth-card" key={item.item_id}><div className="cloth-img"><WardrobeImage item={item} alt={titleCase(item.subcategory ?? item.category ?? "Món đồ")} /><button type="button" aria-label="Tùy chọn món đồ" onClick={(event) => event.preventDefault()}>•••</button></div><strong>{titleCase(item.subcategory ?? item.category ?? "Món đồ")}</strong><span className="cloth-details">{categoryLabel(item.category)} · {colorLabel(item.color)} · {patternLabel(item.pattern)}</span><span className={`cloth-status ${status.tone}`} title={status.title}><i aria-hidden="true" />{status.label}</span></Link>; })}</div>}
      </section>
    </div>
  </div>;
}
