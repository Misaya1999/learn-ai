import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LearnAI",
  description: "AI-powered learning, built one milestone at a time.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

