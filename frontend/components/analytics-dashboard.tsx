"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  ApiError,
  getCourseAnalytics,
  getCourseLessonAnalytics,
  getCourseQuestionAnalytics,
  getCourseStudentAnalytics,
  getStudentAnalytics,
  getStudentLessonAnalytics,
  getStudentProgress,
  listCourses,
  type Course,
  type CourseAnalyticsOverview,
  type CourseLessonAnalytics,
  type CourseQuestionAnalytics,
  type CourseStudentAnalytics,
  type StudentAnalyticsOverview,
  type StudentLessonAnalytics,
  type StudentProgressPoint,
} from "@/lib/api";

interface AnalyticsProps {
  token: string;
  userId: string;
  onUnauthorized: () => void;
}

function formatPercent(value: string | null): string {
  return value === null ? "No data" : `${value}%`;
}

function MetricCard({ label, value, help }: { label: string; value: string | number; help?: string }) {
  return <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><dt className="text-sm font-semibold text-slate-600">{label}</dt><dd className="mt-2 text-2xl font-bold text-slate-950">{value}</dd>{help && <p className="mt-2 text-xs leading-5 text-slate-500">{help}</p>}</div>;
}

function PercentageBar({ value, label }: { value: string | null; label: string }) {
  if (value === null) return <span className="text-sm text-slate-500">No data</span>;
  const width = Math.min(100, Math.max(0, Number(value)));
  return <div className="min-w-32"><div className="flex justify-between gap-3 text-xs"><span className="text-slate-500">{label}</span><span className="font-semibold text-slate-800">{value}%</span></div><div className="mt-1.5 h-2 overflow-hidden rounded-full bg-slate-100" aria-hidden="true"><div className="h-full rounded-full bg-indigo-600" style={{ width: `${width}%` }} /></div></div>;
}

function AnalyticsError({ message, onRetry }: { message: string; onRetry: () => void }) {
  return <div role="alert" className="rounded-2xl border border-red-200 bg-red-50 p-6 text-red-800"><p className="font-semibold">Analytics are unavailable</p><p className="mt-1 text-sm">{message}</p><button type="button" onClick={onRetry} className="mt-4 rounded-lg border border-red-300 px-3 py-2 text-sm font-semibold">Try again</button></div>;
}

