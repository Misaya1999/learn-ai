const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

let unauthorizedHandler: (() => void) | null = null;

export function setUnauthorizedHandler(handler: (() => void) | null): void {
  unauthorizedHandler = handler;
}

export type UserRole = "student" | "teacher";

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  created_at: string;
  updated_at: string;
}

export interface RegisterInput {
  name: string;
  email: string;
  password: string;
  role: UserRole;
}

export interface Course {
  id: string;
  teacher_id: string;
  title: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface CourseCreateInput {
  title: string;
  description: string | null;
}

export interface Lesson {
  id: string;
  course_id: string;
  title: string;
  content: string | null;
  position: number;
  created_at: string;
  updated_at: string;
}

export interface LessonCreateInput {
  title: string;
  content: string | null;
  position: number;
}

export interface Enrollment {
  id: string;
  student_id: string;
  course_id: string;
  enrolled_at: string;
}

export type DocumentStatus = "processing" | "ready" | "failed";

export interface LessonDocument {
  id: string;
  lesson_id: string;
  uploaded_by: string;
  original_filename: string;
  content_type: string;
  file_size: number;
  status: DocumentStatus;
  created_at: string;
  updated_at: string;
}

export interface TutorSource {
  document_id: string;
  filename: string;
  chunk_index: number;
  similarity: number;
}

export interface TutorAnswer {
  answer: string;
  sources: TutorSource[];
}

export interface QuizSummary {
  id: string;
  lesson_id: string;
  title: string;
  created_at: string;
}

export interface QuizOptionStudent {
  id: string;
  option_text: string;
  position: number;
}

export interface QuizQuestionStudent {
  id: string;
  question_text: string;
  position: number;
  options: QuizOptionStudent[];
}

export interface QuizStudent {
  id: string;
  lesson_id: string;
  title: string;
  questions: QuizQuestionStudent[];
}

export interface QuizOptionTeacher extends QuizOptionStudent {
  is_correct: boolean;
}

export interface QuizQuestionTeacher extends Omit<QuizQuestionStudent, "options"> {
  explanation: string;
  options: QuizOptionTeacher[];
}

export interface QuizTeacher extends Omit<QuizStudent, "questions"> {
  created_by: string;
  created_at: string;
  questions: QuizQuestionTeacher[];
}

export interface QuizGenerateInput {
  title: string;
  question_count: number;
}

export interface QuizAttemptStart {
  id: string;
  quiz: QuizStudent;
  total_questions: number;
  started_at: string;
}

export interface QuizAttemptAnswerInput {
  question_id: string;
  selected_option_id: string;
}

export interface QuizAttemptReviewItem {
  question_id: string;
  question_text: string;
  selected_option_id: string;
  selected_option_text: string;
  correct_option_id: string;
  correct_option_text: string;
  is_correct: boolean;
  explanation: string;
}

export interface QuizAttemptReview {
  attempt_id: string;
  quiz_id: string;
  correct_count: number;
  total_questions: number;
  score_percent: string;
  submitted_at: string;
  answers: QuizAttemptReviewItem[];
}

export interface StudentAnalyticsOverview {
  total_submitted_attempts: number;
  distinct_quizzes_attempted: number;
  distinct_lessons_practiced: number;
  average_score: string | null;
  best_score: string | null;
  total_questions_answered: number;
  total_correct_answers: number;
  overall_accuracy_percent: string | null;
}

export interface StudentLessonAnalytics {
  lesson_id: string;
  lesson_title: string;
  submitted_attempts: number;
  average_score: string;
  best_score: string;
  total_questions: number;
  correct_answers: number;
  accuracy_percent: string;
}

export interface StudentProgressPoint {
  attempt_id: string;
  quiz_id: string;
  quiz_title: string;
  lesson_id: string;
  lesson_title: string;
  score_percent: string;
  submitted_at: string;
}

export interface CourseAnalyticsOverview {
  course_id: string;
  enrolled_students: number;
  students_with_submitted_attempts: number;
  total_submitted_attempts: number;
  average_score: string | null;
  total_questions_answered: number;
  total_correct_answers: number;
  overall_accuracy_percent: string | null;
}

export interface CourseStudentAnalytics {
  student_id: string;
  student_name: string;
  submitted_attempts: number;
  average_score: string | null;
  best_score: string | null;
  total_questions: number;
  correct_answers: number;
  accuracy_percent: string | null;
}

export interface CourseLessonAnalytics {
  lesson_id: string;
  lesson_title: string;
  quizzes: number;
  submitted_attempts: number;
  participating_students: number;
  average_score: string | null;
  total_questions: number;
  correct_answers: number;
  accuracy_percent: string | null;
}

export interface CourseQuestionAnalytics {
  question_id: string;
  quiz_id: string;
  question_text: string;
  lesson_id: string;
  total_answers: number;
  correct_answers: number;
  incorrect_answers: number;
  accuracy_percent: string | null;
}

export const MAX_DOCUMENT_UPLOAD_BYTES = 10 * 1024 * 1024;

interface TokenResponse {
  access_token: string;
  token_type: "bearer";
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function errorMessage(detail: unknown, status: number): string {
  if (typeof detail === "string") return detail;
  if (status === 422) return "Please check the information you entered and try again.";
  return "Something went wrong. Please try again.";
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, init);
  } catch {
    throw new ApiError("LearnAI could not reach the API. Please try again shortly.", 0);
  }

