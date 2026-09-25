"use client";

import { useRouter } from "next/navigation";
import { useCallback } from "react";
import { AppShell } from "@/components/app-shell";
import { StudentAnalyticsDashboard, TeacherAnalyticsDashboard } from "@/components/analytics-dashboard";
import { useAuth } from "@/lib/auth-context";

export default function DashboardPage() {
  const router = useRouter();
  const { user, token, signOut } = useAuth();
  const handleUnauthorized = useCallback(() => {
    signOut();
    router.replace("/login");
  }, [signOut, router]);

  return (
    <AppShell>
      <main className="mx-auto max-w-7xl px-5 py-12 sm:px-8 sm:py-16 lg:px-10">
        <p className="text-sm font-bold uppercase tracking-[0.18em] text-indigo-700">Dashboard</p>
        <h1 className="mt-3 text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl">Welcome back{user ? `, ${user.name}` : ""}.</h1>
        <p className="mt-3 max-w-3xl leading-7 text-slate-600">{user?.role === "teacher" ? "Review real quiz participation and performance across the courses you own." : "Review your submitted quiz performance across lessons and over time."}</p>
        <div className="mt-10">{user && token && (user.role === "student" ? <StudentAnalyticsDashboard token={token} onUnauthorized={handleUnauthorized} /> : <TeacherAnalyticsDashboard token={token} userId={user.id} onUnauthorized={handleUnauthorized} />)}</div>
      </main>
    </AppShell>
  );
}
