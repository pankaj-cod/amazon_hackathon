import "../styles/globals.css";
import type { Metadata, Viewport } from "next";
import { ReactNode } from "react";
import { Noto_Sans, Noto_Sans_Devanagari, Noto_Sans_Gurmukhi } from "next/font/google";

const latin = Noto_Sans({ subsets: ["latin"], weight: ["400", "600", "700", "800"], variable: "--font-latin" });
const gurmukhi = Noto_Sans_Gurmukhi({ subsets: ["gurmukhi"], weight: ["400", "600", "700", "800"], variable: "--font-gurmukhi" });
const devanagari = Noto_Sans_Devanagari({ subsets: ["devanagari"], weight: ["400", "600", "700", "800"], variable: "--font-devanagari" });

export const metadata: Metadata = {
  title: "Parali Mitra",
  description: "Stubble-burning history, soil carbon loss and carbon-credit potential for Punjab and Haryana fields, with advice in Punjabi and Hindi.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#1c6b4f",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="pa" className={`${latin.variable} ${gurmukhi.variable} ${devanagari.variable}`}>
      <body className="antialiased">{children}</body>
    </html>
  );
}