  if (!response.ok) {
    let detail: unknown;
    try {
      detail = (await response.json()).detail;
    } catch {
      detail = undefined;
    }
    if (response.status === 401 && new Headers(init.headers).has("Authorization")) {
      unauthorizedHandler?.();
    }
    throw new ApiError(errorMessage(detail, response.status), response.status);
  }

  if (response.status === 204) return undefined as T;

  return response.json() as Promise<T>;
}

export function registerAccount(input: RegisterInput): Promise<User> {
  return request<User>("/api/v1/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export function loginAccount(email: string, password: string): Promise<TokenResponse> {
  const body = new URLSearchParams({ username: email, password });
  return request<TokenResponse>("/api/v1/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
}

export function getCurrentUser(token: string): Promise<User> {
  return request<User>("/api/v1/users/me", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

function bearerHeaders(token: string, json = false): HeadersInit {
  return {
    Authorization: `Bearer ${token}`,
    ...(json ? { "Content-Type": "application/json" } : {}),
  };
}

export function listCourses(token: string): Promise<Course[]> {
  return request<Course[]>("/api/v1/courses", { headers: bearerHeaders(token) });
}

export function getCourse(token: string, courseId: string): Promise<Course> {
  return request<Course>(`/api/v1/courses/${courseId}`, { headers: bearerHeaders(token) });
}

export function createCourse(token: string, input: CourseCreateInput): Promise<Course> {
  return request<Course>("/api/v1/courses", {
    method: "POST",
    headers: bearerHeaders(token, true),
    body: JSON.stringify(input),
  });
}

export function listCourseLessons(token: string, courseId: string): Promise<Lesson[]> {
  return request<Lesson[]>(`/api/v1/courses/${courseId}/lessons`, { headers: bearerHeaders(token) });
}

export function createLesson(token: string, courseId: string, input: LessonCreateInput): Promise<Lesson> {
  return request<Lesson>(`/api/v1/courses/${courseId}/lessons`, {
    method: "POST",
    headers: bearerHeaders(token, true),
    body: JSON.stringify(input),
  });
}

export function getLesson(token: string, lessonId: string): Promise<Lesson> {
  return request<Lesson>(`/api/v1/lessons/${lessonId}`, { headers: bearerHeaders(token) });
}

export function listMyEnrollments(token: string): Promise<Enrollment[]> {
  return request<Enrollment[]>("/api/v1/users/me/enrollments", { headers: bearerHeaders(token) });
}

export function enrollInCourse(token: string, courseId: string): Promise<Enrollment> {
  return request<Enrollment>(`/api/v1/courses/${courseId}/enroll`, {
    method: "POST",
    headers: bearerHeaders(token),
  });
}

export function listLessonDocuments(token: string, lessonId: string): Promise<LessonDocument[]> {
  return request<LessonDocument[]>(`/api/v1/lessons/${lessonId}/documents`, { headers: bearerHeaders(token) });
}

export function uploadLessonDocument(token: string, lessonId: string, file: File): Promise<LessonDocument> {
  const body = new FormData();
  body.append("file", file);
  return request<LessonDocument>(`/api/v1/lessons/${lessonId}/documents`, {
    method: "POST",
    headers: bearerHeaders(token),
    body,
  });
}

export function deleteDocument(token: string, documentId: string): Promise<void> {
  return request<void>(`/api/v1/documents/${documentId}`, {
    method: "DELETE",
    headers: bearerHeaders(token),
  });
}

export function askLessonQuestion(token: string, lessonId: string, question: string): Promise<TutorAnswer> {
  return request<TutorAnswer>(`/api/v1/lessons/${lessonId}/ask`, {
    method: "POST",
    headers: bearerHeaders(token, true),
    body: JSON.stringify({ question }),
  });
}

export function listLessonQuizzes(token: string, lessonId: string): Promise<QuizSummary[]> {
  return request<QuizSummary[]>(`/api/v1/lessons/${lessonId}/quizzes`, { headers: bearerHeaders(token) });
}

export function generateLessonQuiz(token: string, lessonId: string, input: QuizGenerateInput): Promise<QuizTeacher> {
  return request<QuizTeacher>(`/api/v1/lessons/${lessonId}/quizzes/generate`, {
    method: "POST",
    headers: bearerHeaders(token, true),
    body: JSON.stringify(input),
  });
}

export function getTeacherQuiz(token: string, quizId: string): Promise<QuizTeacher> {
  return request<QuizTeacher>(`/api/v1/quizzes/${quizId}`, { headers: bearerHeaders(token) });
}

export function startQuizAttempt(token: string, quizId: string): Promise<QuizAttemptStart> {
  return request<QuizAttemptStart>(`/api/v1/quizzes/${quizId}/attempts`, {
    method: "POST",
    headers: bearerHeaders(token),
  });
}

export function submitQuizAttempt(token: string, attemptId: string, answers: QuizAttemptAnswerInput[]): Promise<QuizAttemptReview> {
  return request<QuizAttemptReview>(`/api/v1/quiz-attempts/${attemptId}/submit`, {
    method: "POST",
    headers: bearerHeaders(token, true),
    body: JSON.stringify({ answers }),
  });
}

export function getStudentAnalytics(token: string): Promise<StudentAnalyticsOverview> {
  return request<StudentAnalyticsOverview>("/api/v1/users/me/analytics", { headers: bearerHeaders(token) });
}

export function getStudentLessonAnalytics(token: string): Promise<StudentLessonAnalytics[]> {
  return request<StudentLessonAnalytics[]>("/api/v1/users/me/analytics/lessons", { headers: bearerHeaders(token) });
}

export function getStudentProgress(token: string): Promise<StudentProgressPoint[]> {
  return request<StudentProgressPoint[]>("/api/v1/users/me/analytics/progress", { headers: bearerHeaders(token) });
}

export function getCourseAnalytics(token: string, courseId: string): Promise<CourseAnalyticsOverview> {
  return request<CourseAnalyticsOverview>(`/api/v1/courses/${courseId}/analytics`, { headers: bearerHeaders(token) });
}

export function getCourseStudentAnalytics(token: string, courseId: string): Promise<CourseStudentAnalytics[]> {
  return request<CourseStudentAnalytics[]>(`/api/v1/courses/${courseId}/analytics/students`, { headers: bearerHeaders(token) });
}

export function getCourseLessonAnalytics(token: string, courseId: string): Promise<CourseLessonAnalytics[]> {
  return request<CourseLessonAnalytics[]>(`/api/v1/courses/${courseId}/analytics/lessons`, { headers: bearerHeaders(token) });
}

export function getCourseQuestionAnalytics(token: string, courseId: string): Promise<CourseQuestionAnalytics[]> {
  return request<CourseQuestionAnalytics[]>(`/api/v1/courses/${courseId}/analytics/questions`, { headers: bearerHeaders(token) });
}
