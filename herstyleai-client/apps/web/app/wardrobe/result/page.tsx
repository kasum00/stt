"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import AppShell from "@/components/AppShell";
import PageHeader from "@/components/PageHeader";
import Icon from "@/components/Icon";
import { ProtectedMediaImage } from "@/components/ProtectedMediaImage";
import { api, resolveMediaUrl, type AnalysisResult } from "@/lib/api";

type PendingResult = { result: AnalysisResult; preview: string; name: string };
type Values = { category: string; subcategory: string; color: string; pattern: string; material: string };

function getValues(result: AnalysisResult): Values {
  const item = result.preview_item ?? result.attributes ?? result;
  return {
    category: typeof item.category === "string" ? item.category : "",
    subcategory: typeof item.subcategory === "string" ? item.subcategory : "",
    color: typeof item.color === "string" ? item.color : "",
    pattern: typeof item.pattern === "string" ? item.pattern : "",
    material: typeof item.material === "string" ? item.material : "",
  };
}

function readStoredResults(): PendingResult[] {
  if (typeof window === "undefined") return [];
  try {
    const stored = JSON.parse(sessionStorage.getItem("herstyleai:last-analysis") ?? "[]") as PendingResult[];
    return Array.isArray(stored) ? stored : [];
  } catch {
    return [];
  }
}

export default function Recognition() {
  const [results, setResults] = useState<PendingResult[]>(readStoredResults);
  const [selected, setSelected] = useState(0);
  const [values, setValues] = useState<Values>(() => {
    const first = readStoredResults()[0];
    return first ? getValues(first.result) : { category: "", subcategory: "", color: "", pattern: "", material: "" };
  });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  const active = results[selected];
  const activeItem = useMemo(() => active?.result.preview_item ?? active?.result.attributes ?? active?.result, [active]);

  function choose(index: number) {
    setSelected(index);
    setMessage("");
    setValues(getValues(results[index].result));
  }

  async function saveActive() {
    if (!active) return;
    if (active.result.status === "saved") {
      setMessage("Trang phục đã được lưu vào tủ đồ của bạn.");
      return;
    }
    setSaving(true);
    setMessage("");
    try {
      await api.confirmGarment(active.result.analysis_id, values);
      setMessage("Đã lưu trang phục vào tủ đồ.");
      const next = results.filter((_, index) => index !== selected);
      if (next.length) {
        setResults(next);
        setSelected(0);
        setValues(getValues(next[0].result));
        sessionStorage.setItem("herstyleai:last-analysis", JSON.stringify(next));
      } else {
        sessionStorage.removeItem("herstyleai:last-analysis");
      }
    } catch (reason) {
      setMessage(reason instanceof Error ? reason.message : "Không thể lưu trang phục.");
    } finally {
      setSaving(false);
    }
  }

  if (!active) return <AppShell><PageHeader title="Kết quả nhận diện" subtitle="Chưa có kết quả nhận diện nào." /><div className="empty-state"><p>Hãy tải ảnh trang phục để bắt đầu.</p><Link className="button button-primary" href="/wardrobe/add">Tải ảnh lên</Link></div></AppShell>;

  const rows: Array<[keyof Values, string]> = [["category", "Danh mục"], ["subcategory", "Kiểu dáng"], ["color", "Màu sắc"], ["pattern", "Họa tiết"], ["material", "Chất liệu"]];
  return (
    <AppShell>
      <PageHeader title="Kết quả nhận diện" subtitle={`${results.length} ảnh đã nhận diện · các món đồ đã được lưu theo tài khoản của bạn.`} />
      <section className="recognition-card">
        <div className="recognition-thumbs">{results.map((entry, index) => <button type="button" className={index === selected ? "active" : ""} onClick={() => choose(index)} key={`${entry.name}-${index}`}><img src={entry.preview} alt={entry.name} /></button>)}</div>
        <div className="recognition-photo"><div className="transparent-bg"><ProtectedMediaImage
          src={resolveMediaUrl(
            active.result.images?.transparent_url ??
              active.result.images?.model_url ??
              active.result.images?.original_url,
          )}
          alt={active.name}
          className="recognition-result-image"
          fallback={<img className="recognition-result-image" src={active.preview} alt={active.name} />}
        /></div><Link className="button button-white full" href="/wardrobe/add"><Icon name="refresh" size={16} /> Đổi ảnh khác</Link></div>
        <div className="recognition-details">
          <div className="panel-heading"><h2>Thông tin nhận diện</h2><span className="match">{active.result.status ?? "Sẵn sàng"}</span></div>
          <div className="details-table">{rows.map(([key, text]) => <label key={key}><span>{text}</span><input value={values[key]} disabled={active.result.status === "saved"} onChange={(event) => setValues((current) => ({ ...current, [key]: event.target.value }))} placeholder="Chưa có dữ liệu" /></label>)}{Array.isArray(activeItem?.style_tags) && <div><span>Phong cách</span><strong className="style-tags">{activeItem.style_tags.map((tag) => <i key={tag}>{tag}</i>)}</strong></div>}</div>
          {message && <p className={message.startsWith("Đã") ? "form-success" : "form-error"}>{message}</p>}
          <div className="recognition-actions"><button type="button" className="button button-primary" onClick={() => void saveActive()} disabled={saving || active.result.status === "saved"}>{saving ? "Đang lưu…" : active.result.status === "saved" ? "Đã lưu vào tủ đồ" : "Lưu vào tủ đồ"}</button><Link href="/wardrobe" className="button button-white">Xem tủ đồ</Link></div>
        </div>
      </section>
    </AppShell>
  );
}
