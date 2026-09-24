const features = [
  { title: "Grounded AI Tutor", description: "Ask questions against lesson materials and receive focused answers with source references.", icon: "spark" },
  { title: "AI-generated quizzes", description: "Turn indexed lesson content into multiple-choice practice with automatic, server-side grading.", icon: "quiz" },
  { title: "Learning analytics", description: "Help students track progress and give teachers a clear view of course and lesson performance.", icon: "chart" },
  { title: "Course management", description: "Organize courses and ordered lessons with ownership-aware workflows for educators.", icon: "course" },
  { title: "PDF learning materials", description: "Upload course documents, extract their content, and prepare them for semantic retrieval.", icon: "document" },
  { title: "Teacher and student roles", description: "Keep authoring, enrollment, practice, and review experiences clearly separated by role.", icon: "users" },
] as const;

const workflow = [
  { step: "01", title: "Add lesson material", description: "A teacher creates a course and uploads a text-based PDF to a lesson." },
  { step: "02", title: "Process and index", description: "LearnAI extracts, chunks, embeds, and indexes the material for retrieval." },
  { step: "03", title: "Learn and practice", description: "Students ask grounded questions and complete lesson-based quizzes." },
  { step: "04", title: "Understand progress", description: "Submitted results become useful student and course analytics." },
] as const;

const technologies = [
  ["Next.js", "TypeScript frontend"], ["FastAPI", "Python API"],
  ["PostgreSQL", "pgvector retrieval"], ["OpenAI", "Embeddings and RAG"],
  ["Docker Compose", "Reproducible stack"], ["GitHub Actions", "Automated checks"],
] as const;

function FeatureIcon({ name }: { name: (typeof features)[number]["icon"] }) {
  const paths = {
    spark: <path d="m12 3-1.4 4.1a5.5 5.5 0 0 1-3.5 3.5L3 12l4.1 1.4a5.5 5.5 0 0 1 3.5 3.5L12 21l1.4-4.1a5.5 5.5 0 0 1 3.5-3.5L21 12l-4.1-1.4a5.5 5.5 0 0 1-3.5-3.5L12 3Z" />,
    quiz: <><path d="M9 11h6M9 15h4" /><path d="M6 3h12a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z" /><path d="m9 7 1 1 2-2" /></>,
    chart: <><path d="M4 20V10M10 20V4M16 20v-7M22 20H2" /></>,
    course: <><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v16H6.5A2.5 2.5 0 0 0 4 21.5v-16Z" /><path d="M4 18.5A2.5 2.5 0 0 1 6.5 16H20" /></>,
    document: <><path d="M6 2h8l4 4v16H6V2Z" /><path d="M14 2v5h5M9 12h6M9 16h6" /></>,
    users: <><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8ZM22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" /></>,
  };
  return <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6">{paths[name]}</svg>;
}

