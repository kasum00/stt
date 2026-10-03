const categoryLabels: Record<string, string> = {
  top: "Áo",
  bottom: "Quần / chân váy",
  dress: "Đầm",
  outerwear: "Áo khoác",
  shoes: "Giày",
  accessory: "Túi & phụ kiện",
};

const colorLabels: Record<string, string> = {
  beige: "beige",
  brown: "nâu",
  black: "đen",
  white: "trắng",
  gray: "xám",
  grey: "xám",
  navy: "xanh navy",
  blue: "xanh dương",
  red: "đỏ",
  pink: "hồng",
  green: "xanh lá",
  yellow: "vàng",
  orange: "cam",
  purple: "tím",
};

const patternLabels: Record<string, string> = {
  solid: "trơn",
  floral: "hoa",
  striped: "sọc",
  polka_dot: "chấm bi",
  checked: "caro",
  plaid: "kẻ ô",
  graphic: "họa tiết hình",
};

export function categoryLabel(value?: string | null): string {
  if (!value) return "Trang phục";
  return categoryLabels[value.toLowerCase()] ?? value;
}

export function colorLabel(value?: string | null): string {
  if (!value) return "chưa rõ màu";
  return colorLabels[value.toLowerCase()] ?? value;
}

export function patternLabel(value?: string | null): string {
  if (!value) return "chưa rõ họa tiết";
  return patternLabels[value.toLowerCase()] ?? value;
}

export function titleCase(value?: string | null): string {
  if (!value) return "Chưa cập nhật";
  return value
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function scoreLabel(value?: number | null): string {
  if (typeof value !== "number" || Number.isNaN(value)) return "—";
  return value.toFixed(2);
}

export function temperatureLabel(value?: number | null): string {
  if (typeof value !== "number" || Number.isNaN(value)) return "—";
  return `${Math.round(value)}°`;
}

export function outfitTitle(
  structure?: string | null,
  itemCount?: number,
): string {
  if (structure) return structure.split("+").map(categoryLabel).join(" · ");
  return itemCount ? `Phối đồ ${itemCount} món` : "Gợi ý phối đồ";
}

