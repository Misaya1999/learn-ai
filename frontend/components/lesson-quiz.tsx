"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import {
  ApiError,
  generateLessonQuiz,
  getTeacherQuiz,
  listLessonQuizzes,
  startQuizAttempt,
  submitQuizAttempt,
  type QuizAttemptReview,
  type QuizAttemptStart,
  type QuizSummary,
  type QuizTeacher,
  type UserRole,
} from "@/lib/api";

interface LessonQuizProps {
  token: string;
  lessonId: string;
  courseId: string;
  role: UserRole;
  ownsCourse: boolean;
  hasReadyDocuments: boolean;
  onUnauthorized: () => void;
}

export function LessonQuiz({ token, lessonId, courseId, role, ownsCourse, hasReadyDocuments, onUnauthorized }: LessonQuizProps) {
  const [quizzes, setQuizzes] = useState<QuizSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [title, setTitle] = useState("");
  const [questionCount, setQuestionCount] = useState("5");
  const [generating, setGenerating] = useState(false);
  const [generationError, setGenerationError] = useState("");
  const [teacherQuiz, setTeacherQuiz] = useState<QuizTeacher | null>(null);
  const [viewingQuizId, setViewingQuizId] = useState<string | null>(null);
  const [startingQuizId, setStartingQuizId] = useState<string | null>(null);
  const [attempt, setAttempt] = useState<QuizAttemptStart | null>(null);
  const [selections, setSelections] = useState<Record<string, string>>({});
  const [submissionError, setSubmissionError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [review, setReview] = useState<QuizAttemptReview | null>(null);

  const handleApiError = useCallback((caught: unknown, fallback: string): string => {
    if (caught instanceof ApiError && caught.status === 401) {
      onUnauthorized();
      return "";
    }
    return caught instanceof ApiError ? caught.message : fallback;
  }, [onUnauthorized]);

  const loadQuizzes = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setQuizzes(await listLessonQuizzes(token, lessonId));
    } catch (caught) {
      setError(handleApiError(caught, "Quizzes could not be loaded."));
    } finally {
      setLoading(false);
    }
  }, [token, lessonId, handleApiError]);

  useEffect(() => {
    queueMicrotask(() => void loadQuizzes());
  }, [loadQuizzes]);

  async function handleGenerate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalizedTitle = title.trim();
    const count = Number(questionCount);
    if (generating) return;
    if (!normalizedTitle || normalizedTitle.length > 200) {
      setGenerationError("Quiz title must contain between 1 and 200 characters.");
      return;
    }
    if (!Number.isInteger(count) || count < 1 || count > 10) {
      setGenerationError("Question count must be a whole number from 1 to 10.");
      return;
    }
    setGenerating(true);
    setGenerationError("");
    try {
      const generated = await generateLessonQuiz(token, lessonId, { title: normalizedTitle, question_count: count });
      setTeacherQuiz(generated);
      setQuizzes((current) => [...current.filter((quiz) => quiz.id !== generated.id), {
        id: generated.id,
        lesson_id: generated.lesson_id,
        title: generated.title,
        created_at: generated.created_at,
      }]);
      setTitle("");
    } catch (caught) {
      setGenerationError(handleApiError(caught, "The quiz could not be generated."));
    } finally {
      setGenerating(false);
    }
  }

  async function handleViewTeacherQuiz(quizId: string) {
    if (viewingQuizId) return;
    setViewingQuizId(quizId);
    setError("");
    try {
      setTeacherQuiz(await getTeacherQuiz(token, quizId));
    } catch (caught) {
      setError(handleApiError(caught, "The quiz could not be opened."));
    } finally {
      setViewingQuizId(null);
    }
  }

  async function handleStartAttempt(quizId: string) {
    if (startingQuizId) return;
    setStartingQuizId(quizId);
    setSubmissionError("");
    setReview(null);
    try {
      const started = await startQuizAttempt(token, quizId);
      setAttempt(started);
      setSelections({});
    } catch (caught) {
      setSubmissionError(handleApiError(caught, "The quiz attempt could not be started."));
    } finally {
      setStartingQuizId(null);
    }
  }

  async function handleSubmitAttempt(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!attempt || submitting) return;
    const answers = attempt.quiz.questions.map((question) => ({
      question_id: question.id,
      selected_option_id: selections[question.id],
    }));
    if (answers.some((answer) => !answer.selected_option_id)) {
      setSubmissionError("Answer every question before submitting the quiz.");
      return;
    }
    setSubmitting(true);
    setSubmissionError("");
    try {
      setReview(await submitQuizAttempt(token, attempt.id, answers));
    } catch (caught) {
      setSubmissionError(handleApiError(caught, "The quiz could not be submitted."));
    } finally {
      setSubmitting(false);
    }
  }

  const enrollmentRequired = role === "student" && error === "Enrollment required";

  return <section aria-labelledby="quiz-heading" className="mt-10 rounded-2xl border border-violet-100 bg-white p-6 shadow-sm sm:p-8">
    <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
      <div><p className="text-sm font-bold uppercase tracking-[0.18em] text-violet-700">Knowledge check</p><h2 id="quiz-heading" className="mt-2 text-2xl font-bold text-slate-950">Lesson quizzes</h2><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">Grounded multiple-choice quizzes generated from this lesson&apos;s processed material. Student answers are graded by the server.</p></div>
      <button type="button" onClick={() => void loadQuizzes()} disabled={loading} className="w-fit rounded-lg border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-60">{loading ? "Loading…" : "Refresh"}</button>
    </div>

    {ownsCourse && <div className="mt-6 rounded-xl border border-violet-100 bg-violet-50/50 p-5">
      <h3 className="font-semibold text-slate-950">Generate a grounded quiz</h3>
      <p className="mt-1 text-sm leading-6 text-slate-600">Generation requires usable chunks from at least one READY document and a configured AI provider.</p>
      {!hasReadyDocuments && <p className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">Upload and successfully process a PDF before generating a quiz.</p>}
      {generationError && <p role="alert" className="mt-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">{generationError}</p>}
      <form onSubmit={handleGenerate} className="mt-5 grid gap-4 sm:grid-cols-[1fr_9rem_auto] sm:items-end" noValidate>
        <div><label htmlFor="quiz-title" className="text-sm font-semibold text-slate-800">Quiz title</label><input id="quiz-title" value={title} onChange={(event) => setTitle(event.target.value)} maxLength={200} disabled={!hasReadyDocuments || generating} className="mt-2 block w-full rounded-xl border border-slate-300 px-3.5 py-3 outline-none focus:border-violet-500 focus:ring-2 focus:ring-violet-100 disabled:bg-slate-100" /></div>
        <div><label htmlFor="question-count" className="text-sm font-semibold text-slate-800">Questions</label><input id="question-count" type="number" min={1} max={10} step={1} value={questionCount} onChange={(event) => setQuestionCount(event.target.value)} disabled={!hasReadyDocuments || generating} className="mt-2 block w-full rounded-xl border border-slate-300 px-3.5 py-3 outline-none focus:border-violet-500 focus:ring-2 focus:ring-violet-100 disabled:bg-slate-100" /></div>
        <button type="submit" disabled={!hasReadyDocuments || !title.trim() || generating} className="rounded-xl bg-violet-600 px-5 py-3 font-semibold text-white hover:bg-violet-700 disabled:cursor-not-allowed disabled:bg-violet-400">{generating ? "Generating…" : "Generate quiz"}</button>
      </form>
    </div>}

    {loading && <p role="status" className="mt-6 rounded-xl bg-slate-50 p-5 text-sm text-slate-600">Loading available quizzes…</p>}
    {!loading && error && <div role="alert" className="mt-6 rounded-xl border border-red-200 bg-red-50 p-5 text-sm text-red-800"><p className="font-semibold">Quizzes unavailable</p><p className="mt-1">{error}</p>{enrollmentRequired && <Link href={`/courses/${courseId}`} className="mt-3 inline-flex font-semibold underline">Return to the course to enroll</Link>}</div>}
    {!loading && !error && quizzes.length === 0 && <div className="mt-6 rounded-xl border border-dashed border-slate-300 p-8 text-center"><p className="font-semibold text-slate-900">No quizzes available</p><p className="mt-2 text-sm text-slate-600">{ownsCourse ? "Generate the first quiz when lesson material is ready." : "The teacher has not published a quiz for this lesson."}</p></div>}

    {!loading && !error && quizzes.length > 0 && <ul className="mt-6 grid gap-3 sm:grid-cols-2">{quizzes.map((quiz) => <li key={quiz.id} className="rounded-xl border border-slate-200 p-4"><h3 className="font-semibold text-slate-950">{quiz.title}</h3><p className="mt-1 text-xs text-slate-500">Created {new Date(quiz.created_at).toLocaleDateString()}</p>{ownsCourse ? <button type="button" onClick={() => void handleViewTeacherQuiz(quiz.id)} disabled={viewingQuizId !== null} className="mt-4 text-sm font-semibold text-violet-700 hover:text-violet-900 disabled:opacity-50">{viewingQuizId === quiz.id ? "Opening…" : "View quiz and answer key"}</button> : role === "student" && <button type="button" onClick={() => void handleStartAttempt(quiz.id)} disabled={startingQuizId !== null || (attempt !== null && review === null)} className="mt-4 rounded-lg bg-violet-600 px-4 py-2 text-sm font-semibold text-white hover:bg-violet-700 disabled:cursor-not-allowed disabled:bg-violet-400">{startingQuizId === quiz.id ? "Starting…" : "Start quiz"}</button>}</li>)}</ul>}

    {teacherQuiz && ownsCourse && <div className="mt-8 border-t border-slate-200 pt-7"><h3 className="text-xl font-bold text-slate-950">{teacherQuiz.title}</h3><p className="mt-1 text-sm text-slate-500">Teacher view · {teacherQuiz.questions.length} questions</p><ol className="mt-5 space-y-5">{teacherQuiz.questions.map((question) => <li key={question.id} className="rounded-xl border border-slate-200 p-5"><p className="font-semibold text-slate-950">{question.position}. {question.question_text}</p><ul className="mt-3 space-y-2">{question.options.map((option) => <li key={option.id} className={`rounded-lg border px-3 py-2 text-sm ${option.is_correct ? "border-emerald-200 bg-emerald-50 text-emerald-800" : "border-slate-200 text-slate-700"}`}>{option.position}. {option.option_text}{option.is_correct && <span className="ml-2 font-semibold">Correct</span>}</li>)}</ul><p className="mt-3 text-sm leading-6 text-slate-600"><span className="font-semibold text-slate-800">Explanation:</span> {question.explanation}</p></li>)}</ol></div>}

    {submissionError && <p role="alert" className="mt-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{submissionError}</p>}
    {attempt && role === "student" && !review && <form onSubmit={handleSubmitAttempt} className="mt-8 border-t border-slate-200 pt-7"><div className="flex flex-wrap items-baseline justify-between gap-3"><div><p className="text-sm font-bold uppercase tracking-[0.16em] text-violet-700">Quiz attempt</p><h3 className="mt-1 text-xl font-bold text-slate-950">{attempt.quiz.title}</h3></div><p className="text-sm text-slate-500">{attempt.total_questions} questions</p></div><ol className="mt-6 space-y-6">{attempt.quiz.questions.map((question) => <li key={question.id} className="rounded-xl border border-slate-200 p-5"><fieldset><legend className="font-semibold leading-7 text-slate-950">{question.position}. {question.question_text}</legend><div className="mt-4 space-y-2">{question.options.map((option) => <label key={option.id} className="flex cursor-pointer gap-3 rounded-lg border border-slate-200 px-4 py-3 text-sm text-slate-700 hover:border-violet-300 has-checked:border-violet-500 has-checked:bg-violet-50"><input type="radio" name={`question-${question.id}`} value={option.id} checked={selections[question.id] === option.id} onChange={() => setSelections((current) => ({ ...current, [question.id]: option.id }))} disabled={submitting} className="mt-0.5 h-4 w-4 accent-violet-600" /><span>{option.option_text}</span></label>)}</div></fieldset></li>)}</ol><button type="submit" disabled={submitting} className="mt-6 rounded-xl bg-violet-600 px-5 py-3 font-semibold text-white hover:bg-violet-700 disabled:bg-violet-400">{submitting ? "Submitting for grading…" : "Submit answers"}</button><p className="mt-2 text-xs text-slate-500">All questions are required. Correctness is determined only after server submission.</p></form>}

    {review && <div className="mt-8 border-t border-slate-200 pt-7"><div className="rounded-xl border border-emerald-200 bg-emerald-50 p-5"><p className="text-sm font-semibold text-emerald-800">Server-graded result</p><p className="mt-2 text-3xl font-bold text-emerald-950">{review.score_percent}%</p><p className="mt-1 text-sm text-emerald-800">{review.correct_count} of {review.total_questions} correct</p></div><ol className="mt-5 space-y-4">{review.answers.map((answer, index) => <li key={answer.question_id} className={`rounded-xl border p-5 ${answer.is_correct ? "border-emerald-200" : "border-red-200"}`}><p className="font-semibold text-slate-950">{index + 1}. {answer.question_text}</p><p className="mt-3 text-sm text-slate-700"><span className="font-semibold">Your answer:</span> {answer.selected_option_text}</p><p className={`mt-1 text-sm font-semibold ${answer.is_correct ? "text-emerald-700" : "text-red-700"}`}>{answer.is_correct ? "Correct" : `Correct answer: ${answer.correct_option_text}`}</p><p className="mt-3 text-sm leading-6 text-slate-600">{answer.explanation}</p></li>)}</ol></div>}
  </section>;
}
