"use client";

import Link from "next/link";
import { AppShell } from "@/components/app-shell";
import { useAuth } from "@/lib/auth-context";

export default function DashboardPage() {
  const { user } = useAuth();

  return (
    <AppShell>
      <main className="mx-auto max-w-7xl px-5 py-12 sm:px-8 sm:py-16 lg:px-10">
        <p className="text-sm font-bold uppercase tracking-[0.18em] text-indigo-700">Dashboard</p>
        <h1 className="mt-3 text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl">Welcome back{user ? `, ${user.name}` : ""}.</h1>
        <p className="mt-3 max-w-2xl leading-7 text-slate-600">Your LearnAI workspace is ready. Continue to Courses to manage lessons or explore available learning material.</p>
        <div className="mt-10 grid gap-5 md:grid-cols-2">
          <Link href="/courses" className="group rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:border-indigo-200 hover:shadow-md"><span className="flex h-11 w-11 items-center justify-center rounded-xl bg-indigo-50 text-xl text-indigo-700">▤</span><h2 className="mt-5 text-xl font-semibold text-slate-950">Courses</h2><p className="mt-2 leading-7 text-slate-600">{user?.role === "teacher" ? "Create courses and organize their lessons." : "Browse courses and manage your enrollments."}</p><span className="mt-5 inline-flex text-sm font-semibold text-indigo-700">Open courses <span aria-hidden="true" className="ml-2 transition-transform group-hover:translate-x-1">→</span></span></Link>
          <section aria-labelledby="account-heading" className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between gap-4"><h2 id="account-heading" className="text-xl font-semibold text-slate-950">Account</h2>{user && <span className="rounded-full bg-indigo-50 px-3 py-1 text-sm font-semibold capitalize text-indigo-700">{user.role}</span>}</div>
            {user && <dl className="mt-5 divide-y divide-slate-200"><div className="py-3"><dt className="text-sm text-slate-500">Name</dt><dd className="mt-1 font-medium text-slate-900">{user.name}</dd></div><div className="py-3"><dt className="text-sm text-slate-500">Email</dt><dd className="mt-1 break-all font-medium text-slate-900">{user.email}</dd></div></dl>}
          </section>
        </div>
      </main>
    </AppShell>
  );
}
