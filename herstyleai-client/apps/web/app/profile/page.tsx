"use client";

import { FormEvent, useEffect, useState } from "react";
import { SideNav } from "@/components/SideNav";
import { ApiError, api } from "@/lib/api";
import { useAuth } from "@/lib/auth/auth-context";

const splitValues = (value: string) => value.split(",").map((item) => item.trim()).filter(Boolean);

export default function ProfilePage() {
  const { user, changePassword } = useAuth();
  const [displayName, setDisplayName] = useState("");
  const [timezone, setTimezone] = useState("Asia/Ho_Chi_Minh");
  const [locale, setLocale] = useState("vi-VN");
  const [locationName, setLocationName] = useState("");
  const [preferredColors, setPreferredColors] = useState("");
  const [preferredStyles, setPreferredStyles] = useState("");
  const [preferDress, setPreferDress] = useState(false);
  const [passwords, setPasswords] = useState({ current: "", next: "" });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api.getProfile(), api.getPreferences()]).then(([profileResult, preferencesResult]) => {
      setDisplayName(profileResult.display_name ?? "");
      setTimezone(profileResult.timezone ?? "Asia/Ho_Chi_Minh");
      setLocale(profileResult.locale ?? "vi-VN");
      setLocationName(profileResult.location_name ?? "");
      setPreferredColors(preferencesResult.preferred_colors?.join(", ") ?? "");
      setPreferredStyles(preferencesResult.preferred_styles?.join(", ") ?? "");
      setPreferDress(preferencesResult.prefer_dress);
    }).catch((reason) => setError(reason instanceof Error ? reason.message : "Không thể tải hồ sơ."))
      .finally(() => setLoading(false));
  }, []);

  async function saveProfile(event: FormEvent) {
    event.preventDefault();
    setSaving(true); setMessage(""); setError("");
    try {
      await api.patchProfile({ display_name: displayName, timezone, locale, location_name: locationName || null });
      await api.patchPreferences({ prefer_dress: preferDress, preferred_colors: splitValues(preferredColors), preferred_styles: splitValues(preferredStyles) });
      setMessage("Đã lưu thay đổi.");
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : "Không thể lưu hồ sơ.");
    } finally {
      setSaving(false);
    }
  }

  async function submitPassword(event: FormEvent) {
    event.preventDefault();
    setMessage(""); setError("");
    try {
      await changePassword(passwords.current, passwords.next);
      setMessage("Mật khẩu đã đổi. Vui lòng đăng nhập lại.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể đổi mật khẩu.");
    }
  }

  return <div className="content-page profile-layout">
    <SideNav active="/profile" />
    <section className="profile-content"><div className="page-heading"><div><h1>Thông tin cá nhân</h1><p>Quản lý thông tin và tùy chỉnh trải nghiệm HerStyle AI</p></div></div>
      {loading ? <div className="empty-state"><h3>Đang tải hồ sơ…</h3></div> : <>
        {error ? <p className="error-copy">{error}</p> : null}
        {message ? <p className="success-copy">{message}</p> : null}
        <form className="profile-card" onSubmit={saveProfile}>
          <div className="profile-head"><div className="avatar large-avatar">{(user?.email?.slice(0, 2) ?? "H").toUpperCase()}</div><div><h2>{displayName || "Phong cách của bạn"}</h2><p>{user?.email}</p></div></div>
          <div className="form-grid"><label><span>Tên hiển thị</span><input value={displayName} onChange={(event) => setDisplayName(event.target.value)} /></label><label><span>Múi giờ</span><input value={timezone} onChange={(event) => setTimezone(event.target.value)} /></label><label><span>Ngôn ngữ</span><input value={locale} onChange={(event) => setLocale(event.target.value)} /></label><label><span>Khu vực</span><input value={locationName} onChange={(event) => setLocationName(event.target.value)} placeholder="Hà Nội" /></label></div>
          <label className="check-row"><input type="checkbox" checked={preferDress} onChange={(event) => setPreferDress(event.target.checked)} /><span>Ưu tiên váy trong gợi ý phối đồ</span></label>
          <div className="form-grid"><label><span>Màu yêu thích, cách nhau bằng dấu phẩy</span><input value={preferredColors} onChange={(event) => setPreferredColors(event.target.value)} placeholder="xanh, trắng, be" /></label><label><span>Phong cách yêu thích</span><input value={preferredStyles} onChange={(event) => setPreferredStyles(event.target.value)} placeholder="thanh lịch, nữ tính" /></label></div>
          <button className="btn primary" disabled={saving}>{saving ? "Đang lưu…" : "Lưu thay đổi"}</button>
        </form>
        <form className="profile-card security-card" onSubmit={submitPassword}><h2>Bảo mật</h2><p className="muted-copy">Đổi mật khẩu sẽ đăng xuất các phiên hiện tại.</p><div className="form-grid"><label><span>Mật khẩu hiện tại</span><input type="password" value={passwords.current} onChange={(event) => setPasswords((value) => ({ ...value, current: event.target.value }))} required /></label><label><span>Mật khẩu mới</span><input type="password" minLength={8} value={passwords.next} onChange={(event) => setPasswords((value) => ({ ...value, next: event.target.value }))} required /></label></div><button className="btn ghost">Đổi mật khẩu</button></form>
      </>}
    </section>
  </div>;
}