function Brand() {
  return <span className="inline-flex items-center gap-2.5 font-semibold tracking-tight text-slate-950"><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600 text-sm font-bold text-white shadow-sm">LA</span><span className="text-lg">LearnAI</span></span>;
}

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-950">
      <header className="sticky top-0 z-50 border-b border-slate-200/80 bg-slate-50/95 backdrop-blur-sm">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-6 px-5 py-4 sm:px-8 lg:px-10">
          <a href="#top" aria-label="LearnAI home"><Brand /></a>
          <nav aria-label="Primary navigation" className="hidden items-center gap-8 text-sm font-medium text-slate-600 md:flex">
            <a className="transition-colors hover:text-indigo-700" href="#features">Features</a>
            <a className="transition-colors hover:text-indigo-700" href="#how-it-works">How it works</a>
            <a className="transition-colors hover:text-indigo-700" href="#engineering">Engineering</a>
          </nav>
          <div className="flex items-center gap-2 sm:gap-3">
            <a href="/login" className="hidden rounded-lg px-3 py-2 text-sm font-semibold text-slate-600 transition-colors hover:text-indigo-700 sm:inline-flex">Sign in</a>
            <a href="/register" className="inline-flex items-center justify-center rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-indigo-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600">Get started</a>
          </div>
        </div>
      </header>

      <main id="top">
        <section className="relative overflow-hidden border-b border-slate-200 bg-white">
          <div aria-hidden="true" className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-indigo-300 to-transparent" />
          <div className="mx-auto grid max-w-7xl items-center gap-14 px-5 py-20 sm:px-8 sm:py-28 lg:grid-cols-[1.05fr_.95fr] lg:px-10 lg:py-32">
            <div>
              <p className="mb-6 inline-flex items-center rounded-full border border-indigo-200 bg-indigo-50 px-3.5 py-1.5 text-sm font-semibold text-indigo-700">Learning grounded in your course materials</p>
              <h1 className="max-w-3xl text-4xl font-bold tracking-[-0.04em] text-slate-950 sm:text-6xl sm:leading-[1.08]">Turn lesson content into an active learning experience.</h1>
              <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600 sm:text-xl">LearnAI brings a grounded AI Tutor, lesson-based quizzes, and meaningful learning analytics together around the material teachers already use.</p>
              <div className="mt-9 flex flex-col gap-3 sm:flex-row">
                <a href="/register" className="inline-flex items-center justify-center rounded-xl bg-indigo-600 px-5 py-3 text-base font-semibold text-white shadow-sm transition-colors hover:bg-indigo-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600">Create an account <span aria-hidden="true" className="ml-2">→</span></a>
                <a href="#features" className="inline-flex items-center justify-center rounded-xl border border-slate-300 bg-white px-5 py-3 text-base font-semibold text-slate-700 shadow-sm transition-colors hover:border-slate-400 hover:bg-slate-50">Explore features</a>
              </div>
            </div>

            <div className="relative mx-auto w-full max-w-xl" aria-label="LearnAI product workflow preview">
              <div aria-hidden="true" className="absolute -inset-5 rounded-[2rem] bg-indigo-100/60 blur-2xl" />
              <div className="relative overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl shadow-slate-200/70">
                <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
                  <div className="flex items-center gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600 text-xs font-bold text-white">LA</span><div><p className="text-sm font-semibold text-slate-900">Introduction to ML</p><p className="text-xs text-slate-500">Lesson workspace</p></div></div>
                  <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700">Material ready</span>
                </div>
                <div className="grid sm:grid-cols-[.7fr_1.3fr]">
                  <div className="border-b border-slate-200 bg-slate-50 p-5 sm:border-r sm:border-b-0">
                    <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Lesson material</p>
                    <div className="mt-4 rounded-xl border border-slate-200 bg-white p-3"><p className="text-sm font-semibold text-slate-800">machine-learning.pdf</p><p className="mt-1 text-xs text-slate-500">Indexed for retrieval</p></div>
                    <div className="mt-5 space-y-2"><div className="h-2 rounded-full bg-slate-200" /><div className="h-2 w-4/5 rounded-full bg-slate-200" /><div className="h-2 w-3/5 rounded-full bg-slate-200" /></div>
                  </div>
                  <div className="p-5">
                    <div className="flex items-center gap-2 text-sm font-semibold text-indigo-700"><FeatureIcon name="spark" /> AI Tutor</div>
                    <div className="mt-4 rounded-xl bg-slate-100 p-3 text-sm leading-6 text-slate-700">How does supervised learning use labeled data?</div>
                    <div className="mt-3 rounded-xl border border-indigo-100 bg-indigo-50 p-4 text-sm leading-6 text-slate-700">Supervised learning uses labeled examples to learn a mapping between inputs and expected outputs.</div>
                    <p className="mt-3 text-xs font-medium text-slate-500">Source: machine-learning.pdf · chunk 4</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="features" className="scroll-mt-24 py-20 sm:py-28">
          <div className="mx-auto max-w-7xl px-5 sm:px-8 lg:px-10">
            <div className="max-w-2xl"><p className="text-sm font-bold uppercase tracking-[0.18em] text-indigo-700">Platform capabilities</p><h2 className="mt-3 text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl">Everything stays connected to the lesson.</h2><p className="mt-4 text-lg leading-8 text-slate-600">From uploaded material to practice and progress, LearnAI keeps each workflow tied to a course, lesson, and user role.</p></div>
            <div className="mt-12 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
              {features.map((feature) => <article key={feature.title} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><span className="flex h-11 w-11 items-center justify-center rounded-xl bg-indigo-50 text-indigo-700"><FeatureIcon name={feature.icon} /></span><h3 className="mt-5 text-lg font-semibold text-slate-950">{feature.title}</h3><p className="mt-2 leading-7 text-slate-600">{feature.description}</p></article>)}
            </div>
          </div>
        </section>

        <section id="how-it-works" className="scroll-mt-20 border-y border-slate-200 bg-white py-20 sm:py-28">
          <div className="mx-auto max-w-7xl px-5 sm:px-8 lg:px-10">
            <div className="max-w-2xl"><p className="text-sm font-bold uppercase tracking-[0.18em] text-indigo-700">How it works</p><h2 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">A clear path from material to insight.</h2></div>
            <ol className="mt-12 grid gap-8 md:grid-cols-2 lg:grid-cols-4">
              {workflow.map((item, index) => <li key={item.step} className="relative"><div className="flex items-center gap-4"><span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-indigo-200 bg-indigo-50 text-sm font-bold text-indigo-700">{item.step}</span>{index < workflow.length - 1 && <span aria-hidden="true" className="hidden h-px flex-1 bg-slate-200 lg:block" />}</div><h3 className="mt-5 text-lg font-semibold">{item.title}</h3><p className="mt-2 leading-7 text-slate-600">{item.description}</p></li>)}
            </ol>
          </div>
        </section>

        <section id="engineering" className="scroll-mt-20 py-20 sm:py-28">
          <div className="mx-auto grid max-w-7xl gap-12 px-5 sm:px-8 lg:grid-cols-[.8fr_1.2fr] lg:px-10">
            <div><p className="text-sm font-bold uppercase tracking-[0.18em] text-indigo-700">Built as a real system</p><h2 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">Modern engineering, end to end.</h2><p className="mt-5 text-lg leading-8 text-slate-600">LearnAI is a personal portfolio project exploring how product design, backend architecture, retrieval, authorization, testing, and deployment fit together in an EdTech platform.</p><a href="https://github.com/Misaya1999/learn-ai" target="_blank" rel="noreferrer" className="mt-7 inline-flex items-center font-semibold text-indigo-700 hover:text-indigo-800">Explore the source on GitHub <span aria-hidden="true" className="ml-2">↗</span></a></div>
            <div className="grid gap-4 sm:grid-cols-2">{technologies.map(([name, detail]) => <div key={name} className="flex items-center gap-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><span aria-hidden="true" className="h-2.5 w-2.5 rounded-full bg-indigo-500" /><div><h3 className="font-semibold text-slate-900">{name}</h3><p className="mt-0.5 text-sm text-slate-500">{detail}</p></div></div>)}</div>
          </div>
        </section>

        <section className="px-5 pb-20 sm:px-8 sm:pb-28">
          <div className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-7 rounded-2xl bg-slate-950 px-7 py-10 text-white sm:px-10 md:flex-row md:items-center"><div><h2 className="text-2xl font-bold tracking-tight sm:text-3xl">Explore how LearnAI is built.</h2><p className="mt-2 max-w-2xl leading-7 text-slate-300">Follow the project architecture, implementation milestones, and technical decisions in the repository.</p></div><a href="https://github.com/Misaya1999/learn-ai" target="_blank" rel="noreferrer" className="inline-flex shrink-0 items-center justify-center rounded-xl bg-white px-5 py-3 font-semibold text-slate-950 transition-colors hover:bg-indigo-50">View GitHub repository <span aria-hidden="true" className="ml-2">↗</span></a></div>
        </section>
      </main>

      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-6 px-5 py-8 sm:flex-row sm:items-center sm:justify-between sm:px-8 lg:px-10"><div><Brand /><p className="mt-2 text-sm text-slate-500">Personal EdTech / AI portfolio project.</p></div><a href="https://github.com/Misaya1999/learn-ai" target="_blank" rel="noreferrer" className="text-sm font-semibold text-slate-600 hover:text-indigo-700">GitHub <span aria-hidden="true">↗</span></a></div>
      </footer>
    </div>
  );
}
