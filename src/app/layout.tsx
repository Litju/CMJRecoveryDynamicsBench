import type { Metadata } from "next";
import { brand } from "@/lib/brand";
import "./globals.css";
import "./editorial.css";
export const metadata: Metadata = {
  title: `${brand.name} — Synthetic recovery research`,
  description: brand.description,
  robots: { index: false, follow: false },
  openGraph: {
    type: "website",
    locale: "en_US",
    siteName: brand.name,
    title: `${brand.name} — Synthetic recovery research`,
    description: brand.description,
  },
  twitter: {
    card: "summary",
    title: `${brand.name} — Synthetic recovery research`,
    description: brand.description,
  },
};
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
