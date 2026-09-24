const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

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
