import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/contexts/AuthContext";
import { BotProvider } from "@/contexts/BotContext";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "CryptoBot - Kripto Al-Sat Botu",
  description: "Otomatik kripto para alım satım botu arayüzü",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="tr">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-[#0f0f1a]`}
      >
        <AuthProvider>
          <BotProvider>
            {children}
          </BotProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
