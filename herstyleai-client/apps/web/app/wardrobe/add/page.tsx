"use client";

import { ChangeEvent, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import AppShell from "@/components/AppShell";
import PageHeader from "@/components/PageHeader";
import Icon from "@/components/Icon";
import { ApiError, api, type AnalysisResult } from "@/lib/api";

type PendingResult = { result: AnalysisResult; preview: string; name: string };

function valuesFromResult(result: AnalysisResult) {
  const item = result.preview_item ?? result.attributes ?? result;
  const values = {
    category: typeof item.category === "string" ? item.category.trim() : "",
    subcategory: typeof item.subcategory === "string" ? item.subcategory.trim() : "",
    color: typeof item.color === "string" ? item.color.trim() : "",
    pattern: typeof item.pattern === "string" ? item.pattern.trim() : "",
    material: typeof item.material === "string" ? item.material.trim() : "",
  };

  return Object.fromEntries(
    Object.entries(values).filter(([, value]) => value.length > 0),
  );
}

function detailFromApiError(reason: unknown) {
  if (!(reason instanceof ApiError) || reason.status !== 409) return null;
  const payload = reason.payload;
  if (!payload || typeof payload !== "object") return null;
  const detail = (payload as { detail?: unknown }).detail;
  return detail && typeof detail === "object" ? detail as { code?: unknown; analysis_id?: unknown; item_id?: unknown } : null;
}

function toDataUrl(file: File) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

async function waitForAnalysis(result: AnalysisResult) {
  let current = result;
  for (let attempt = 0; attempt < 60; attempt += 1) {
    if (!current.status || !["pending", "queued", "processing", "running"].includes(current.status.toLowerCase())) return current;
    await new Promise((resolve) => setTimeout(resolve, 1000));
    current = await api.getPendingAnalysis(current.analysis_id);
  }
  return current;
}

export default function AddItem() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function chooseFiles(event: ChangeEvent<HTMLInputElement>) {
    const selected = Array.from(event.target.files ?? []).slice(0, 50);
    setFiles(selected);
    setPreviews(selected.map((file) => URL.createObjectURL(file)));
    setError(selected.length === 50 && (event.target.files?.length ?? 0) > 50 ? "Chỉ nhận tối đa 50 ảnh mỗi lần." : "");
  }

  async function analyze() {
    if (!files.length) {
      setError("Hãy chọn ít nhất một ảnh trang phục.");
      return;
    }
    setLoading(true);
    setError("");
    const results: PendingResult[] = [];
    try {
      for (let index = 0; index < files.length; index += 1) {
        let result: AnalysisResult;
        try {
          result = await waitForAnalysis(await api.analyzeGarment(files[index]));
        } catch (reason) {
          const detail = detailFromApiError(reason);
          if (detail?.code === "duplicate_pending_analysis" && typeof detail.analysis_id === "string") {
            result = await api.getPendingAnalysis(detail.analysis_id);
          } else if (detail?.code === "duplicate_wardrobe_item" && typeof detail.item_id === "string") {
            const item = await api.getWardrobeItem(detail.item_id);
            results.push({
              result: { analysis_id: detail.item_id, status: "saved", preview_item: item },
              preview: await toDataUrl(files[index]),
              name: files[index].name,
            });
            continue;
          } else {
            throw reason;
          }
        }

        // Recognition is complete only after the authenticated API has
        // persisted the item for the current user.  Keep the result screen
        // for review, but do not require a second manual save click.
        await api.confirmGarment(result.analysis_id, valuesFromResult(result));
        results.push({
          result: { ...result, status: "saved" },
          preview: await toDataUrl(files[index]),
          name: files[index].name,
        });
      }
      sessionStorage.setItem("herstyleai:last-analysis", JSON.stringify(results));
      router.push("/wardrobe/result");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể nhận diện ảnh.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell>
      <PageHeader title="Thêm trang phục vào tủ đồ" subtitle="Tải tối đa 50 ảnh để HerStyle AI nhận diện và lưu vào tủ đồ." />
      <section className="upload-zone">
        <div className="upload-circle"><Icon name="upload" size={28} /></div>
        <h2>Tải ảnh trang phục lên</h2>
        <p>PNG, JPG, WEBP · Ảnh rõ vật thể sẽ cho kết quả tốt hơn</p>
        <input ref={inputRef} hidden type="file" accept="image/png,image/jpeg,image/webp" multiple onChange={chooseFiles} />
        <div className="upload-buttons"><button type="button" className="button button-outline" onClick={() => inputRef.current?.click()}><Icon name="camera" size={17} /> Chọn ảnh</button><button type="button" className="button button-primary" onClick={() => void analyze()} disabled={loading || !files.length}><Icon name="sparkle" size={17} /> {loading ? "Đang nhận diện…" : "Nhận diện bằng AI"}</button></div>
        {files.length > 0 && <p className="upload-count">Đã chọn {files.length}/50 ảnh</p>}
        {error && <p className="form-error">{error}</p>}
      </section>
      {previews.length > 0 && <div className="upload-preview-grid">{previews.map((src, index) => <div className="upload-preview" key={`${src}-${index}`}><img src={src} alt={files[index]?.name ?? "Ảnh trang phục"} /><span>{index + 1}</span></div>)}</div>}
      <div className="tips-layout">
        <section><h3>Mẹo để nhận diện chính xác hơn:</h3><ul><li>✓ Chụp rõ một trang phục</li><li>✓ Nền đơn giản, đủ ánh sáng</li><li>✓ Có thể chọn nhiều ảnh cùng lúc</li></ul></section>
      </div>
    </AppShell>
  );
}
