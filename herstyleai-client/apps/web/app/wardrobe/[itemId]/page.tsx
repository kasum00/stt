"use client";

/* eslint-disable @next/next/no-img-element */

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
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

  return src ? <img src={src} alt={alt} /> : <div className="cloth-image-loading"><Icon name="wardrobe" size={36} /></div>;
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
  return <div className="content-page item-detail-page"><Link href="/wardrobe" className="text-link">← Về tủ đồ</Link>{loading ? <div className="empty-state"><Icon name="wardrobe" size={30} /><h3>Đang tải món đồ…</h3></div> : error && !item ? <div className="empty-state"><h3>Không thể tải món đồ</h3><p>{error}</p></div> : item ? <div className="recognition-grid item-detail-grid"><div className="recognition-image-card"><ProtectedWardrobeImage imagePath={image} alt={titleCase(item.subcategory ?? item.category)} /></div><form className="analysis-card" onSubmit={save}><h1>{titleCase(item.subcategory ?? item.category)}</h1><p>Món đồ trong tủ đồ của bạn</p>{error ? <p className="error-copy">{error}</p> : null}{message ? <p className="success-copy">{message}</p> : null}{["category", "subcategory", "color", "pattern", "material"].map((field) => <label className="info-row info-input" key={field}><span>{{ category: "Danh mục", subcategory: "Kiểu dáng", color: "Màu sắc", pattern: "Họa tiết", material: "Chất liệu" }[field]}</span><input value={values[field as keyof typeof values]} onChange={(event) => setValues((current) => ({ ...current, [field]: event.target.value }))} /></label>)}<div className="tag-row"><span>{categoryLabel(item.category)}</span><span>{colorLabel(item.color)}</span><span>{patternLabel(item.pattern)}</span></div><div className="stack-actions"><button className="btn primary" disabled={saving}>{saving ? "Đang lưu…" : "Lưu thay đổi"}</button><button className="btn danger" type="button" onClick={() => void remove()}>Xóa món đồ</button><Link href="/stylist" className="btn ghost"><Icon name="sparkle" size={16} /> Phối món đồ này</Link></div></form></div> : null}</div>;
}
