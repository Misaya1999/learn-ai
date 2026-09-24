export default function Home() {
  return (
    <main className="flex min-h-screen items-center justify-center px-6">
      <section className="w-full max-w-2xl rounded-3xl border border-slate-200 bg-white p-10 text-center shadow-sm sm:p-16">
        <div className="mx-auto mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-600 text-xl font-bold text-white">
          LA
        </div>
        <p className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-indigo-600">
          Milestone 1
        </p>
        <h1 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
          LearnAI is running.
        </h1>
        <p className="mx-auto mt-5 max-w-lg text-lg leading-8 text-slate-600">
          The project foundation is ready for the learning experiences we will build next.
        </p>
      </section>
    </main>
  );
}

