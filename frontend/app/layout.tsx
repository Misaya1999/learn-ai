import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LearnAI — Learning grounded in your course materials",
  description:
    "An AI-powered EdTech platform with grounded tutoring, lesson-based quizzes, and learning analytics.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
