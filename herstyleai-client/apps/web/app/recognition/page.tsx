"use client";

/* eslint-disable @next/next/no-img-element */

import Link from "next/link";
import { ChangeEvent, FormEvent, useEffect, useMemo, useState } from "react";
import { Icon } from "@/components/Icon";
import { getAccessToken } from "@/lib/auth/token-store";
import { AnalysisResult, ApiError, api, resolveMediaUrl } from "@/lib/api";
import { categoryLabel, colorLabel, patternLabel } from "@/lib/format";

const MAX_UPLOADS = 50;

const emptyValues = {
  category: "",
  subcategory: "",
  color: "",
  pattern: "",
};

type AttributeKey = keyof typeof emptyValues;
type AttributeValues = typeof emptyValues;
type BatchStatus = "queued" | "processing" | "ready" | "saving" | "error" | "saved";

type BatchItem = {
  id: string;
  file: File;
  previewUrl: string;
  name: string;
  status: BatchStatus;
  result?: AnalysisResult;
  values: AttributeValues;
  error?: string;
};

const fields: Array<{ key: AttributeKey; label: string }> = [
  { key: "category", label: "Danh mục" },
  { key: "subcategory", label: "Kiểu dáng" },
  { key: "color", label: "Màu sắc" },
  { key: "pattern", label: "Họa tiết" },
];

function valuesFromResult(result: AnalysisResult): AttributeValues {
  const item = result.preview_item ?? result.attributes ?? result;
  return {
    category: typeof item.category === "string" ? item.category : "",
    subcategory: typeof item.subcategory === "string" ? item.subcategory : "",
    color: typeof item.color === "string" ? item.color : "",
    pattern: typeof item.pattern === "string" ? item.pattern : "",
  };
}

function messageFromError(reason: unknown, fallback: string) {
  return reason instanceof Error ? reason.message : fallback;
}

function duplicatePendingAnalysisId(reason: unknown): string | null {
  if (!(reason instanceof ApiError) || reason.status !== 409) return null;

  const payload = reason.payload;
  if (!payload || typeof payload !== "object") return null;

  const detail = (payload as { detail?: unknown }).detail;
  if (!detail || typeof detail !== "object") return null;

  const detailRecord = detail as { code?: unknown; analysis_id?: unknown };
  if (detailRecord.code !== "duplicate_pending_analysis") return null;
  return typeof detailRecord.analysis_id === "string" ? detailRecord.analysis_id : null;
}

