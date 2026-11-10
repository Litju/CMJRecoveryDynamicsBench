import type { Metadata } from "next";
import { brand } from "@/lib/brand";
import "./tokens.css";
import "./globals.css";
import "./editorial.css";
import "./publication.css";
export const metadata: Metadata = {
  title: `${brand.name} — Countermovement-jump recovery research companion`,
  description: brand.description,
  robots: { index: false, follow: false },
  openGraph: {
    type: "website",
    locale: "en_US",
    siteName: brand.name,
    title: `${brand.name} — Recovery research atlas`,
    description: brand.description,
  },
  twitter: {
    card: "summary",
    title: `${brand.name} — Recovery research atlas`,
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
