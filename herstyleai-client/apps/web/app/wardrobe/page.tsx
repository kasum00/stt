"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import AppShell from "@/components/AppShell";
import PageHeader from "@/components/PageHeader";
import Icon from "@/components/Icon";
import { ProtectedMediaImage } from "@/components/ProtectedMediaImage";
import { api, resolveMediaUrl, type WardrobeItem } from "@/lib/api";

const filters = [
  ["all", "Tất cả"],
  ["top", "Áo"],
  ["bottom", "Quần"],
  ["dress", "Váy"],
  ["outerwear", "Áo khoác"],
  ["shoes", "Giày"],
  ["accessory", "Phụ kiện"],
] as const;

function label(value?: string | null) {
  if (!value) return "Chưa phân loại";
  return value.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function itemImage(item: WardrobeItem) {
  return resolveMediaUrl(item.transparent_image_url ?? item.transparent_url ?? item.image_url ?? item.image_path);
}

function usageStatus(item: WardrobeItem) {
  if (!item.last_styled_at) {
    return { label: "Chưa sử dụng", className: "unused", note: "Sẵn sàng để phối" };
  }

  let note = "Đã được dùng trong outfit";
  if (item.styling_available_at) {
    const availableAt = new Date(item.styling_available_at);
    if (!Number.isNaN(availableAt.getTime())) {
      note = `Có thể dùng lại từ ${availableAt.toLocaleDateString("vi-VN")}`;
    }
  }

  return { label: "Đã sử dụng", className: "used", note };
}

export default function Wardrobe() {
  const [items, setItems] = useState<WardrobeItem[]>([]);
  const [filter, setFilter] = useState("all");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    void api.getWardrobe().then((result) => {
      if (active) setItems(result.items ?? []);
    }).catch((reason) => {
      if (active) setError(reason instanceof Error ? reason.message : "Không tải được tủ đồ.");
    }).finally(() => {
      if (active) setLoading(false);
    });
    return () => { active = false; };
  }, []);

  const visible = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return items.filter((item) => {
      const haystack = [item.category, item.subcategory, item.color, item.pattern, item.material].filter(Boolean).join(" ").toLowerCase();
      const matchesFilter = filter === "all" || item.category === filter;
      return matchesFilter && (!normalized || haystack.includes(normalized));
    });
  }, [filter, items, query]);

  return (
    <AppShell>
      <PageHeader title="Tủ đồ của bạn" subtitle="Quản lý và khám phá toàn bộ trang phục trong tủ đồ số." action={<Link className="button button-primary" href="/wardrobe/add">＋ Thêm trang phục</Link>} />
      <section className="wardrobe-controls">
        <div className="page-search"><Icon name="search" size={17} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Tìm kiếm trang phục..." /></div>
        <div className="chips">{filters.map(([value, text]) => <button type="button" className={filter === value ? "active" : ""} onClick={() => setFilter(value)} key={value}>{text} <small>{value === "all" ? items.length : items.filter((item) => item.category === value).length}</small></button>)}</div>
      </section>
      {loading ? <div className="empty-state">Đang tải tủ đồ…</div> : error ? <div className="empty-state"><h3>Không tải được tủ đồ</h3><p>{error}</p></div> : visible.length === 0 ? <div className="empty-state"><h3>Chưa có trang phục phù hợp</h3><p>Hãy thêm ảnh mới hoặc đổi bộ lọc.</p></div> : (
        <div className="products-grid">
          {visible.map((item) => {
            const src = itemImage(item);
            const status = usageStatus(item);
            return <Link className="product-card" href={`/wardrobe/${item.item_id}`} key={item.item_id}>
              <div className="product-image">
                <ProtectedMediaImage src={src} alt={label(item.subcategory ?? item.category)} fallback={<span className="image-fallback"><Icon name="shirt" size={34} /></span>} />
              </div>
              <div className="product-meta">
                <strong>{label(item.subcategory ?? item.category)}</strong>
                <span>{label(item.category)} · {label(item.color)} · {label(item.pattern)}</span>
                <div className="product-usage">
                  <em className={`usage-tag ${status.className}`}><i />{status.label}</em>
                  <small>{status.note}</small>
                </div>
              </div>
            </Link>;
          })}
        </div>
      )}
    </AppShell>
  );
}
