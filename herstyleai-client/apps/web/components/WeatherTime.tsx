"use client";

import { useEffect, useState } from "react";
import { Icon } from "./Icon";

export function WeatherTime() {
  const [now, setNow] = useState(new Date());
  const [temp, setTemp] = useState<number | null>(null);

  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 30000);
    fetch("https://api.open-meteo.com/v1/forecast?latitude=21.0285&longitude=105.8542&current=temperature_2m&timezone=Asia%2FBangkok")
      .then((r) => r.json())
      .then((d) => setTemp(Math.round(d?.current?.temperature_2m)))
      .catch(() => setTemp(28));
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="weather-time" title="Dữ liệu thời tiết demo mặc định theo Hà Nội">
      <Icon name="sun" size={18} />
      <div>
        <strong>{temp ?? 28}°C</strong>
        <span>Hà Nội · {now.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" })}</span>
      </div>
    </div>
  );
}
