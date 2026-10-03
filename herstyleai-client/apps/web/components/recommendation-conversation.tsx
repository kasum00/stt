"use client";

/* eslint-disable @next/next/no-img-element */

import { FormEvent } from "react";
import { Icon } from "./icons";
import {
  FeedbackEventType,
  Outfit,
  resolveMediaUrl,
  ScheduleDay,
  WardrobeItem,
  WeeklyResponse,
} from "../lib/api";
import { categoryLabel, outfitTitle, temperatureLabel, titleCase } from "../lib/format";

type View = "home" | "wardrobe" | "recommend" | "week";

type Props = {
  requestText: string;
  setRequestText: (value: string) => void;
  preferDress: boolean;
  setPreferDress: (value: boolean) => void;
  days: number;
  setDays: (value: number) => void;
  loading: boolean;
  error: string | null;
  weekly: WeeklyResponse | null;
  onSubmit: (event: FormEvent) => void;
  onOpenOutfit: (outfit: Outfit, explanation?: Outfit["explanation"]) => void;
  onFeedback: (eventType: FeedbackEventType, outfit: Outfit) => Promise<void>;
  feedbackState: Record<string, FeedbackEventType[]>;
  onNavigate: (view: View) => void;
};

function itemImage(item: WardrobeItem): string | null {
  const transparentImage = item.transparent_image_url ?? item.transparent_url ?? item.model_url;
  return resolveMediaUrl(typeof transparentImage === "string" ? transparentImage : typeof item.image_url === "string" ? item.image_url : null);
}

function ConversationImage({ item }: { item: WardrobeItem }) {
  const src = itemImage(item);
  return <div className="conversation-item-image">{src ? <img src={src} alt={`${categoryLabel(item.category)} ${titleCase(item.subcategory)}`} /> : <Icon name="hanger" size={22} />}</div>;
}

function ConversationOutfitCard({ day, onOpenOutfit, onFeedback, feedback }: { day: ScheduleDay; onOpenOutfit: Props["onOpenOutfit"]; onFeedback: Props["onFeedback"]; feedback: FeedbackEventType[] }) {
  const outfit = day.outfit;
  if (!outfit) return null;
  const items = Object.entries(outfit.items ?? {});
  const temperature = day.weather?.temperature ?? day.weather?.temperature_c;
  return <article className="conversation-outfit-card"><div className="conversation-outfit-images">{items.slice(0, 4).map(([slot, item]) => <div className="conversation-outfit-image" key={`${slot}-${item.item_id}`}><ConversationImage item={item} /></div>)}</div><div className="conversation-outfit-content"><div className="conversation-outfit-topline"><span className="conversation-day">Ngày {day.day}</span>{typeof temperature === "number" ? <span className="conversation-weather"><Icon name="sun" size={14} /> {temperatureLabel(temperature)}</span> : null}</div><h3>{outfitTitle(outfit.structure, items.length)}</h3><p>{day.explanation?.summary ?? outfit.explanation?.summary ?? "Mình đã chọn một outfit từ chính tủ đồ của bạn."}</p><div className="conversation-outfit-actions"><button className="button button-primary button-small" onClick={() => onOpenOutfit(outfit, day.explanation)}>Xem chi tiết <Icon name="arrow" size={14} /></button><button className={`feedback-button ${feedback.includes("outfit_liked") ? "selected" : ""}`} onClick={() => void onFeedback("outfit_liked", outfit)} aria-label="Thích outfit"><Icon name="heart" size={16} /></button><button className={`feedback-button ${feedback.includes("outfit_saved") ? "selected" : ""}`} onClick={() => void onFeedback("outfit_saved", outfit)} aria-label="Lưu outfit"><Icon name="bookmark" size={16} /></button><button className={`feedback-button ${feedback.includes("outfit_worn") ? "selected" : ""}`} onClick={() => void onFeedback("outfit_worn", outfit)} aria-label="Đã mặc outfit"><Icon name="check" size={16} /></button></div></div></article>;
}

