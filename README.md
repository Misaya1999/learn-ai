# LearnAI

LearnAI is an AI-powered EdTech learning platform. Milestone 9 makes the complete application reproducibly runnable with Docker Compose and automatically checked by GitHub Actions.

## Stack

- Frontend: Next.js, TypeScript, Tailwind CSS
- Backend: Python, FastAPI, SQLAlchemy, Alembic
- Database: PostgreSQL
- Authentication: Argon2 password hashing and signed JWT access tokens
- Semantic retrieval: OpenAI `text-embedding-3-small` and pgvector
- Answer generation: an injectable provider using the OpenAI Responses API

## Project structure

```text
learn-ai/
├── frontend/                  # Next.js web application
├── backend/
│   ├── alembic/versions/      # Database migrations
│   ├── app/
│   │   ├── api/               # Routes and request dependencies
│   │   ├── core/              # Configuration and security primitives
│   │   ├── db/                # SQLAlchemy base, engine, and sessions
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   └── services/          # Business logic, PDF processing, and storage
│   ├── storage/documents/     # Git-ignored runtime PDF uploads
│   └── tests/                 # Isolated API tests
├── .env.example
├── compose.yaml
├── docker/                    # PostgreSQL initialization
├── .github/workflows/ci.yml  # Portable, PostgreSQL, and frontend CI
└── README.md
```

## Docker Quick Start

Clone the repository, create local configuration, replace the development placeholders, and start the stack:

```bash
git clone <repository-url> learn-ai
cd learn-ai
cp .env.example .env
docker compose up --build
```

On Windows PowerShell, use `Copy-Item .env.example .env` instead of `cp`. At minimum, replace `POSTGRES_PASSWORD`, `POSTGRES_ADMIN_PASSWORD`, and `JWT_SECRET_KEY`. Development defaults in `compose.yaml` are conveniences only and are not production credentials.

Services are available at:

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- Backend health: `http://localhost:8000/health`

The database initializes a non-superuser application role and enables pgvector as the PostgreSQL administrator. After database health succeeds, exactly one backend container runs `alembic upgrade head`; migration failure stops API startup. The current target is `20260924_05`.

Stop containers without deleting data:

```bash
docker compose down
```

To intentionally reset both database and uploaded-document development data:

```bash
docker compose down --volumes
```

PostgreSQL data and uploaded PDFs use separate named volumes. Rebuilding or recreating containers therefore preserves both unless volumes are explicitly removed.

`NEXT_PUBLIC_API_URL` defaults to `http://localhost:8000` because frontend requests run in the user's browser, which cannot resolve the internal Compose hostname `backend`. The backend itself connects to PostgreSQL at `db:5432`. CORS remains restricted to `FRONTEND_ORIGIN`, which defaults to `http://localhost:3000`.

OpenAI configuration is optional for startup. Authentication, learning APIs, grading, analytics, health checks, and automated tests work without it. Embedding, AI Tutor, and quiz-generation operations require `OPENAI_API_KEY` only when those provider-backed operations are invoked.

## Prerequisites

- Docker Desktop or another Docker Engine with Compose, for the recommended Quick Start
- Node.js 20.9+
- Python 3.11+
- PostgreSQL 14+

## PostgreSQL setup

Create the application database and a dedicated database user. For example, from `psql` as a PostgreSQL administrator:

```sql
CREATE USER learnai WITH PASSWORD 'choose-a-strong-database-password';
CREATE DATABASE learnai OWNER learnai;
```

Copy `.env.example` to `.env` at the repository root and replace the database credentials:

```env
DATABASE_URL=postgresql+psycopg://learnai:your-password@localhost:5432/learnai
```

The backend loads the root `.env` file automatically. Do not commit `.env`; it is ignored by Git.

## Authentication configuration

Generate a strong JWT signing secret rather than using a memorable value:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Add it to `.env` together with the token lifetime:

