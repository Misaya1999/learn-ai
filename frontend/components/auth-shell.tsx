import Link from "next/link";

export function AuthShell({
  title,
  description,
  children,
  footer,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
  footer: React.ReactNode;
}) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-5 py-12 sm:px-8">
      <div className="w-full max-w-md">
        <Link href="/" className="mx-auto flex w-fit items-center gap-2.5 font-semibold tracking-tight text-slate-950" aria-label="Back to LearnAI home">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 text-sm font-bold text-white shadow-sm">LA</span>
          <span className="text-xl">LearnAI</span>
        </Link>
        <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-lg shadow-slate-200/50 sm:p-8">
          <header>
            <h1 className="text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl">{title}</h1>
            <p className="mt-2 leading-7 text-slate-600">{description}</p>
          </header>
          <div className="mt-7">{children}</div>
          <div className="mt-7 border-t border-slate-200 pt-6 text-center text-sm text-slate-600">{footer}</div>
        </section>
        <Link href="/" className="mx-auto mt-6 flex w-fit items-center gap-2 text-sm font-semibold text-slate-600 hover:text-indigo-700"><span aria-hidden="true">←</span> Back to LearnAI</Link>
      </div>
    </main>
  );
}