export function RecommendationConversation({ requestText, setRequestText, preferDress, setPreferDress, days, setDays, loading, error, weekly, onSubmit, onOpenOutfit, onFeedback, feedbackState, onNavigate }: Props) {
  const hasResults = Boolean(weekly);
  const schedule = weekly?.schedule ?? [];

  return (
    <section className="page-section conversation-page">
      <div className="conversation-header">
        <span className="eyebrow">AI STYLIST · GỢI Ý TỪ TỦ ĐỒ CỦA BẠN</span>
        <h1>Gợi ý phối đồ cho bạn</h1>
        <p>Hãy kể một chút về ngày của bạn, HerStyleAI sẽ tìm outfit phù hợp từ chính tủ đồ.</p>
      </div>

      <div className="conversation-shell">
        <div className="assistant-message">
          <span className="assistant-avatar"><Icon name="sparkle" size={16} /></span>
          <div className="message-body">
            <span className="message-author">HerStyleAI</span>
            <p>Chào bạn 👋<br />Hôm nay bạn có kế hoạch gì? Mình sẽ chọn outfit phù hợp với thời tiết và những món đồ bạn đang có.</p>
          </div>
        </div>

        {requestText.trim() ? <div className="user-message"><p>{requestText}</p></div> : null}

        {loading ? (
          <div className="assistant-message assistant-loading" role="status" aria-live="polite">
            <span className="assistant-avatar"><Icon name="sparkle" size={16} /></span>
            <div className="message-body">
              <span className="message-author">HerStyleAI</span>
              <p><span className="spinner" /> Mình đang xem thời tiết và tìm outfit hợp với bạn…</p>
            </div>
          </div>
        ) : null}

        {!loading && error ? (
          <div className="assistant-message assistant-error">
            <span className="assistant-avatar"><Icon name="info" size={16} /></span>
            <div className="message-body">
              <span className="message-author">HerStyleAI</span>
              <p>{error}</p>
              <button className="text-button" onClick={() => onNavigate("recommend")}>Thử lại yêu cầu <Icon name="arrow" size={14} /></button>
            </div>
          </div>
        ) : null}

        {!loading && !error && hasResults ? (
          <div className="assistant-message results-message">
            <span className="assistant-avatar"><Icon name="sparkle" size={16} /></span>
            <div className="message-body">
              <span className="message-author">HerStyleAI</span>
              <p>{schedule.length ? "Đây là những outfit mình chọn cho bạn." : "Mình chưa tìm thấy outfit phù hợp hoàn toàn với yêu cầu này."}</p>
              {schedule.length ? (
                <div className="conversation-results">
                  {schedule.slice(0, 3).map((day) => (
                    <ConversationOutfitCard
                      key={day.day}
                      day={day}
                      onOpenOutfit={onOpenOutfit}
                      onFeedback={onFeedback}
                      feedback={day.outfit?.recommendation_id ? feedbackState[day.outfit.recommendation_id] ?? [] : []}
                    />
                  ))}
                </div>
              ) : (
                <button className="button button-secondary button-small" onClick={() => setRequestText("")}>Thử một yêu cầu khác</button>
              )}
            </div>
          </div>
        ) : null}

        <form className="styling-composer" onSubmit={onSubmit}>
          <textarea value={requestText} onChange={(event) => setRequestText(event.target.value)} placeholder="Ví dụ: Mai mình có cuộc họp và muốn mặc sơ mi…" rows={1} />
          <button className="composer-send" disabled={loading} aria-label="Gửi yêu cầu">{loading ? <span className="spinner spinner-white" /> : <Icon name="arrow" size={18} />}</button>
        </form>

        <div className="conversation-suggestions">
          <span>Gợi ý nhanh</span>
          <button type="button" onClick={() => setRequestText("Ngày mai em muốn mặc váy, tone sáng, không đi sneaker")}>Váy tone sáng</button>
          <button type="button" onClick={() => setRequestText("Hôm nay mặc sơ mi trắng, không đi sneaker")}>Sơ mi trắng</button>
          <button type="button" onClick={() => setRequestText("Đi làm thanh lịch")}>Đi làm thanh lịch</button>
        </div>

        <div className="conversation-options">
          <label className="conversation-toggle">
            <span>Ưu tiên váy / đầm</span>
            <button type="button" className={`switch ${preferDress ? "on" : ""}`} onClick={() => setPreferDress(!preferDress)} aria-label="Bật ưu tiên váy"><span /></button>
          </label>
          <div className="conversation-days">
            <span>Lịch</span>
            {[1, 3, 7].map((value) => <button type="button" key={value} className={days === value ? "active" : ""} onClick={() => setDays(value)}>{value} ngày</button>)}
          </div>
        </div>
      </div>
    </section>
  );
}

