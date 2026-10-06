"use client";

import { useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import PageHeader from "@/components/PageHeader";
import { useAuth } from "@/lib/auth/auth-context";
import { api, type Preferences, type Profile } from "@/lib/api";

export default function Profile() {
  const { user, logout } = useAuth();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [preferences, setPreferences] = useState<Preferences | null>(null);

  useEffect(() => {
    void Promise.all([api.getProfile(), api.getPreferences()]).then(([nextProfile, nextPreferences]) => { setProfile(nextProfile); setPreferences(nextPreferences); }).catch(() => undefined);
  }, []);

  const displayName = profile?.display_name || user?.email?.split("@")[0] || "Bạn";
  return (
    <AppShell>
      <PageHeader title="Hồ sơ & sở thích" subtitle="Cá nhân hóa HerStyle AI theo phong cách của bạn." />
      <div className="profile-layout">
        <section className="profile-card"><div className="profile-avatar">{displayName.slice(0, 1).toUpperCase()}</div><h2>{displayName}</h2><p>{user?.email}</p><span>Đang hoạt động</span><button className="button button-outline full" type="button">Chỉnh sửa hồ sơ</button></section>
        <section className="profile-settings"><h2>Phong cách của bạn</h2><div className="profile-row"><span>Phong cách ưu tiên</span><strong>{preferences?.preferred_styles?.join(" · ") || "Chưa thiết lập"}</strong></div><div className="profile-row"><span>Danh mục yêu thích</span><strong>{preferences?.preferred_categories?.join(" · ") || "Tất cả trang phục"}</strong></div><div className="profile-row"><span>Màu yêu thích</span><strong>{preferences?.preferred_colors?.join(" · ") || "Chưa thiết lập"}</strong></div><div className="profile-row"><span>Khu vực</span><strong>{profile?.location_name || "Hà Nội"}</strong></div><h2 className="account-title">Tài khoản</h2><button className="account-row" type="button">Đổi mật khẩu <b>›</b></button><button className="account-row" type="button">Thông báo <b>›</b></button><button className="account-row danger" type="button" onClick={() => void logout()}>Đăng xuất <b>›</b></button></section>
      </div>
    </AppShell>
  );
}
