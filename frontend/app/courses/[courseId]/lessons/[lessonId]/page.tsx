"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { ChangeEvent, FormEvent, useCallback, useEffect, useRef, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { LessonQuiz } from "@/components/lesson-quiz";
import { useAuth } from "@/lib/auth-context";
import {
  ApiError,
  MAX_DOCUMENT_UPLOAD_BYTES,
  askLessonQuestion,
  deleteDocument,
  getCourse,
  getLesson,
  listLessonDocuments,
  uploadLessonDocument,
  type Course,
  type DocumentStatus,
  type Lesson,
  type LessonDocument,
  type TutorAnswer,
} from "@/lib/api";

const statusStyles: Record<DocumentStatus, string> = {
  processing: "bg-amber-50 text-amber-800 ring-amber-200",
  ready: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  failed: "bg-red-50 text-red-700 ring-red-200",
};

function formatBytes(value: number): string {
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

export default function LessonDetailPage() {
  const params = useParams<{ courseId: string; lessonId: string }>();
  const { courseId, lessonId } = params;
  const router = useRouter();
  const { user, token, ready, signOut } = useAuth();
  const fileInput = useRef<HTMLInputElement>(null);
  const [course, setCourse] = useState<Course | null>(null);
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [documents, setDocuments] = useState<LessonDocument[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [documentsError, setDocumentsError] = useState("");
  const [refreshing, setRefreshing] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [success, setSuccess] = useState("");
  const [uploading, setUploading] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [question, setQuestion] = useState("");
  const [submittedQuestion, setSubmittedQuestion] = useState("");
  const [tutorAnswer, setTutorAnswer] = useState<TutorAnswer | null>(null);
  const [tutorError, setTutorError] = useState("");
  const [askingTutor, setAskingTutor] = useState(false);

  const handleUnauthorized = useCallback(() => {
    signOut();
    router.replace("/login");
  }, [signOut, router]);

  const refreshDocuments = useCallback(async () => {
    if (!token || !lessonId) return;
    setRefreshing(true);
    setDocumentsError("");
    try {
      const data = await listLessonDocuments(token, lessonId);
      setDocuments(data);
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 401) handleUnauthorized();
      else setDocumentsError(caught instanceof ApiError ? caught.message : "Documents could not be loaded.");
    } finally {
      setRefreshing(false);
    }
  }, [token, lessonId, handleUnauthorized]);

  const loadLesson = useCallback(async () => {
    if (!token || !courseId || !lessonId) return;
    setLoading(true);
    setError("");
    try {
      const [courseData, lessonData, documentData] = await Promise.all([
        getCourse(token, courseId),
        getLesson(token, lessonId),
        listLessonDocuments(token, lessonId),
      ]);
      if (lessonData.course_id !== courseId) {
        setError("This lesson does not belong to the selected course.");
        return;
      }
      setCourse(courseData);
      setLesson(lessonData);
      setDocuments(documentData);
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 401) {
        handleUnauthorized();
        return;
      }
      setError(caught instanceof ApiError ? caught.message : "This lesson could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, [token, courseId, lessonId, handleUnauthorized]);

  useEffect(() => {
    if (ready && token && user) queueMicrotask(() => void loadLesson());
  }, [ready, token, user, loadLesson]);

  function handleFileSelection(event: ChangeEvent<HTMLInputElement>) {
    setUploadError("");
    setSuccess("");
    const file = event.target.files?.[0] ?? null;
    if (!file) {
      setSelectedFile(null);
      return;
    }
    if (!file.name.toLowerCase().endsWith(".pdf") || file.type !== "application/pdf") {
      setSelectedFile(null);
      setUploadError("Choose a PDF file with the application/pdf content type.");
      event.target.value = "";
      return;
    }
    if (file.size === 0) {
      setSelectedFile(null);
      setUploadError("The selected PDF is empty.");
      event.target.value = "";
      return;
    }
    if (file.size > MAX_DOCUMENT_UPLOAD_BYTES) {
      setSelectedFile(null);
      setUploadError("The selected PDF exceeds the 10 MB upload limit.");
      event.target.value = "";
      return;
    }
    setSelectedFile(file);
  }

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !selectedFile || uploading) return;
    setUploading(true);
    setUploadError("");
    setSuccess("");
    try {
      const uploaded = await uploadLessonDocument(token, lessonId, selectedFile);
      setDocuments((current) => [...current.filter((item) => item.id !== uploaded.id), uploaded]);
      setSuccess(`${uploaded.original_filename} was processed successfully.`);
      setSelectedFile(null);
      if (fileInput.current) fileInput.current.value = "";
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 401) {
        handleUnauthorized();
      } else {
        setUploadError(caught instanceof ApiError ? caught.message : "The PDF could not be uploaded.");
        await refreshDocuments();
      }
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(document: LessonDocument) {
    if (!token || deletingId || !window.confirm(`Delete ${document.original_filename}?`)) return;
    setDeletingId(document.id);
    setUploadError("");
    setSuccess("");
    try {
      await deleteDocument(token, document.id);
      setDocuments((current) => current.filter((item) => item.id !== document.id));
      setSuccess(`${document.original_filename} was deleted.`);
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 401) handleUnauthorized();
      else setUploadError(caught instanceof ApiError ? caught.message : "The document could not be deleted.");
    } finally {
      setDeletingId(null);
    }
  }

  async function handleAskTutor(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalizedQuestion = question.trim();
    if (!token || !normalizedQuestion || askingTutor) return;
    setAskingTutor(true);
    setTutorError("");
    setTutorAnswer(null);
    setSubmittedQuestion(normalizedQuestion);
    try {
      const answer = await askLessonQuestion(token, lessonId, normalizedQuestion);
      setTutorAnswer(answer);
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 401) {
        handleUnauthorized();
      } else {
        setTutorError(caught instanceof ApiError ? caught.message : "The AI Tutor could not answer this question.");
      }
    } finally {
      setAskingTutor(false);
    }
  }

  const ownsCourse = user?.role === "teacher" && course?.teacher_id === user.id;
  const hasReadyDocuments = documents.some((document) => document.status === "ready");

  return (
    <AppShell>
      <main className="mx-auto max-w-5xl px-5 py-10 sm:px-8 sm:py-14">
        <Link href={`/courses/${courseId}`} className="inline-flex items-center gap-2 text-sm font-semibold text-slate-600 hover:text-indigo-700"><span aria-hidden="true">←</span> Back to course</Link>

        {loading && <div role="status" className="mt-8 rounded-2xl border border-slate-200 bg-white p-10 text-center text-slate-600">Loading lesson…</div>}
        {!loading && error && <div role="alert" className="mt-8 rounded-2xl border border-red-200 bg-red-50 p-6 text-red-800"><p className="font-semibold">Lesson unavailable</p><p className="mt-1 text-sm">{error}</p><button type="button" onClick={() => void loadLesson()} className="mt-4 rounded-lg border border-red-300 px-3 py-2 text-sm font-semibold">Try again</button></div>}

        {!loading && !error && lesson && course && <>
          <section className="mt-7 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
            <p className="text-sm font-semibold text-indigo-700">{course.title} · Lesson {lesson.position}</p>
            <h1 className="mt-3 text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl">{lesson.title}</h1>
            {lesson.content ? <p className="mt-5 whitespace-pre-line leading-8 text-slate-600">{lesson.content}</p> : <p className="mt-5 text-slate-500">No lesson content provided.</p>}
          </section>

          {ownsCourse && <section aria-labelledby="upload-heading" className="mt-8 rounded-2xl border border-indigo-100 bg-white p-6 shadow-sm sm:p-8">
            <div><p className="text-sm font-bold uppercase tracking-[0.18em] text-indigo-700">Teacher tools</p><h2 id="upload-heading" className="mt-2 text-xl font-semibold text-slate-950">Upload PDF material</h2><p className="mt-2 text-sm leading-6 text-slate-600">Text-based PDF only, up to 10 MB. LearnAI extracts and embeds the document synchronously before the request completes.</p></div>
            {uploadError && <p role="alert" className="mt-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{uploadError}</p>}
            {success && <p role="status" className="mt-5 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{success}</p>}
            <form onSubmit={handleUpload} className="mt-6" noValidate>
              <label htmlFor="pdf-file" className="block text-sm font-semibold text-slate-800">PDF file</label>
              <input ref={fileInput} id="pdf-file" name="file" type="file" accept="application/pdf,.pdf" onChange={handleFileSelection} disabled={uploading} className="mt-2 block w-full rounded-xl border border-slate-300 bg-slate-50 px-3 py-3 text-sm file:mr-4 file:rounded-lg file:border-0 file:bg-indigo-50 file:px-3 file:py-2 file:font-semibold file:text-indigo-700 hover:file:bg-indigo-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600" />
              {selectedFile && <p className="mt-3 text-sm text-slate-600"><span className="font-semibold text-slate-800">Selected:</span> {selectedFile.name} · {formatBytes(selectedFile.size)}</p>}
              <button type="submit" disabled={!selectedFile || uploading} className="mt-5 rounded-xl bg-indigo-600 px-5 py-3 font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-indigo-400">{uploading ? "Uploading and processing…" : "Upload PDF"}</button>
            </form>
          </section>}

          <section aria-labelledby="tutor-heading" className="mt-8 overflow-hidden rounded-2xl border border-indigo-100 bg-white shadow-sm">
            <div className="border-b border-indigo-100 bg-indigo-50/60 p-6 sm:p-8">
              <p className="text-sm font-bold uppercase tracking-[0.18em] text-indigo-700">Grounded learning support</p>
              <h2 id="tutor-heading" className="mt-2 text-2xl font-bold text-slate-950">AI Tutor</h2>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">Ask one question at a time. Answers are generated from processed PDF material attached to this lesson, with the retrieved sources shown below.</p>
            </div>

            <div className="p-6 sm:p-8">
              {!hasReadyDocuments && <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-4 text-sm text-amber-900">
                <p className="font-semibold">AI Tutor is not available yet</p>
                <p className="mt-1 leading-6">This lesson needs at least one successfully processed document with READY status before questions can be asked.</p>
              </div>}

              <form onSubmit={handleAskTutor} className="mt-5" noValidate>
                <label htmlFor="tutor-question" className="block text-sm font-semibold text-slate-800">Your question</label>
                <textarea
                  id="tutor-question"
                  name="question"
                  rows={4}
                  maxLength={2000}
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  disabled={!hasReadyDocuments || askingTutor}
                  placeholder={hasReadyDocuments ? "What would you like to understand about this lesson?" : "A READY document is required to ask a question."}
                  aria-describedby="tutor-question-help"
                  className="mt-2 block w-full resize-y rounded-xl border border-slate-300 bg-white px-4 py-3 text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200 disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-500"
                />
                <div id="tutor-question-help" className="mt-2 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500">
                  <span>The backend validates questions from 1 to 2,000 characters.</span>
                  <span>{question.length}/2,000</span>
                </div>
                <button type="submit" disabled={!hasReadyDocuments || !question.trim() || askingTutor} className="mt-4 rounded-xl bg-indigo-600 px-5 py-3 font-semibold text-white shadow-sm hover:bg-indigo-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:cursor-not-allowed disabled:bg-indigo-400">
                  {askingTutor ? "Searching lesson material…" : "Ask AI Tutor"}
                </button>
              </form>

              {askingTutor && <div role="status" aria-live="polite" className="mt-6 rounded-xl border border-indigo-100 bg-indigo-50 px-4 py-4 text-sm text-indigo-800">Retrieving relevant lesson material and preparing an answer…</div>}
              {tutorError && <div role="alert" className="mt-6 rounded-xl border border-red-200 bg-red-50 px-4 py-4 text-sm text-red-800"><p className="font-semibold">AI Tutor could not answer</p><p className="mt-1">{tutorError}</p></div>}

              {!askingTutor && tutorAnswer && <article aria-labelledby="tutor-answer-heading" className="mt-8 border-t border-slate-200 pt-7">
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">Your question</p>
                  <p className="mt-2 leading-7 text-slate-800">{submittedQuestion}</p>
                </div>
                <div className="mt-4 rounded-xl border border-indigo-100 bg-white p-5 shadow-sm">
                  <p className="text-xs font-bold uppercase tracking-[0.16em] text-indigo-700">Grounded answer</p>
                  <h3 id="tutor-answer-heading" className="sr-only">AI Tutor answer</h3>
                  <p className="mt-3 whitespace-pre-line leading-7 text-slate-800">{tutorAnswer.answer}</p>
                </div>

                <div className="mt-6">
                  <h3 className="text-sm font-bold uppercase tracking-[0.16em] text-slate-700">Sources from lesson material</h3>
                  {tutorAnswer.sources.length === 0 ? <p className="mt-3 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">No source chunks were available for this answer.</p> : <ul className="mt-3 grid gap-3 sm:grid-cols-2">{tutorAnswer.sources.map((source) => <li key={`${source.document_id}-${source.chunk_index}`} className="rounded-xl border border-slate-200 p-4">
                    <p className="break-words font-semibold text-slate-900">{source.filename}</p>
                    <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
                      <span>Chunk {source.chunk_index}</span>
                      <span title="Vector cosine similarity used for retrieval; this is not answer confidence.">Retrieval similarity {source.similarity.toFixed(3)}</span>
                    </div>
                  </li>)}</ul>}
                  {tutorAnswer.sources.length > 0 && <p className="mt-3 text-xs leading-5 text-slate-500">Retrieval similarity describes how closely a source chunk matched the question. It is not an answer-confidence score.</p>}
                </div>
              </article>}
            </div>
          </section>

          <section aria-labelledby="documents-heading" className="mt-10">
            <div className="flex items-end justify-between gap-4"><div><p className="text-sm font-bold uppercase tracking-[0.18em] text-indigo-700">Learning material</p><h2 id="documents-heading" className="mt-2 text-2xl font-bold text-slate-950 sm:text-3xl">Documents</h2></div><button type="button" disabled={refreshing} onClick={() => void refreshDocuments()} className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60">{refreshing ? "Refreshing…" : "Refresh"}</button></div>
            {documentsError && <div role="alert" className="mt-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{documentsError}</div>}
            {documents.length === 0 ? <div className="mt-6 rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center"><h3 className="font-semibold text-slate-900">No documents yet</h3><p className="mt-2 text-slate-600">{ownsCourse ? "Upload the first PDF learning material for this lesson." : "The teacher has not added any PDF material."}</p></div> : <ul className="mt-6 space-y-4">{documents.map((document) => <li key={document.id} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6"><div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"><div className="min-w-0"><div className="flex flex-wrap items-center gap-3"><h3 className="truncate font-semibold text-slate-950">{document.original_filename}</h3><span className={`rounded-full px-2.5 py-1 text-xs font-bold uppercase tracking-wide ring-1 ring-inset ${statusStyles[document.status]}`}>{document.status}</span></div><p className="mt-2 text-sm text-slate-500">{formatBytes(document.file_size)} · Uploaded {new Date(document.created_at).toLocaleString()}</p>{document.status === "failed" && <p className="mt-2 text-sm text-red-700">Processing failed. The teacher can delete this record and try another text-based PDF.</p>}{document.status === "processing" && <p className="mt-2 text-sm text-amber-700">Processing is currently in progress.</p>}</div>{ownsCourse && <button type="button" disabled={deletingId !== null} onClick={() => void handleDelete(document)} className="shrink-0 rounded-lg border border-red-200 px-3 py-2 text-sm font-semibold text-red-700 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50">{deletingId === document.id ? "Deleting…" : "Delete"}</button>}</div></li>)}</ul>}
          </section>

          {token && user && <LessonQuiz token={token} lessonId={lessonId} courseId={courseId} role={user.role} ownsCourse={ownsCourse} hasReadyDocuments={hasReadyDocuments} onUnauthorized={handleUnauthorized} />}
        </>}
      </main>
    </AppShell>
  );
}
