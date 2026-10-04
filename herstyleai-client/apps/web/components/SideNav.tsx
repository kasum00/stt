import Link from "next/link";
import { Icon } from "./Icon";

const items = [
  ["/", "Trang chủ", "home"],
  ["/wardrobe", "Tủ đồ", "wardrobe"],
  ["/planner", "Lịch phối đồ", "calendar"],
  ["/calendar", "Sự kiện", "calendar"],
  ["/chat", "Chat AI", "chat"],
  ["/profile", "Hồ sơ", "user"]
] as const;

export function SideNav({ active }: { active: string }) {
  return <aside className="side-nav">{items.map(([href, label, icon]) => <Link key={href} href={href} className={active === href ? "active" : ""}><Icon name={icon} size={18}/><span>{label}</span></Link>)}</aside>;
}
