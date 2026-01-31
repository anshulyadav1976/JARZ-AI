import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "JARZ Rental Valuation",
  description: "Spatio-Temporal Rental Valuation with AI-powered predictions",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
