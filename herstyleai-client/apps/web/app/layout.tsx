import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import { AuthProvider } from "@/lib/auth/auth-context";

const inter = localFont({
  src: [
    { path: "../public/fonts/inter-400.ttf", weight: "400", style: "normal" },
    { path: "../public/fonts/inter-600.ttf", weight: "600", style: "normal" },
    { path: "../public/fonts/inter-700.ttf", weight: "700", style: "normal" },
  ],
  variable: "--font-inter",
  display: "swap",
});

const lora = localFont({
  src: [{ path: "../public/fonts/lora.ttf", weight: "400 700", style: "normal" }],
  variable: "--font-lora",
  display: "swap",
});

const cormorant = localFont({
  src: [
    { path: "../public/fonts/cormorant-400.ttf", weight: "400", style: "normal" },
    { path: "../public/fonts/cormorant-500.ttf", weight: "500", style: "normal" },
    { path: "../public/fonts/cormorant-600.ttf", weight: "600", style: "normal" },
    { path: "../public/fonts/cormorant-700.ttf", weight: "700", style: "normal" },
  ],
  variable: "--font-cormorant",
  display: "swap",
});

export const metadata: Metadata = {
  title: "HerStyle AI",
  description: "Tủ quần áo số thông minh cho phụ nữ công sở",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="vi" className={`${inter.variable} ${lora.variable} ${cormorant.variable}`}>
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
