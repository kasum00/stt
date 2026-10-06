"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import Icon from "@/components/Icon";
import { ProtectedMediaImage } from "@/components/ProtectedMediaImage";
import { api, resolveMediaUrl, type Outfit, type WardrobeItem, type Weather } from "@/lib/api";

type DateContext = {
  date?: string;
  display_date_vi?: string;
  now?: string;
};

function greetingForHour(hour: number) {
  if (hour >= 22 || hour < 5) return "Chào buổi đêm";
  if (hour < 12) return "Chào buổi sáng";
  if (hour < 18) return "Chào buổi chiều";
  return "Chào buổi tối";
}

function wardrobeImage(item: WardrobeItem) {
  return resolveMediaUrl(
    item.transparent_image_url ??
      item.transparent_url ??
      item.image_url ??
      item.image_path,
  );
}

function wardrobeLabel(item: WardrobeItem) {
  return item.subcategory ?? item.category ?? "Trang phục";
}

export default function Home(){
  const [wardrobeCount, setWardrobeCount] = useState<number | null>(null);
  const [wardrobeItems, setWardrobeItems] = useState<WardrobeItem[]>([]);
  const [todayOutfit, setTodayOutfit] = useState<Outfit | null>(null);
  const [todayWeather, setTodayWeather] = useState<Weather | null>(null);
  const [displayName, setDisplayName] = useState("bạn");
  const [greeting, setGreeting] = useState("Chào bạn");
  const [displayDate, setDisplayDate] = useState("");
  const [locationName, setLocationName] = useState("Hà Nội");
  const [recommendationLoading, setRecommendationLoading] = useState(true);

  useEffect(() => {
    void api.getWardrobe().then((result) => {
      setWardrobeCount(result.count ?? result.items.length);
      setWardrobeItems(result.items ?? []);
    }).catch(() => {
      setWardrobeCount(0);
      setWardrobeItems([]);
    });

    void (async () => {
      try {
        const [contextResult, accountResult, latestResult] = await Promise.all([
          api.getDateContext().catch(() => null),
          Promise.all([api.getMe(), api.getProfile()]).catch(() => null),
          api.getLatestWeeklyRecommendation().catch(() => null),
        ]);
        const dateContext = contextResult as DateContext | null;
        const profile = accountResult?.[1] ?? null;
        const current = dateContext?.now ? new Date(dateContext.now) : new Date();
        setGreeting(greetingForHour(current.getHours()));
        setDisplayDate(
          dateContext?.display_date_vi ??
            new Intl.DateTimeFormat("vi-VN", { day: "2-digit", month: "long", year: "numeric" }).format(current),
        );
        if (accountResult) {
          const [user] = accountResult;
          const profileName = profile?.display_name?.trim();
          const emailName = user.email.split("@")[0]?.trim();
          setDisplayName(profileName || emailName || "bạn");
          setLocationName(profile?.location_name?.trim() || "Hà Nội");
        }

        let today = latestResult?.schedule?.find(
          (day) => day.weather?.date === dateContext?.date && day.outfit,
        ) ?? null;
        if (!today) {
          const fresh = await api.getWeeklyRecommendation({
            latitude: profile?.latitude ?? 21.0285,
            longitude: profile?.longitude ?? 105.8542,
            prefer_dress: false,
            days: 1,
            styling_request: "Gợi ý trang phục hôm nay",
          });
          today = fresh.schedule?.[0] ?? null;
        }
        setTodayOutfit(today?.outfit ?? null);
        setTodayWeather(today?.weather ?? null);
      } catch {
        setTodayOutfit(null);
        setTodayWeather(null);
      } finally {
        setRecommendationLoading(false);
      }
    })();
  }, []);

  const suggestedItems = Object.entries(todayOutfit?.items ?? {}).slice(0, 4);
  const score = todayOutfit?.compatibility_score ?? todayOutfit?.score;
  const scoreLabel = typeof score === "number"
    ? `${Math.round(score * (score <= 1 ? 100 : 1))}% phù hợp`
    : "AI đang gợi ý";
  const temperature = todayWeather?.temperature_c ?? todayWeather?.temperature;
  const weatherDescription = todayWeather?.description ?? todayWeather?.condition ?? "Đang cập nhật";

  return (
    <AppShell>
      <div className="dashboard-top">
        <div><h1>{greeting}, {displayName}! 👋</h1><p>{displayDate || "Đang cập nhật ngày"}</p></div>
        <div className="weather-card-home"><span className="weather-location">{locationName}</span><strong>{typeof temperature === "number" ? `${Math.round(temperature)}°C` : "--"}</strong><span className="weather-condition">☁ {weatherDescription}</span></div>
      </div>

      <div className="home-grid">
        <section className="panel suggestion-panel">
          <div className="panel-heading"><h2>Gợi ý hôm nay</h2><span className="match">● {scoreLabel}</span></div>
          <div className="suggestion-content">
            <div className="suggestion-products">
              {suggestedItems.length > 0 ? suggestedItems.map(([slot, item]) => (
                <Link className="product-card compact" href={`/wardrobe/${item.item_id}`} key={`${slot}-${item.item_id}`}>
                  <div className="product-image">
                    <ProtectedMediaImage
                      src={wardrobeImage(item)}
                      alt={wardrobeLabel(item)}
                      fallback={<span className="image-fallback"><Icon name="shirt" size={24} /></span>}
                    />
                  </div>
                </Link>
              )) : <div className="dashboard-wardrobe-empty">{recommendationLoading ? "Đang tải gợi ý hôm nay…" : "Chưa có outfit gợi ý hôm nay."}</div>}
            </div>
            <div className="suggestion-info"><span>{todayOutfit?.structure ?? "Phối đồ cá nhân hóa"}</span><span>Phù hợp thời tiết hôm nay</span><span>{todayOutfit ? "Đã có lịch gợi ý" : recommendationLoading ? "Đang tải dữ liệu" : "Tạo gợi ý đầu tiên"}</span><Link href={todayOutfit ? "/recommend/result" : "/recommend"} className="button button-primary button-sm">Xem chi tiết →</Link></div>
          </div>
        </section>

        <aside className="quick-stack">
          <Link href="/wardrobe/add" className="quick-action"><div className="quick-icon blue"><Icon name="upload"/></div><div><strong>Thêm trang phục</strong><span>Tải ảnh để nhận diện</span></div><b>›</b></Link>
          <Link href="/recommend" className="quick-action"><div className="quick-icon purple"><Icon name="sparkle"/></div><div><strong>AI gợi ý phối đồ</strong><span>Tạo outfit cho hôm nay</span></div><b>›</b></Link>
          <Link href="/calendar" className="quick-action"><div className="quick-icon cyan"><Icon name="calendar"/></div><div><strong>Lên kế hoạch tuần</strong><span>Tạo outfit theo lịch</span></div><b>›</b></Link>
        </aside>
      </div>

      <section className="panel wardrobe-preview">
        <div className="panel-heading"><div className="inline-title"><h2>Tủ đồ của bạn</h2><span>{wardrobeCount === null ? "Đang tải…" : `${wardrobeCount} trang phục`}</span></div><Link href="/wardrobe">Xem tất cả →</Link></div>
        <div className="wardrobe-preview-grid dashboard-wardrobe-large">
          {wardrobeItems.length > 0 ? wardrobeItems.slice(0, 6).map((item) => (
            <Link className="dashboard-wardrobe-item" href={`/wardrobe/${item.item_id}`} key={item.item_id}>
              <div className="dashboard-wardrobe-image">
                <ProtectedMediaImage
                  src={wardrobeImage(item)}
                  alt={wardrobeLabel(item)}
                  fallback={<span className="image-fallback"><Icon name="shirt" size={24} /></span>}
                />
              </div>
              <div className="dashboard-wardrobe-meta">
                <strong>{wardrobeLabel(item)}</strong>
                <span>{item.color ?? "Chưa có màu"}{item.pattern ? ` · ${item.pattern}` : ""}</span>
              </div>
            </Link>
          )) : (
            <div className="dashboard-wardrobe-empty">Chưa có ảnh trang phục trong tủ đồ.</div>
          )}
        </div>
      </section>
    </AppShell>
  );
}
