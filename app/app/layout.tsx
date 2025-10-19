import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Hanzi Flow - Learn Chinese Characters",
  description: "Practice Chinese character pinyin typing",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
