"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { AuthShell } from "@/components/auth-shell";
import { ApiError, registerAccount, type UserRole } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<UserRole>("student");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const normalizedName = name.trim();
    const normalizedEmail = email.trim();
    if (!normalizedName || normalizedName.length > 100) {
      setError("Name must contain between 1 and 100 characters.");
      return;
    }
    if (!normalizedEmail || !/^\S+@\S+\.\S+$/.test(normalizedEmail)) {
      setError("Enter a valid email address.");
      return;
    }
    if (password.length < 8 || password.length > 128) {
      setError("Password must contain between 8 and 128 characters.");
      return;
    }

    setSubmitting(true);
    try {
      await registerAccount({ name: normalizedName, email: normalizedEmail, password, role });
      router.replace("/login?registered=1");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Your account could not be created. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthShell title="Create your account" description="Choose your role and start building a learning workspace." footer={<>Already have an account? <Link href="/login" className="font-semibold text-indigo-700 hover:text-indigo-800">Sign in</Link></>}>
      {error && <div role="alert" className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{error}</div>}
      <form onSubmit={handleSubmit} noValidate className="space-y-5">
        <div><label htmlFor="name" className="block text-sm font-semibold text-slate-800">Full name</label><input id="name" name="name" type="text" autoComplete="name" required maxLength={100} value={name} onChange={(event) => setName(event.target.value)} className="mt-2 block w-full rounded-xl border border-slate-300 bg-white px-3.5 py-3 outline-none transition focus:border-indigo-500 focus:ring-3 focus:ring-indigo-100" placeholder="Your name" /></div>
        <div><label htmlFor="email" className="block text-sm font-semibold text-slate-800">Email address</label><input id="email" name="email" type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} className="mt-2 block w-full rounded-xl border border-slate-300 bg-white px-3.5 py-3 outline-none transition focus:border-indigo-500 focus:ring-3 focus:ring-indigo-100" placeholder="you@example.com" /></div>
        <div><label htmlFor="password" className="block text-sm font-semibold text-slate-800">Password</label><input id="password" name="password" type="password" autoComplete="new-password" required minLength={8} maxLength={128} value={password} onChange={(event) => setPassword(event.target.value)} className="mt-2 block w-full rounded-xl border border-slate-300 bg-white px-3.5 py-3 outline-none transition focus:border-indigo-500 focus:ring-3 focus:ring-indigo-100" placeholder="8–128 characters" /></div>
        <fieldset><legend className="text-sm font-semibold text-slate-800">I am joining as</legend><div className="mt-2 grid grid-cols-2 gap-3">{(["student", "teacher"] as const).map((option) => <label key={option} className={`cursor-pointer rounded-xl border px-4 py-3 text-center text-sm font-semibold capitalize transition has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-indigo-600 ${role === option ? "border-indigo-500 bg-indigo-50 text-indigo-700 ring-2 ring-indigo-100" : "border-slate-300 text-slate-600 hover:border-slate-400"}`}><input type="radio" name="role" value={option} checked={role === option} onChange={() => setRole(option)} className="sr-only" />{option}</label>)}</div></fieldset>
        <button type="submit" disabled={submitting} className="inline-flex w-full items-center justify-center rounded-xl bg-indigo-600 px-4 py-3 font-semibold text-white shadow-sm transition hover:bg-indigo-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:cursor-not-allowed disabled:bg-indigo-400">{submitting ? "Creating account…" : "Create account"}</button>
      </form>
    </AuthShell>
  );
}