```env
JWT_SECRET_KEY=the-generated-random-value
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

`JWT_SECRET_KEY` is required and must contain at least 32 characters. The application will not start with a missing or short key.

## Document configuration

The defaults below store PDFs locally under a Git-ignored backend directory and split extracted text into 1,000-character chunks with a 200-character overlap:

```env
DOCUMENT_STORAGE_DIR=backend/storage/documents
DOCUMENT_MAX_UPLOAD_SIZE=10485760
DOCUMENT_CHUNK_SIZE=1000
DOCUMENT_CHUNK_OVERLAP=200
```

`DOCUMENT_CHUNK_OVERLAP` must be smaller than `DOCUMENT_CHUNK_SIZE`. Stored database paths are generated relative keys, not client filenames or machine-specific absolute paths.

## Embeddings and pgvector

An embedding is a numeric representation of text. LearnAI embeds each extracted document chunk so semantically related text can be found even when a query does not use the exact same words. `text-embedding-3-small` is used as a cost-conscious retrieval model and produces 1,536-dimensional vectors by default.

Configure the provider in `.env`:

```env
OPENAI_API_KEY=your-api-key
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_EMBEDDING_DIMENSIONS=1536
OPENAI_EMBEDDING_BATCH_SIZE=100
OPENAI_CHAT_MODEL=gpt-4.1-mini
AI_TUTOR_MAX_OUTPUT_TOKENS=500
AI_TUTOR_RETRIEVAL_TOP_K=5
AI_TUTOR_MAX_CONTEXT_CHARACTERS=12000
QUIZ_GENERATION_MAX_CONTEXT_CHARACTERS=16000
QUIZ_GENERATION_MAX_OUTPUT_TOKENS=4000
```

Never commit or log `OPENAI_API_KEY`. New uploads require a configured key; existing chunks migrated from Milestone 4 may retain a NULL embedding until explicitly reprocessed later.

For a fresh PostgreSQL database, enable pgvector before or during migration:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Creating an extension may require a PostgreSQL administrator or superuser. The normal LearnAI application role should not be promoted to superuser. Once the extension is installed, run `alembic upgrade head` as usual.

Semantic search embeds the query with the same model, filters ready documents and non-NULL embeddings within the requested lesson, calculates exact pgvector cosine distance, and returns the closest chunks. The API exposes `similarity = 1 - cosine_distance`; larger values indicate greater semantic similarity. No approximate vector index is used for the current MVP dataset.

## Grounded RAG AI Tutor

RAG separates retrieval from generation. LearnAI first uses the existing exact pgvector search to retrieve a configured top-K of ready, embedded chunks belonging only to the requested lesson. It then builds deterministic, clearly delimited context blocks and asks the configured answer provider to respond using only that context.

The context builder includes only complete chunks that fit within `AI_TUTOR_MAX_CONTEXT_CHARACTERS`; it never truncates a chunk mid-text. Duplicate document/chunk references are removed while preserving retrieval order. If no usable chunk is retrieved or fits the budget, LearnAI returns a deterministic insufficient-context answer and does not call the LLM.

Uploaded PDF text is treated as untrusted reference data. Higher-level instructions tell the provider not to follow instructions found inside documents, invent unsupported facts, or claim access to material that was not retrieved. This is defense-in-depth for an MVP, not a guarantee that prompt injection is impossible.

Public citations are built from retrieved database metadata—not model-generated citation text—and contain only `document_id`, `filename`, `chunk_index`, and similarity. Embeddings, storage paths, prompts, provider responses, and secrets are not exposed.

The embedding and answer-generation services are injectable. Automated tests use deterministic fakes and make zero OpenAI calls. A real `OPENAI_API_KEY` enables an optional manual provider smoke test; such a test may incur API charges and is not required for application imports, migrations, or the test suite. Fake-provider tests verify orchestration, scoping, error handling, and citation integrity, but they do not prove real-model answer quality.

## Quiz generation and grading

The owning teacher can generate a 1–10 question quiz from a lesson's ready document chunks. LearnAI builds bounded, deterministic context from the existing document pipeline, marks uploaded text as untrusted, and instructs the provider to use only lesson facts. The provider abstraction supports deterministic fakes and an optional OpenAI Responses API implementation with schema-constrained Pydantic output. Output is validated again before one atomic commit: the requested count, non-blank text, exactly four unique options, exactly one correct option, and a grounded explanation are required.

The database stores quizzes, ordered questions, ordered options, attempts, and selected answers. Generated questions and options have no editing endpoint. Historical foreign keys use restrictive deletion behavior so an answer key cannot silently change beneath an attempt. Scores use fixed-precision `NUMERIC(5,2)`.

Teachers may generate and inspect answer keys only for courses they own. Student quiz responses omit correctness and explanations before submission. Students must be enrolled in the parent course to view or start a quiz; teachers cannot participate as students. Multiple attempts are allowed.

Submission requires exactly one answer for every snapshotted question. The server verifies question and option ownership, reads correctness from the database, calculates `correct_count / total_questions * 100`, and persists answers plus the result atomically. Only after submission does review expose the selected answer, correct answer, correctness, and explanation.

Quiz tests inject deterministic generators and make zero OpenAI calls. These tests verify application behavior and persistence, not real-model question quality.

## Learning Analytics

Analytics are read-time SQL aggregations over submitted quiz attempts and persisted answers. No analytics tables or AI calls are used. Unsubmitted attempts and their answers are excluded from every performance metric.

Student APIs provide an own-data overview, per-lesson performance, and chronological progress points. Teacher APIs provide owned-course overview, enrolled-student performance, lesson performance, and question accuracy. Enrolled students and course lessons with no submitted activity are included with zero counts and null performance percentages. Questions with no submitted answers are also included.

Metric definitions:

- `average_score` is the arithmetic mean of submitted attempt `score_percent` values.
- `overall_accuracy_percent` is `sum(correct_count) / sum(total_questions) × 100`.
- These are intentionally different: attempts scoring 1/1 and 1/3 average `66.67%`, while weighted accuracy is `50.00%`.
- Counts return zero when no observations exist. Percentages and averages requiring observations return null.
- Percentages use decimal arithmetic and two decimal places.

Student endpoints require the student role and expose only the authenticated student's data. Teacher endpoints require ownership of the requested course. Student-level teacher analytics include only enrolled student ID and name; aggregate question analytics contain no student identity or answer-key internals.

## Install and migrate the backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
```