export default function RecognitionPage() {
  const [batchItems, setBatchItems] = useState<BatchItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [working, setWorking] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [authenticatedImage, setAuthenticatedImage] = useState<{ source: string; url: string } | null>(null);

  const activeItem = useMemo(
    () => batchItems.find((item) => item.id === selectedId) ?? null,
    [batchItems, selectedId],
  );
  const completedCount = batchItems.filter(
    (item) => item.status === "ready" || item.status === "saved" || item.status === "error",
  ).length;
  const readyCount = batchItems.filter((item) => item.status === "ready" || item.status === "saved").length;
  const savedCount = batchItems.filter((item) => item.status === "saved").length;

  const activeImagePath = resolveMediaUrl(
    activeItem?.result?.images?.transparent_url ??
      activeItem?.result?.images?.model_url ??
      activeItem?.result?.images?.original_url,
  );

  useEffect(() => {
    if (!activeImagePath) return;

    const imagePath = activeImagePath;

    const controller = new AbortController();
    let objectUrl: string | null = null;

    async function loadPreview() {
      try {
        const token = getAccessToken();
        const response = await fetch(imagePath, {
          signal: controller.signal,
          headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        });
        if (!response.ok) throw new Error("Không tải được ảnh preview");
        const blob = await response.blob();
        const previewUrl = URL.createObjectURL(blob);
        objectUrl = previewUrl;
        setAuthenticatedImage({ source: imagePath, url: previewUrl });
      } catch {
        // Keep the local upload thumbnail as a reliable fallback when the
        // authenticated preview request is unavailable.
      }
    }

    void loadPreview();
    return () => {
      controller.abort();
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [activeImagePath]);

  function updateItem(id: string, update: Partial<BatchItem>) {
    setBatchItems((current) =>
      current.map((item) => (item.id === id ? { ...item, ...update } : item)),
    );
  }

  function resetBatch() {
    batchItems.forEach((item) => URL.revokeObjectURL(item.previewUrl));
    setBatchItems([]);
    setSelectedId(null);
    setWorking(false);
    setSaving(false);
    setError("");
  }

  async function chooseFiles(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? []);
    event.target.value = "";

    if (!files.length) return;
    if (files.length > MAX_UPLOADS) {
      setError(`Bạn có thể chọn tối đa ${MAX_UPLOADS} ảnh trong một lần.`);
      return;
    }

    const invalidFile = files.find((file) => !file.type.startsWith("image/"));
    if (invalidFile) {
      setError("Vui lòng chỉ chọn các tệp ảnh PNG, JPG hoặc WEBP.");
      return;
    }

    batchItems.forEach((item) => URL.revokeObjectURL(item.previewUrl));

    const items: BatchItem[] = files.map((file, index) => ({
      id: `${Date.now()}-${index}-${file.name}`,
      file,
      previewUrl: URL.createObjectURL(file),
      name: file.name,
      status: "queued",
      values: { ...emptyValues },
    }));

    setBatchItems(items);
    setSelectedId(items[0]?.id ?? null);
    setError("");
    setWorking(true);

    for (const item of items) {
      updateItem(item.id, { status: "processing", error: undefined });
      try {
        const result = await api.analyzeGarment(item.file);
        const values = valuesFromResult(result);
        updateItem(item.id, {
          status: "saving",
          result,
          values,
          error: undefined,
        });
        await saveRecognizedItem(item.id, result, values);
      } catch (reason) {
        const pendingAnalysisId = duplicatePendingAnalysisId(reason);
        if (pendingAnalysisId) {
          try {
            const result = await api.getPendingAnalysis(pendingAnalysisId);
            const values = valuesFromResult(result);
            updateItem(item.id, {
              status: "saving",
              result,
              values,
              error: undefined,
            });
            await saveRecognizedItem(item.id, result, values);
            continue;
          } catch (resumeReason) {
            updateItem(item.id, {
              status: "error",
              error: messageFromError(
                resumeReason,
                "Không thể khôi phục kết quả nhận diện đang chờ.",
              ),
            });
            continue;
          }
        }

        updateItem(item.id, {
          status: "error",
          error: messageFromError(reason, "Không nhận diện được ảnh này."),
        });
      }
    }

    setWorking(false);
  }

  function selectItem(item: BatchItem) {
    setSelectedId(item.id);
    setError(item.status === "error" ? item.error ?? "Không nhận diện được ảnh này." : "");
  }

  function updateActiveValue(key: AttributeKey, value: string) {
    if (!activeItem) return;
    updateItem(activeItem.id, { values: { ...activeItem.values, [key]: value } });
  }

  async function saveRecognizedItem(
    itemId: string,
    result: AnalysisResult,
    values: AttributeValues,
  ) {
    updateItem(itemId, { status: "saving", error: undefined });
    try {
      await api.confirmGarment(result.analysis_id, values);
      updateItem(itemId, { status: "saved", error: undefined });
    } catch (reason) {
      updateItem(itemId, {
        status: "ready",
        error: messageFromError(reason, "Nhận diện xong nhưng chưa lưu được vào tủ đồ."),
      });
    }
  }

  async function confirm(event: FormEvent) {
    event.preventDefault();
    if (!activeItem?.result || activeItem.status === "saved") return;

    setSaving(true);
    setError("");
    try {
      await api.confirmGarment(activeItem.result.analysis_id, activeItem.values);
      updateItem(activeItem.id, { status: "saved" });
    } catch (reason) {
      setError(messageFromError(reason, "Không lưu được món đồ."));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="content-page recognition-page">
      <div className="page-heading recognition-heading">
        <div>
          <span className="recognition-eyebrow">HERSTYLE AI · WARDROBE SCAN</span>
          <h1>Nhận diện trang phục</h1>
          <p>Chọn một hoặc tối đa {MAX_UPLOADS} ảnh để AI phân tích nhanh tủ đồ của bạn.</p>
        </div>
        {batchItems.length ? (
          <div className="recognition-progress">
            <strong>{readyCount}/{batchItems.length}</strong>
            <span>{working ? `Đang xử lý · ${completedCount}/${batchItems.length}` : "Ảnh đã được lưu"}</span>
          </div>
        ) : null}
      </div>

      <div className="recognition-workspace">
        <section className="recognition-upload-card" aria-label="Tải ảnh trang phục">
          <div className="recognition-upload-hero">
            <div className="recognition-upload-icon"><Icon name="upload" size={28} /></div>
            <div>
              <span className="recognition-eyebrow">BƯỚC 01</span>
              <h2>Tải ảnh món đồ lên</h2>
              <p>Ảnh rõ vật thể, nền đơn giản sẽ giúp kết quả nhận diện chính xác hơn.</p>
            </div>
            <label className="btn primary recognition-upload-button">
              <Icon name="upload" size={17} />
              Chọn ảnh
              <input
                type="file"
                accept="image/png,image/jpeg,image/webp"
                multiple
                onChange={chooseFiles}
              />
            </label>
          </div>

          <div className="recognition-upload-note">
            <span><Icon name="sparkle" size={16} /> Tối đa {MAX_UPLOADS} ảnh · nhận diện xong tự lưu</span>
            <span>PNG · JPG · WEBP</span>
          </div>

          {batchItems.length ? (
            <div className="recognition-batch-grid">
              {batchItems.map((item, index) => (
                <button
                  type="button"
                  className={`recognition-batch-item ${item.id === selectedId ? "selected" : ""}`}
                  key={item.id}
                  onClick={() => selectItem(item)}
                  title={item.name}
                >
                  <span className="recognition-batch-index">{index + 1}</span>
                  <img src={item.previewUrl} alt={item.name} />
                  <span className={`recognition-status ${item.status}`}>
                    {item.status === "processing" ? "Đang xử lý" : item.status === "saving" ? "Đang lưu" : item.status === "ready" ? "Cần kiểm tra" : item.status === "saved" ? "Đã thêm" : item.status === "error" ? "Lỗi" : "Đang chờ"}
                  </span>
                </button>
              ))}
            </div>
          ) : (
            <div className="recognition-upload-empty">
              <div className="recognition-empty-art"><Icon name="sparkle" size={36} /></div>
              <strong>Chưa có ảnh nào được chọn</strong>
              <p>Bạn có thể tải lên cả một loạt ảnh quần áo cùng lúc.</p>
            </div>
          )}

          {batchItems.length ? (
            <div className="recognition-upload-footer">
              <span>{batchItems.length} ảnh trong phiên nhận diện{savedCount ? ` · ${savedCount} ảnh đã thêm vào tủ` : ""}</span>
              <button className="text-link" type="button" onClick={resetBatch}>Xóa và chọn lại</button>
            </div>
          ) : null}
        </section>

        <form className="analysis-card recognition-analysis-card" onSubmit={confirm}>
          <div className="recognition-panel-heading">
            <div>
              <span className="recognition-eyebrow">BƯỚC 02</span>
              <h2>Thông tin nhận diện</h2>
            </div>
            {activeItem ? <span className={`recognition-detail-status ${activeItem.status}`}>{activeItem.status === "saved" ? "Đã lưu vào tủ" : activeItem.status === "saving" ? "Đang lưu…" : activeItem.status === "ready" ? "Cần kiểm tra" : activeItem.status === "processing" ? "Đang xử lý" : "Ảnh đã chọn"}</span> : null}
          </div>

          {error ? <p className="error-copy">{error}</p> : null}

          {!activeItem ? (
            <div className="analysis-empty recognition-analysis-empty">
              <Icon name="sparkle" size={30} />
              <strong>Chọn ảnh để xem kết quả</strong>
              <p>Thông tin danh mục, màu sắc và họa tiết sẽ xuất hiện ở đây.</p>
            </div>
          ) : activeItem.status === "processing" || activeItem.status === "queued" || activeItem.status === "saving" ? (
            <div className="analysis-empty recognition-analysis-empty">
              <span className="recognition-spinner"><Icon name="sparkle" size={30} /></span>
              <strong>{activeItem.status === "processing" ? "AI đang phân tích ảnh…" : activeItem.status === "saving" ? "Đang lưu vào tủ đồ…" : "Ảnh đang chờ xử lý…"}</strong>
              <p>{activeItem.status === "saving" ? "Món đồ sẽ xuất hiện ngay trong tủ đồ của bạn." : "Hệ thống sẽ tự động chuyển sang ảnh tiếp theo."}</p>
            </div>
          ) : activeItem.status === "error" ? (
            <div className="analysis-empty recognition-analysis-empty is-error">
              <Icon name="sparkle" size={30} />
              <strong>Chưa nhận diện được ảnh này</strong>
              <p>{activeItem.error ?? "Bạn có thể chọn ảnh khác để tiếp tục."}</p>
            </div>
          ) : (
            <>
              <div className="recognition-result-preview">
                <img src={authenticatedImage?.source === activeImagePath ? authenticatedImage.url : activeItem.previewUrl} alt="Kết quả nhận diện" />
                <span>{activeItem.name}</span>
              </div>
              {activeItem.error ? <p className="error-copy recognition-save-warning">{activeItem.error}</p> : null}
              <div className="recognition-fields">
                {fields.map((field) => (
                  <label className="info-row info-input" key={field.key}>
                    <span>{field.label}</span>
                    <input
                      value={activeItem.values[field.key]}
                      disabled={activeItem.status === "saved"}
                      onChange={(event) => updateActiveValue(field.key, event.target.value)}
                    />
                  </label>
                ))}
              </div>
              <div className="tag-line">
                <span>Gợi ý nhanh</span>
                <div>
                  <b>{categoryLabel(activeItem.values.category)}</b>
                  <b>{colorLabel(activeItem.values.color)}</b>
                  <b>{patternLabel(activeItem.values.pattern)}</b>
                </div>
              </div>
              <div className="stack-actions recognition-actions">
                <button className="btn primary" disabled={saving || activeItem.status === "saved"}>
                  <Icon name={activeItem.status === "saved" ? "check" : "plus"} size={17} />
                  {saving ? "Đang lưu…" : activeItem.status === "saved" ? "Đã thêm vào tủ đồ" : "Thêm vào tủ đồ"}
                </button>
                <Link href="/wardrobe" className="btn ghost">Mở tủ đồ</Link>
              </div>
            </>
          )}
        </form>
      </div>
    </div>
  );
}
