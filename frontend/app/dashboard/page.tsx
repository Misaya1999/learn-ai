"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/lib/auth-context";

export default function DashboardPage() {
  const router = useRouter();
  const { user, ready, signOut } = useAuth();

  useEffect(() => {
    if (ready && !user) router.replace("/login");
  }, [ready, user, router]);

  function handleLogout() {
    signOut();
    router.replace("/login");
  }

  if (!ready || !user) {
    return <main className="flex min-h-screen items-center justify-center bg-slate-50"><p role="status" className="text-sm font-medium text-slate-600">Checking your session…</p></main>;
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-5 py-4 sm:px-8">
          <Link href="/" className="flex items-center gap-2.5 font-semibold text-slate-950"><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600 text-sm font-bold text-white">LA</span><span className="text-lg">LearnAI</span></Link>
          <button type="button" onClick={handleLogout} className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600">Log out</button>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-5 py-12 sm:px-8 sm:py-16">
        <p className="text-sm font-bold uppercase tracking-[0.18em] text-indigo-700">Authenticated workspace</p>
        <h1 className="mt-3 text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl">Welcome, {user.name}.</h1>
        <p className="mt-3 max-w-2xl leading-7 text-slate-600">Your account is connected to the LearnAI API. Course and learning experiences will arrive in the next frontend milestone.</p>

        <section aria-labelledby="account-heading" className="mt-10 max-w-2xl rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
          <div className="flex items-center justify-between gap-4"><h2 id="account-heading" className="text-xl font-semibold text-slate-950">Account</h2><span className="rounded-full bg-indigo-50 px-3 py-1 text-sm font-semibold capitalize text-indigo-700">{user.role}</span></div>
          <dl className="mt-6 divide-y divide-slate-200">
            <div className="grid gap-1 py-4 sm:grid-cols-[8rem_1fr]"><dt className="text-sm font-medium text-slate-500">Name</dt><dd className="font-medium text-slate-900">{user.name}</dd></div>
            <div className="grid gap-1 py-4 sm:grid-cols-[8rem_1fr]"><dt className="text-sm font-medium text-slate-500">Email</dt><dd className="break-all font-medium text-slate-900">{user.email}</dd></div>
            <div className="grid gap-1 py-4 sm:grid-cols-[8rem_1fr]"><dt className="text-sm font-medium text-slate-500">Role</dt><dd className="font-medium capitalize text-slate-900">{user.role}</dd></div>
          </dl>
        </section>
      </main>
    </div>
  );
}