To inspect migration state or roll back the latest revision:

```bash
alembic current
alembic downgrade -1
```

## Run the backend

```bash
cd backend
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`; interactive documentation is available at `http://localhost:8000/docs`.

### Authentication endpoints

- `POST /api/v1/auth/register` accepts `name`, `email`, `password`, and `role` (`student` or `teacher`).
- `POST /api/v1/auth/login` accepts OAuth2 form fields `username` (the user's email) and `password`, and returns a bearer access token.
- `GET /api/v1/users/me` requires `Authorization: Bearer <access_token>`.
- `GET /health` remains an unauthenticated health check.

### Learning endpoints

- `POST /api/v1/courses` creates a teacher-owned course.
- `GET /api/v1/courses` and `GET /api/v1/courses/{course_id}` retrieve courses.
- `PATCH` or `DELETE /api/v1/courses/{course_id}` requires the owning teacher.
- `POST /api/v1/courses/{course_id}/lessons` requires the owning teacher.
- `GET /api/v1/courses/{course_id}/lessons` returns lessons ordered by position.
- `GET`, `PATCH`, or `DELETE /api/v1/lessons/{lesson_id}` retrieves or manages a lesson; writes require the owning teacher.
- `POST /api/v1/courses/{course_id}/enroll` enrolls the authenticated student.
- `GET /api/v1/users/me/enrollments` returns the authenticated student's enrollments.

### Document endpoints

- `POST /api/v1/lessons/{lesson_id}/documents` accepts one PDF as multipart form field `file`; only the owning teacher may upload.
- `GET /api/v1/lessons/{lesson_id}/documents` lists document metadata for a lesson.
- `GET /api/v1/documents/{document_id}` retrieves document metadata without exposing its storage key.
- `DELETE /api/v1/documents/{document_id}` requires the owning teacher and removes chunks plus the local PDF.
- `POST /api/v1/lessons/{lesson_id}/search` embeds a query and returns the most similar ready document chunks for that lesson.
- `POST /api/v1/lessons/{lesson_id}/ask` retrieves lesson context and returns a grounded answer plus structured sources.
- `POST /api/v1/lessons/{lesson_id}/quizzes/generate` generates a grounded quiz for the owning teacher.
- `GET /api/v1/lessons/{lesson_id}/quizzes` and `GET /api/v1/quizzes/{quiz_id}` return authorized quiz views.
- `POST /api/v1/quizzes/{quiz_id}/attempts` starts an enrolled student's attempt.
- `POST /api/v1/quiz-attempts/{attempt_id}/submit` grades a complete submission server-side.
- `GET /api/v1/users/me/quiz-attempts` returns only the current student's history.
- `GET /api/v1/users/me/analytics` returns the student's submitted-attempt overview.
- `GET /api/v1/users/me/analytics/lessons` groups the student's performance by lesson.
- `GET /api/v1/users/me/analytics/progress` returns chronological chart-ready attempt points.
- `GET /api/v1/courses/{course_id}/analytics` returns an owned-course overview.
- `GET /api/v1/courses/{course_id}/analytics/students` includes every enrolled student.
- `GET /api/v1/courses/{course_id}/analytics/lessons` includes every course lesson.
- `GET /api/v1/courses/{course_id}/analytics/questions` includes every generated question.

PDF and embedding processing are synchronous. Text-based PDFs are supported; scanned/image-only PDFs require OCR and are marked failed because OCR is outside the current scope.

Example registration body:

```json
{
  "name": "Ada Lovelace",
  "email": "ada@example.com",
  "password": "a-long-unique-password",
  "role": "student"
}
```

## Run the tests

```bash
cd backend
pytest
```

CI runs the portable backend suite without an API key, a separate PostgreSQL 18 plus pgvector integration suite against a non-superuser application role, and frontend lint/build/audit checks. No automated job calls OpenAI.

Tests use a fresh temporary SQLite database with foreign-key enforcement for speed and isolation. PostgreSQL migrations and integration behavior should also be verified against the configured development database.

## Run the frontend

The browser-facing API base URL is configured with:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

The F2 authentication UI stores the short-lived bearer access token in `localStorage` and verifies it through `GET /api/v1/users/me` when the application loads. This keeps the portfolio MVP small and compatible with the existing bearer-token backend, but JavaScript-readable storage is exposed if an XSS vulnerability exists. A production system should prefer an HttpOnly, Secure, SameSite cookie/BFF design where appropriate. The backend does not provide refresh tokens, so the frontend does not simulate refresh behavior.

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

## Current scope

Milestone 9 includes the complete backend feature set, production builds for both applications, PostgreSQL/pgvector initialization, persistent database/upload volumes, health checks, automatic migrations, and GitHub Actions CI. Cloud deployment, TLS termination, managed secrets, backups, horizontal migration coordination, observability, frontend product features, and infrastructure-as-code remain intentionally deferred.
