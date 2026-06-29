import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "VeilleMaroc - Plateforme de Veille Électorale 2026",
  description: "Plateforme de veille électorale pour les élections législatives du Maroc 2026",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr" className="dark">
      <body className={`${inter.variable} font-sans antialiased`}>{children}</body>
    </html>
  );
}
