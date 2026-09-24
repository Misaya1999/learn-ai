"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/lib/auth-context";

const navigation = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/courses", label: "Courses" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
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
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-5 py-4 sm:px-8 lg:px-10">
          <Link href="/" className="flex items-center gap-2.5 font-semibold text-slate-950"><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600 text-sm font-bold text-white">LA</span><span className="text-lg">LearnAI</span></Link>
          <nav aria-label="Application navigation" className="order-3 flex w-full gap-1 border-t border-slate-100 pt-3 sm:order-2 sm:w-auto sm:border-0 sm:pt-0">
            {navigation.map((item) => {
              const active = pathname === item.href || (item.href === "/courses" && pathname.startsWith("/courses/"));
              return <Link key={item.href} href={item.href} aria-current={active ? "page" : undefined} className={`rounded-lg px-3 py-2 text-sm font-semibold transition ${active ? "bg-indigo-50 text-indigo-700" : "text-slate-600 hover:bg-slate-50 hover:text-slate-950"}`}>{item.label}</Link>;
            })}
          </nav>
          <div className="order-2 flex items-center gap-3 sm:order-3">
            <div className="hidden text-right md:block"><p className="text-sm font-semibold text-slate-900">{user.name}</p><p className="text-xs capitalize text-slate-500">{user.role}</p></div>
            <button type="button" onClick={handleLogout} className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600">Log out</button>
          </div>
        </div>
      </header>
      {children}
    </div>
  );
}
