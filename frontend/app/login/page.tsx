"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { AuthShell } from "@/components/auth-shell";
import { useAuth } from "@/lib/auth-context";
import { ApiError } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const { signIn } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [registered, setRegistered] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    queueMicrotask(() => {
      setRegistered(new URLSearchParams(window.location.search).get("registered") === "1");
    });
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const normalizedEmail = email.trim();
    if (!normalizedEmail || !/^\S+@\S+\.\S+$/.test(normalizedEmail)) {
      setError("Enter a valid email address.");
      return;
    }
    if (!password) {
      setError("Enter your password.");
      return;
    }
    if (password.length < 8 || password.length > 128) {
      setError("Password must contain between 8 and 128 characters.");
      return;
    }

    setSubmitting(true);
    try {
      await signIn(normalizedEmail, password);
      router.replace("/dashboard");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Sign in was not successful. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthShell title="Welcome back" description="Sign in to continue to your LearnAI workspace." footer={<>New to LearnAI? <Link href="/register" className="font-semibold text-indigo-700 hover:text-indigo-800">Create an account</Link></>}>
      {registered && <div role="status" className="mb-5 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">Account created successfully. You can now sign in.</div>}
      {error && <div role="alert" className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{error}</div>}
      <form onSubmit={handleSubmit} noValidate className="space-y-5">
        <div><label htmlFor="email" className="block text-sm font-semibold text-slate-800">Email address</label><input id="email" name="email" type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} className="mt-2 block w-full rounded-xl border border-slate-300 bg-white px-3.5 py-3 text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-3 focus:ring-indigo-100" placeholder="you@example.com" /></div>
        <div><label htmlFor="password" className="block text-sm font-semibold text-slate-800">Password</label><input id="password" name="password" type="password" autoComplete="current-password" required minLength={8} maxLength={128} value={password} onChange={(event) => setPassword(event.target.value)} className="mt-2 block w-full rounded-xl border border-slate-300 bg-white px-3.5 py-3 text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-3 focus:ring-indigo-100" placeholder="Enter your password" /></div>
        <button type="submit" disabled={submitting} className="inline-flex w-full items-center justify-center rounded-xl bg-indigo-600 px-4 py-3 font-semibold text-white shadow-sm transition hover:bg-indigo-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:cursor-not-allowed disabled:bg-indigo-400">{submitting ? "Signing in…" : "Sign in"}</button>
      </form>
    </AuthShell>
  );
}
