"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { useAuth } from "@/lib/auth-context";
import { ApiError, createCourse, listCourses, listMyEnrollments, type Course } from "@/lib/api";

export default function CoursesPage() {
  const router = useRouter();
  const { user, token, ready } = useAuth();
  const [courses, setCourses] = useState<Course[]>([]);
  const [enrolledCourseIds, setEnrolledCourseIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [formError, setFormError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const loadCourses = useCallback(async () => {
    if (!token || !user) return;
    setLoading(true);
    setError("");
    try {
      const [courseData, enrollmentData] = await Promise.all([
        listCourses(token),
        user.role === "student" ? listMyEnrollments(token) : Promise.resolve([]),
      ]);
      setCourses(courseData);
      setEnrolledCourseIds(new Set(enrollmentData.map((item) => item.course_id)));
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Courses could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, [token, user]);

  useEffect(() => {
    if (ready && token && user) queueMicrotask(() => void loadCourses());
  }, [ready, token, user, loadCourses]);

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) return;
    const normalizedTitle = title.trim();
    if (!normalizedTitle || normalizedTitle.length > 200) {
      setFormError("Title must contain between 1 and 200 characters.");
      return;
    }
    setSubmitting(true);
    setFormError("");
    try {
      const course = await createCourse(token, { title: normalizedTitle, description: description.trim() || null });
      router.push(`/courses/${course.id}`);
    } catch (caught) {
      setFormError(caught instanceof ApiError ? caught.message : "The course could not be created.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AppShell>
      <main className="mx-auto max-w-7xl px-5 py-10 sm:px-8 sm:py-14 lg:px-10">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
          <div><p className="text-sm font-bold uppercase tracking-[0.18em] text-indigo-700">Learning catalog</p><h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl">Courses</h1><p className="mt-3 max-w-2xl leading-7 text-slate-600">{user?.role === "teacher" ? "Create a course and organize its lessons." : "Browse available courses and open one to enroll."}</p></div>
          {user?.role === "teacher" && <button type="button" onClick={() => setShowForm((value) => !value)} className="inline-flex items-center justify-center rounded-xl bg-indigo-600 px-4 py-3 font-semibold text-white shadow-sm transition hover:bg-indigo-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600">{showForm ? "Close form" : "Create course"}</button>}
        </div>

        {showForm && user?.role === "teacher" && <section aria-labelledby="create-course-heading" className="mt-8 rounded-2xl border border-indigo-100 bg-white p-6 shadow-sm sm:p-8"><h2 id="create-course-heading" className="text-xl font-semibold text-slate-950">Create a new course</h2><p className="mt-1 text-sm text-slate-600">You will be assigned as the course owner automatically.</p>{formError && <p role="alert" className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{formError}</p>}<form onSubmit={handleCreate} className="mt-6 grid gap-5" noValidate><div><label htmlFor="course-title" className="text-sm font-semibold text-slate-800">Course title</label><input id="course-title" value={title} onChange={(event) => setTitle(event.target.value)} required maxLength={200} className="mt-2 block w-full rounded-xl border border-slate-300 px-3.5 py-3 outline-none focus:border-indigo-500 focus:ring-3 focus:ring-indigo-100" /></div><div><label htmlFor="course-description" className="text-sm font-semibold text-slate-800">Description <span className="font-normal text-slate-500">(optional)</span></label><textarea id="course-description" value={description} onChange={(event) => setDescription(event.target.value)} rows={4} className="mt-2 block w-full resize-y rounded-xl border border-slate-300 px-3.5 py-3 outline-none focus:border-indigo-500 focus:ring-3 focus:ring-indigo-100" /></div><div><button type="submit" disabled={submitting} className="rounded-xl bg-indigo-600 px-5 py-3 font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-indigo-400">{submitting ? "Creating…" : "Create course"}</button></div></form></section>}

        <section aria-label="Course list" className="mt-10">
          {loading && <div role="status" className="rounded-2xl border border-slate-200 bg-white p-10 text-center text-slate-600">Loading courses…</div>}
          {!loading && error && <div role="alert" className="rounded-2xl border border-red-200 bg-red-50 p-6 text-red-800"><p className="font-semibold">Courses are unavailable</p><p className="mt-1 text-sm">{error}</p><button type="button" onClick={() => void loadCourses()} className="mt-4 rounded-lg border border-red-300 px-3 py-2 text-sm font-semibold">Try again</button></div>}
          {!loading && !error && courses.length === 0 && <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center"><h2 className="text-lg font-semibold text-slate-900">No courses yet</h2><p className="mt-2 text-slate-600">{user?.role === "teacher" ? "Create the first course to begin adding lessons." : "There are no courses available to browse."}</p></div>}
          {!loading && !error && courses.length > 0 && <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">{courses.map((course) => {
            const owned = user?.role === "teacher" && course.teacher_id === user.id;
            const enrolled = user?.role === "student" && enrolledCourseIds.has(course.id);
            return <article key={course.id} className="flex min-h-60 flex-col rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex items-start justify-between gap-3"><span className="flex h-11 w-11 items-center justify-center rounded-xl bg-indigo-50 text-xl text-indigo-700">▤</span>{(owned || enrolled) && <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700">{owned ? "Your course" : "Enrolled"}</span>}</div><h2 className="mt-5 text-xl font-semibold text-slate-950">{course.title}</h2><p className="mt-2 line-clamp-3 flex-1 leading-7 text-slate-600">{course.description || "No description provided."}</p><Link href={`/courses/${course.id}`} className="mt-5 inline-flex items-center text-sm font-semibold text-indigo-700 hover:text-indigo-800">View course <span aria-hidden="true" className="ml-2">→</span></Link></article>;
          })}</div>}
        </section>
      </main>
    </AppShell>
  );
}
