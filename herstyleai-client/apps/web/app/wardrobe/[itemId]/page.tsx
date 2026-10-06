"use client";

/* eslint-disable @next/next/no-img-element */

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import AppShell from "@/components/AppShell";
import { Icon } from "@/components/Icon";
import { getAccessToken } from "@/lib/auth/token-store";
import { api, resolveMediaUrl, WardrobeItem } from "@/lib/api";
import { categoryLabel, colorLabel, patternLabel, titleCase } from "@/lib/format";

function ProtectedWardrobeImage({ imagePath, alt }: { imagePath: string | null; alt: string }) {
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

  return src ? <img className="wardrobe-detail-image" src={src} alt={alt} /> : <div className="cloth-image-loading"><Icon name="wardrobe" size={36} /></div>;
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

export default function WardrobeItemPage() {
  const params = useParams<{ itemId: string }>();
  const router = useRouter();
  const [item, setItem] = useState<WardrobeItem | null>(null);
  const [values, setValues] = useState({ category: "", subcategory: "", color: "", pattern: "", material: "" });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api.getWardrobeItem(params.itemId).then((result) => {
      setItem(result);
      setValues({ category: String(result.category ?? ""), subcategory: String(result.subcategory ?? ""), color: String(result.color ?? ""), pattern: String(result.pattern ?? ""), material: String(result.material ?? "") });
    }).catch((reason) => setError(reason instanceof Error ? reason.message : "Không tải được món đồ.")).finally(() => setLoading(false));
  }, [params.itemId]);

  async function save(event: FormEvent) {
    event.preventDefault();
    setSaving(true); setMessage(""); setError("");
    try {
      const result = await api.updateGarment(params.itemId, values);
      setItem(result.item);
      setMessage("Đã cập nhật món đồ.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể cập nhật món đồ.");
    } finally {
      setSaving(false);
    }
  }

  async function remove() {
    if (!window.confirm("Xóa món đồ này khỏi tủ đồ?")) return;
    try {
      await api.deleteGarment(params.itemId);
      router.replace("/wardrobe");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể xóa món đồ.");
    }
  }

  const image = item ? resolveMediaUrl(item.transparent_image_url ?? item.transparent_url ?? item.model_url ?? item.image_url ?? item.image_path) : null;
  const status = item ? usageStatus(item) : null;
  const itemTitle = item ? titleCase(item.subcategory ?? item.category) : "Món đồ";

  return (
    <AppShell>
      <div className="content-page item-detail-page">
        <Link href="/wardrobe" className="item-detail-back">← Về tủ đồ</Link>
        {loading ? (
          <div className="empty-state item-detail-loading"><Icon name="wardrobe" size={30} /><h3>Đang tải món đồ…</h3></div>
        ) : error && !item ? (
          <div className="empty-state"><h3>Không thể tải món đồ</h3><p>{error}</p></div>
        ) : item ? (
          <div className="item-detail-shell">
            <header className="item-detail-header">
              <div>
                <span className="item-detail-kicker">CHI TIẾT TỦ ĐỒ</span>
                <h1>{itemTitle}</h1>
                <p>Quản lý thông tin và xem món đồ này trong tủ đồ số của bạn.</p>
              </div>
              {status ? <div className={`item-status ${status.className}`}><i />{status.label}<small>{status.note}</small></div> : null}
            </header>

            <div className="item-detail-layout">
              <section className="item-preview-card">
                <div className="item-preview-frame">
                  <ProtectedWardrobeImage imagePath={image} alt={itemTitle} />
                </div>
                <div className="item-preview-footer">
                  <div><span>Danh mục</span><strong>{categoryLabel(item.category)}</strong></div>
                  <div><span>Màu sắc</span><strong>{colorLabel(item.color)}</strong></div>
                </div>
              </section>

              <form className="item-info-card" onSubmit={save}>
                <div className="item-info-heading"><div><span>THÔNG TIN NHẬN DIỆN</span><h2>Thuộc tính món đồ</h2></div><Icon name="edit" size={19} /></div>
                {error ? <p className="error-copy">{error}</p> : null}
                {message ? <p className="success-copy">{message}</p> : null}
                <div className="item-fields">
                  {["category", "subcategory", "color", "pattern", "material"].map((field) => <label key={field}><span>{{ category: "Danh mục", subcategory: "Kiểu dáng", color: "Màu sắc", pattern: "Họa tiết", material: "Chất liệu" }[field]}</span><input value={values[field as keyof typeof values]} onChange={(event) => setValues((current) => ({ ...current, [field]: event.target.value }))} /></label>)}
                </div>
                <div className="item-tags"><span>Gợi ý nhanh</span><div><b>{categoryLabel(item.category)}</b><b>{colorLabel(item.color)}</b><b>{patternLabel(item.pattern)}</b></div></div>
                <div className="item-detail-actions"><button className="button button-primary" disabled={saving}>{saving ? "Đang lưu…" : "Lưu thay đổi"}</button><Link href="/stylist" className="button button-outline"><Icon name="sparkle" size={16} /> Phối món đồ này</Link><button className="item-delete-button" type="button" onClick={() => void remove()}>Xóa món đồ</button></div>
              </form>
            </div>
          </div>
        ) : null}
      </div>
    </AppShell>
  );
}