export function StudentAnalyticsDashboard({ token, onUnauthorized }: Omit<AnalyticsProps, "userId">) {
  const [overview, setOverview] = useState<StudentAnalyticsOverview | null>(null);
  const [lessons, setLessons] = useState<StudentLessonAnalytics[]>([]);
  const [progress, setProgress] = useState<StudentProgressPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [overviewData, lessonData, progressData] = await Promise.all([
        getStudentAnalytics(token),
        getStudentLessonAnalytics(token),
        getStudentProgress(token),
      ]);
      setOverview(overviewData);
      setLessons(lessonData);
      setProgress(progressData);
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 401) onUnauthorized();
      else setError(caught instanceof ApiError ? caught.message : "Your learning analytics could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, [token, onUnauthorized]);

  useEffect(() => { queueMicrotask(() => void load()); }, [load]);

  if (loading) return <div role="status" className="rounded-2xl border border-slate-200 bg-white p-10 text-center text-slate-600">Loading your learning analytics…</div>;
  if (error) return <AnalyticsError message={error} onRetry={() => void load()} />;
  if (!overview) return null;

  const hasAttempts = overview.total_submitted_attempts > 0;
  return <div className="space-y-10">
    {!hasAttempts && <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center"><h2 className="text-lg font-semibold text-slate-950">No submitted quiz attempts yet</h2><p className="mt-2 text-slate-600">Complete and submit a lesson quiz to begin building your analytics.</p><Link href="/courses" className="mt-4 inline-flex font-semibold text-indigo-700">Browse courses <span className="ml-2" aria-hidden="true">→</span></Link></div>}

    {hasAttempts && <section aria-labelledby="student-overview-heading"><h2 id="student-overview-heading" className="text-xl font-bold text-slate-950">Performance overview</h2><dl className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4"><MetricCard label="Average score" value={formatPercent(overview.average_score)} help="Mean of your submitted attempt score percentages." /><MetricCard label="Weighted accuracy" value={formatPercent(overview.overall_accuracy_percent)} help="Total correct answers divided by total questions answered." /><MetricCard label="Best attempt score" value={formatPercent(overview.best_score)} /><MetricCard label="Submitted attempts" value={overview.total_submitted_attempts} help={`${overview.distinct_quizzes_attempted} quizzes across ${overview.distinct_lessons_practiced} lessons`} /></dl><p className="mt-4 text-sm text-slate-600">You answered <span className="font-semibold text-slate-900">{overview.total_correct_answers}</span> of <span className="font-semibold text-slate-900">{overview.total_questions_answered}</span> questions correctly across submitted attempts.</p></section>}

    <section aria-labelledby="student-lessons-heading"><h2 id="student-lessons-heading" className="text-xl font-bold text-slate-950">Lesson performance</h2>{lessons.length === 0 ? <p className="mt-4 rounded-xl border border-dashed border-slate-300 bg-white p-6 text-center text-slate-600">No lesson performance is available yet.</p> : <div className="mt-5 overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-sm"><table className="w-full min-w-3xl text-left text-sm"><thead className="bg-slate-50 text-slate-600"><tr><th className="px-5 py-3 font-semibold">Lesson</th><th className="px-5 py-3 font-semibold">Attempts</th><th className="px-5 py-3 font-semibold">Average score</th><th className="px-5 py-3 font-semibold">Best score</th><th className="px-5 py-3 font-semibold">Weighted accuracy</th></tr></thead><tbody className="divide-y divide-slate-200">{lessons.map((lesson) => <tr key={lesson.lesson_id}><td className="px-5 py-4 font-semibold text-slate-900">{lesson.lesson_title}</td><td className="px-5 py-4 text-slate-600">{lesson.submitted_attempts}</td><td className="px-5 py-4 text-slate-700">{lesson.average_score}%</td><td className="px-5 py-4 text-slate-700">{lesson.best_score}%</td><td className="px-5 py-4"><PercentageBar value={lesson.accuracy_percent} label={`${lesson.correct_answers}/${lesson.total_questions} correct`} /></td></tr>)}</tbody></table></div>}</section>

    <section aria-labelledby="progress-heading"><h2 id="progress-heading" className="text-xl font-bold text-slate-950">Submitted attempt timeline</h2>{progress.length === 0 ? <p className="mt-4 rounded-xl border border-dashed border-slate-300 bg-white p-6 text-center text-slate-600">No submitted attempts to show.</p> : <ol className="mt-5 space-y-3">{progress.map((point) => <li key={point.attempt_id} className="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-5 shadow-sm sm:flex-row sm:items-center sm:justify-between"><div><p className="font-semibold text-slate-950">{point.quiz_title}</p><p className="mt-1 text-sm text-slate-500">{point.lesson_title} · {new Date(point.submitted_at).toLocaleString()}</p></div><span className="text-lg font-bold text-indigo-700">{point.score_percent}%</span></li>)}</ol>}</section>
  </div>;
}

export function TeacherAnalyticsDashboard({ token, userId, onUnauthorized }: AnalyticsProps) {
  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState("");
  const [overview, setOverview] = useState<CourseAnalyticsOverview | null>(null);
  const [students, setStudents] = useState<CourseStudentAnalytics[]>([]);
  const [lessons, setLessons] = useState<CourseLessonAnalytics[]>([]);
  const [questions, setQuestions] = useState<CourseQuestionAnalytics[]>([]);
  const [loadingCourses, setLoadingCourses] = useState(true);
  const [loadingAnalytics, setLoadingAnalytics] = useState(false);
  const [error, setError] = useState("");

  const loadCourses = useCallback(async () => {
    setLoadingCourses(true);
    setError("");
    try {
      const owned = (await listCourses(token)).filter((course) => course.teacher_id === userId);
      setCourses(owned);
      setSelectedCourseId((current) => owned.some((course) => course.id === current) ? current : owned[0]?.id ?? "");
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 401) onUnauthorized();
      else setError(caught instanceof ApiError ? caught.message : "Your courses could not be loaded.");
    } finally {
      setLoadingCourses(false);
    }
  }, [token, userId, onUnauthorized]);

  const loadAnalytics = useCallback(async (courseId: string) => {
    setLoadingAnalytics(true);
    setError("");
    try {
      const [overviewData, studentData, lessonData, questionData] = await Promise.all([
        getCourseAnalytics(token, courseId),
        getCourseStudentAnalytics(token, courseId),
        getCourseLessonAnalytics(token, courseId),
        getCourseQuestionAnalytics(token, courseId),
      ]);
      setOverview(overviewData); setStudents(studentData); setLessons(lessonData); setQuestions(questionData);
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 401) onUnauthorized();
      else setError(caught instanceof ApiError ? caught.message : "Course analytics could not be loaded.");
    } finally {
      setLoadingAnalytics(false);
    }
  }, [token, onUnauthorized]);

  useEffect(() => { queueMicrotask(() => void loadCourses()); }, [loadCourses]);
  useEffect(() => { if (selectedCourseId) queueMicrotask(() => void loadAnalytics(selectedCourseId)); }, [selectedCourseId, loadAnalytics]);

  if (loadingCourses) return <div role="status" className="rounded-2xl border border-slate-200 bg-white p-10 text-center text-slate-600">Loading your courses…</div>;
  if (error && !selectedCourseId) return <AnalyticsError message={error} onRetry={() => void loadCourses()} />;
  if (courses.length === 0) return <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center"><h2 className="text-lg font-semibold text-slate-950">No courses to analyze</h2><p className="mt-2 text-slate-600">Create a course before viewing teacher analytics.</p><Link href="/courses" className="mt-4 inline-flex font-semibold text-indigo-700">Create a course <span className="ml-2" aria-hidden="true">→</span></Link></div>;

  return <div className="space-y-10">
    <section aria-labelledby="course-selection-heading" className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><label id="course-selection-heading" htmlFor="analytics-course" className="text-sm font-semibold text-slate-700">Course analytics</label><select id="analytics-course" value={selectedCourseId} onChange={(event) => setSelectedCourseId(event.target.value)} className="mt-2 block w-full max-w-xl rounded-xl border border-slate-300 bg-white px-3.5 py-3 font-medium text-slate-900 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100">{courses.map((course) => <option key={course.id} value={course.id}>{course.title}</option>)}</select><p className="mt-2 text-xs text-slate-500">Only courses owned by your account are available.</p></section>
    {loadingAnalytics && <div role="status" className="rounded-2xl border border-slate-200 bg-white p-10 text-center text-slate-600">Loading course analytics…</div>}
    {!loadingAnalytics && error && <AnalyticsError message={error} onRetry={() => void loadAnalytics(selectedCourseId)} />}
    {!loadingAnalytics && !error && overview && <>
      <section aria-labelledby="course-overview-heading"><h2 id="course-overview-heading" className="text-xl font-bold text-slate-950">Course overview</h2><dl className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4"><MetricCard label="Enrolled students" value={overview.enrolled_students} /><MetricCard label="Students with attempts" value={overview.students_with_submitted_attempts} /><MetricCard label="Average score" value={formatPercent(overview.average_score)} help="Mean of submitted attempt score percentages." /><MetricCard label="Weighted accuracy" value={formatPercent(overview.overall_accuracy_percent)} help="Total correct answers divided by total questions answered." /></dl>{overview.total_submitted_attempts === 0 ? <p className="mt-4 rounded-xl border border-dashed border-slate-300 bg-white p-5 text-center text-slate-600">No submitted attempts exist for this course yet. Empty analytics do not indicate poor performance.</p> : <p className="mt-4 text-sm text-slate-600">{overview.total_submitted_attempts} submitted attempts · {overview.total_correct_answers} of {overview.total_questions_answered} answers correct</p>}</section>

      <section aria-labelledby="student-performance-heading"><h2 id="student-performance-heading" className="text-xl font-bold text-slate-950">Student performance</h2>{students.length === 0 ? <p className="mt-4 rounded-xl border border-dashed border-slate-300 bg-white p-6 text-center text-slate-600">No students are enrolled in this course.</p> : <div className="mt-5 overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-sm"><table className="w-full min-w-3xl text-left text-sm"><thead className="bg-slate-50 text-slate-600"><tr><th className="px-5 py-3 font-semibold">Student</th><th className="px-5 py-3 font-semibold">Attempts</th><th className="px-5 py-3 font-semibold">Average score</th><th className="px-5 py-3 font-semibold">Best score</th><th className="px-5 py-3 font-semibold">Weighted accuracy</th></tr></thead><tbody className="divide-y divide-slate-200">{students.map((student) => <tr key={student.student_id}><td className="px-5 py-4 font-semibold text-slate-900">{student.student_name}</td><td className="px-5 py-4 text-slate-600">{student.submitted_attempts}</td><td className="px-5 py-4 text-slate-700">{formatPercent(student.average_score)}</td><td className="px-5 py-4 text-slate-700">{formatPercent(student.best_score)}</td><td className="px-5 py-4"><PercentageBar value={student.accuracy_percent} label={student.total_questions ? `${student.correct_answers}/${student.total_questions} correct` : "No answers"} /></td></tr>)}</tbody></table></div>}</section>

      <section aria-labelledby="lesson-performance-heading"><h2 id="lesson-performance-heading" className="text-xl font-bold text-slate-950">Lesson performance</h2>{lessons.length === 0 ? <p className="mt-4 rounded-xl border border-dashed border-slate-300 bg-white p-6 text-center text-slate-600">This course has no lessons.</p> : <div className="mt-5 grid gap-4 md:grid-cols-2">{lessons.map((lesson) => <article key={lesson.lesson_id} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><h3 className="font-semibold text-slate-950">{lesson.lesson_title}</h3><p className="mt-1 text-xs text-slate-500">{lesson.quizzes} quizzes · {lesson.submitted_attempts} submitted attempts · {lesson.participating_students} participating students</p><dl className="mt-4 grid grid-cols-2 gap-4 text-sm"><div><dt className="text-slate-500">Average score</dt><dd className="mt-1 font-semibold text-slate-900">{formatPercent(lesson.average_score)}</dd></div><div><dt className="text-slate-500">Weighted accuracy</dt><dd className="mt-1 font-semibold text-slate-900">{formatPercent(lesson.accuracy_percent)}</dd></div></dl></article>)}</div>}</section>

      <section aria-labelledby="question-performance-heading"><h2 id="question-performance-heading" className="text-xl font-bold text-slate-950">Question performance</h2>{questions.length === 0 ? <p className="mt-4 rounded-xl border border-dashed border-slate-300 bg-white p-6 text-center text-slate-600">No quiz questions are available for this course.</p> : <div className="mt-5 space-y-3">{questions.map((question) => <article key={question.question_id} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><p className="font-medium leading-6 text-slate-900">{question.question_text}</p><div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between"><p className="text-sm text-slate-500">{question.total_answers === 0 ? "No submitted answers" : `${question.correct_answers} correct · ${question.incorrect_answers} incorrect · ${question.total_answers} total`}</p><PercentageBar value={question.accuracy_percent} label="Accuracy" /></div></article>)}</div>}</section>
    </>}
  </div>;
}
