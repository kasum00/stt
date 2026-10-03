import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import "./phase5b.css";
import { AppHeader } from "@/components/AppHeader";
import { ChatWidget } from "@/components/ChatWidget";
import { AuthGate } from "@/components/AuthGate";
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
  src: [
    { path: "../public/fonts/lora.ttf", weight: "400 700", style: "normal" },
  ],
  variable: "--font-lora",
  display: "swap",
});

export const metadata: Metadata = {
  title: "HerStyle AI",
  description: "Digital wardrobe and AI outfit stylist"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="vi" className={`${inter.variable} ${lora.variable}`}>
      <body>
        <AuthProvider>
          <AppHeader />
          <main className="page-shell"><AuthGate>{children}</AuthGate></main>
          <ChatWidget />
        </AuthProvider>
      </body>
    </html>
  );
}
