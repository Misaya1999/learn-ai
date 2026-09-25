"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { useAuth } from "@/lib/auth-context";
import { ApiError, createLesson, enrollInCourse, getCourse, listCourseLessons, listMyEnrollments, type Course, type Lesson } from "@/lib/api";

export default function CourseDetailPage() {
  const params = useParams<{ courseId: string }>();
  const courseId = params.courseId;
  const { user, token, ready } = useAuth();
  const [course, setCourse] = useState<Course | null>(null);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [enrolled, setEnrolled] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showLessonForm, setShowLessonForm] = useState(false);
  const [lessonTitle, setLessonTitle] = useState("");
  const [lessonContent, setLessonContent] = useState("");
  const [lessonPosition, setLessonPosition] = useState("1");
  const [formError, setFormError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [enrolling, setEnrolling] = useState(false);
  const [enrollmentError, setEnrollmentError] = useState("");

  const loadCourse = useCallback(async () => {
    if (!token || !user || !courseId) return;
    setLoading(true);
    setError("");
    try {
      const [courseData, lessonData, enrollmentData] = await Promise.all([
        getCourse(token, courseId),
        listCourseLessons(token, courseId),
        user.role === "student" ? listMyEnrollments(token) : Promise.resolve([]),
      ]);
      setCourse(courseData);
      setLessons(lessonData);
      setEnrolled(enrollmentData.some((item) => item.course_id === courseId));
      setLessonPosition(String(Math.max(0, ...lessonData.map((lesson) => lesson.position)) + 1));
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "This course could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, [token, user, courseId]);

  useEffect(() => {
    if (ready && token && user) queueMicrotask(() => void loadCourse());
  }, [ready, token, user, loadCourse]);

  async function handleCreateLesson(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) return;
    const normalizedTitle = lessonTitle.trim();
    const position = Number(lessonPosition);
    if (!normalizedTitle || normalizedTitle.length > 200) {
      setFormError("Title must contain between 1 and 200 characters.");
      return;
    }
    if (!Number.isInteger(position) || position <= 0) {
      setFormError("Position must be a positive whole number.");
      return;
    }
    setSubmitting(true);
    setFormError("");
    try {
      const lesson = await createLesson(token, courseId, { title: normalizedTitle, content: lessonContent.trim() || null, position });
      setLessons((current) => [...current, lesson].sort((a, b) => a.position - b.position || a.created_at.localeCompare(b.created_at) || a.id.localeCompare(b.id)));
      setLessonTitle("");
      setLessonContent("");
      setLessonPosition(String(Math.max(position, ...lessons.map((item) => item.position)) + 1));
      setShowLessonForm(false);
    } catch (caught) {
      setFormError(caught instanceof ApiError ? caught.message : "The lesson could not be created.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleEnrollment() {
    if (!token) return;
    setEnrolling(true);
    setEnrollmentError("");
    try {
      await enrollInCourse(token, courseId);
      setEnrolled(true);
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 409) setEnrolled(true);
      else setEnrollmentError(caught instanceof ApiError ? caught.message : "Enrollment was not successful.");
    } finally {
      setEnrolling(false);
    }
  }

  const ownsCourse = user?.role === "teacher" && course?.teacher_id === user.id;

  return (
    <AppShell>
      <main className="mx-auto max-w-5xl px-5 py-10 sm:px-8 sm:py-14">
        <Link href="/courses" className="inline-flex items-center gap-2 text-sm font-semibold text-slate-600 hover:text-indigo-700"><span aria-hidden="true">←</span> All courses</Link>
        {loading && <div role="status" className="mt-8 rounded-2xl border border-slate-200 bg-white p-10 text-center text-slate-600">Loading course…</div>}
        {!loading && error && <div role="alert" className="mt-8 rounded-2xl border border-red-200 bg-red-50 p-6 text-red-800"><p className="font-semibold">Course unavailable</p><p className="mt-1 text-sm">{error}</p><button type="button" onClick={() => void loadCourse()} className="mt-4 rounded-lg border border-red-300 px-3 py-2 text-sm font-semibold">Try again</button></div>}

        {!loading && !error && course && <>
          <section className="mt-7 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
            <div className="flex flex-col gap-6 sm:flex-row sm:items-start sm:justify-between"><div><div className="flex flex-wrap items-center gap-2"><p className="text-sm font-bold uppercase tracking-[0.18em] text-indigo-700">Course</p>{ownsCourse && <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700">You own this course</span>}{enrolled && <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700">Enrolled</span>}</div><h1 className="mt-3 text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl">{course.title}</h1><p className="mt-4 max-w-3xl leading-7 text-slate-600">{course.description || "No description provided."}</p><p className="mt-4 text-sm text-slate-500">Created {new Date(course.created_at).toLocaleDateString()}</p></div>{user?.role === "student" && !enrolled && <button type="button" disabled={enrolling} onClick={() => void handleEnrollment()} className="shrink-0 rounded-xl bg-indigo-600 px-5 py-3 font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-indigo-400">{enrolling ? "Enrolling…" : "Enroll in course"}</button>}</div>
            {enrollmentError && <p role="alert" className="mt-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{enrollmentError}</p>}
          </section>

          <section aria-labelledby="lessons-heading" className="mt-10">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div><p className="text-sm font-bold uppercase tracking-[0.18em] text-indigo-700">Course content</p><h2 id="lessons-heading" className="mt-2 text-2xl font-bold text-slate-950 sm:text-3xl">Lessons</h2></div>{ownsCourse && <button type="button" onClick={() => setShowLessonForm((value) => !value)} className="rounded-xl bg-indigo-600 px-4 py-2.5 font-semibold text-white hover:bg-indigo-700">{showLessonForm ? "Close form" : "Create lesson"}</button>}</div>

            {showLessonForm && ownsCourse && <div className="mt-6 rounded-2xl border border-indigo-100 bg-white p-6 shadow-sm"><h3 className="text-lg font-semibold text-slate-950">Add a lesson</h3>{formError && <p role="alert" className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{formError}</p>}<form onSubmit={handleCreateLesson} noValidate className="mt-5 grid gap-5"><div><label htmlFor="lesson-title" className="text-sm font-semibold text-slate-800">Lesson title</label><input id="lesson-title" value={lessonTitle} onChange={(event) => setLessonTitle(event.target.value)} required maxLength={200} className="mt-2 block w-full rounded-xl border border-slate-300 px-3.5 py-3 outline-none focus:border-indigo-500 focus:ring-3 focus:ring-indigo-100" /></div><div><label htmlFor="lesson-content" className="text-sm font-semibold text-slate-800">Content <span className="font-normal text-slate-500">(optional)</span></label><textarea id="lesson-content" value={lessonContent} onChange={(event) => setLessonContent(event.target.value)} rows={5} className="mt-2 block w-full resize-y rounded-xl border border-slate-300 px-3.5 py-3 outline-none focus:border-indigo-500 focus:ring-3 focus:ring-indigo-100" /></div><div className="max-w-40"><label htmlFor="lesson-position" className="text-sm font-semibold text-slate-800">Position</label><input id="lesson-position" type="number" min={1} step={1} value={lessonPosition} onChange={(event) => setLessonPosition(event.target.value)} required className="mt-2 block w-full rounded-xl border border-slate-300 px-3.5 py-3 outline-none focus:border-indigo-500 focus:ring-3 focus:ring-indigo-100" /></div><button type="submit" disabled={submitting} className="w-fit rounded-xl bg-indigo-600 px-5 py-3 font-semibold text-white hover:bg-indigo-700 disabled:bg-indigo-400">{submitting ? "Creating…" : "Create lesson"}</button></form></div>}

            {lessons.length === 0 ? <div className="mt-6 rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center"><h3 className="font-semibold text-slate-900">No lessons yet</h3><p className="mt-2 text-slate-600">{ownsCourse ? "Create the first lesson for this course." : "The teacher has not added any lessons."}</p></div> : <ol className="mt-6 space-y-4">{lessons.map((lesson) => <li key={lesson.id} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6"><div className="flex gap-4"><span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-indigo-50 text-sm font-bold text-indigo-700">{lesson.position}</span><div className="min-w-0 flex-1"><h3 className="text-lg font-semibold text-slate-950">{lesson.title}</h3>{lesson.content ? <p className="mt-2 line-clamp-3 whitespace-pre-line leading-7 text-slate-600">{lesson.content}</p> : <p className="mt-2 text-sm text-slate-500">No lesson content provided.</p>}<Link href={`/courses/${course.id}/lessons/${lesson.id}`} className="mt-4 inline-flex items-center text-sm font-semibold text-indigo-700 hover:text-indigo-800">Open lesson <span aria-hidden="true" className="ml-2">→</span></Link></div></div></li>)}</ol>}
          </section>
        </>}
      </main>
    </AppShell>
  );
}
