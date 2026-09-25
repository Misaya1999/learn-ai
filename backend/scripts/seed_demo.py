from dataclasses import dataclass

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.user import User, UserRole


TEACHER_EMAIL = "misaya1999@gmail.com"


@dataclass(frozen=True)
class DemoLesson:
    title: str
    content: str
    position: int


@dataclass(frozen=True)
class DemoCourse:
    title: str
    description: str
    lessons: tuple[DemoLesson, ...]


DEMO_COURSES = (
    DemoCourse(
        title="Python Programming Fundamentals",
        description=(
            "Build a strong foundation in Python programming through variables, "
            "control flow, functions, data structures, and object-oriented programming."
        ),
        lessons=(
            DemoLesson(
                title="Python Basics",
                position=1,
                content="""Python is a general-purpose programming language known for its readable syntax and broad ecosystem.

This lesson introduces the basic building blocks of Python programs, including variables, primitive data types, expressions, and console input/output.

Topics:
- Variables and assignment
- Strings, integers, floats, and booleans
- Basic operators
- Type conversion
- print() and input()

Learning outcome:
Students should be able to write and run simple Python programs and work with common primitive data types.""",
            ),
            DemoLesson(
                title="Control Flow and Loops",
                position=2,
                content="""Control flow determines which parts of a program execute and how often they execute.

Students learn how conditional statements make decisions and how loops automate repetitive operations.

Topics:
- if, elif, and else
- Comparison operators
- Boolean expressions
- for loops
- while loops
- break and continue

Learning outcome:
Students should be able to implement decision-making logic and repetition in Python programs.""",
            ),
            DemoLesson(
                title="Functions and Data Structures",
                position=3,
                content="""Functions make programs easier to organize, reuse, and test. Python also provides built-in data structures for managing collections of information.

Topics:
- Defining and calling functions
- Parameters and return values
- Variable scope
- Lists
- Tuples
- Dictionaries
- Sets

Learning outcome:
Students should be able to decompose programs into reusable functions and select appropriate data structures for common problems.""",
            ),
            DemoLesson(
                title="Object-Oriented Programming",
                position=4,
                content="""Object-oriented programming organizes software around objects that combine data and behavior.

Topics:
- Classes and objects
- Attributes
- Methods
- Constructors
- Encapsulation
- Inheritance

Learning outcome:
Students should understand the basic purpose of object-oriented programming and be able to define simple Python classes.""",
            ),
        ),
    ),
    DemoCourse(
        title="Modern Web Development with React",
        description=(
            "Learn how modern frontend applications are built with React, reusable "
            "components, state management, forms, and REST API integration."
        ),
        lessons=(
            DemoLesson(
                title="React Fundamentals",
                position=1,
                content="""React is a JavaScript library for building user interfaces from reusable components.

This lesson introduces the component model and how React applications render user interfaces from application data.

Topics:
- Components
- JSX
- Component composition
- Rendering
- Basic project structure

Learning outcome:
Students should understand the component-based model and be able to build simple React interfaces.""",
            ),
            DemoLesson(
                title="Components and Props",
                position=2,
                content="""Components divide a user interface into reusable pieces. Props allow data to flow from parent components to child components.

Topics:
- Functional components
- Props
- Component reuse
- Parent-child relationships
- Conditional rendering

Learning outcome:
Students should be able to design reusable components and pass data between them using props.""",
            ),
            DemoLesson(
                title="State, Events and Forms",
                position=3,
                content="""Interactive applications need to respond to user actions and maintain data that changes over time.

Topics:
- Component state
- useState
- Event handlers
- Controlled form inputs
- Form submission
- Loading and error states

Learning outcome:
Students should be able to build interactive forms and interfaces whose state changes in response to user actions.""",
            ),
            DemoLesson(
                title="REST API Integration",
                position=4,
                content="""Frontend applications commonly communicate with backend services through HTTP APIs.

Topics:
- REST concepts
- GET, POST, PATCH, and DELETE
- JSON
- Fetching data
- Sending form data
- Loading and error handling
- Authentication headers

Learning outcome:
Students should understand how a React frontend communicates with a backend REST API.""",
            ),
        ),
    ),
    DemoCourse(
        title="AI, Embeddings and RAG Fundamentals",
        description=(
            "Explore the foundations behind modern AI-assisted applications, including "
            "large language models, embeddings, semantic retrieval, and "
            "retrieval-augmented generation."
        ),
        lessons=(
            DemoLesson(
                title="Large Language Models",
                position=1,
                content="""Large language models are neural language systems trained on large text datasets to model patterns in language.

Applications can use LLMs for tasks such as question answering, summarization, classification, and content generation.

However, an LLM does not automatically know private application data or recently uploaded course material.

Topics:
- Language models
- Prompts and responses
- Tokens and context
- Common application patterns
- Model limitations

Learning outcome:
Students should understand the role of an LLM inside an AI-powered application.""",
            ),
            DemoLesson(
                title="Embeddings",
                position=2,
                content="""An embedding represents content as a numerical vector.

Texts with related meaning can have vectors that are closer to each other in the embedding space. Applications can use this property to perform semantic retrieval rather than relying only on exact keyword matching.

Topics:
- Vector representations
- Embedding models
- Semantic similarity
- Document embeddings
- Query embeddings

Learning outcome:
Students should understand why embeddings are useful for semantic search.""",
            ),
            DemoLesson(
                title="Vector Search with pgvector",
                position=3,
                content="""Vector databases and vector-enabled relational databases can store embeddings and compare them using similarity or distance metrics.

LearnAI uses PostgreSQL with pgvector so application data and embedding vectors can coexist in the same database.

Topics:
- PostgreSQL
- pgvector
- Vector columns
- Cosine distance
- Similarity search
- Top-K retrieval

Learning outcome:
Students should understand how an application retrieves semantically related document chunks.""",
            ),
            DemoLesson(
                title="Retrieval-Augmented Generation",
                position=4,
                content="""Retrieval-Augmented Generation, or RAG, combines information retrieval with a language model.

A typical RAG pipeline:

Question
-> question embedding
-> vector search
-> relevant document chunks
-> bounded context
-> language model
-> grounded answer

In LearnAI, retrieved sources are controlled by the application rather than invented by the language model.

Topics:
- Document chunking
- Retrieval
- Context construction
- Grounded generation
- Source attribution
- Retrieval isolation

Learning outcome:
Students should be able to explain the major stages of a basic RAG pipeline.""",
            ),
        ),
    ),
)


def normalized_email(value: str) -> str:
    return value.strip().casefold()


def seed_demo() -> None:
    email = normalized_email(TEACHER_EMAIL)
    with SessionLocal() as db:
        teacher = db.scalar(select(User).where(func.lower(User.email) == email))
        if teacher is None:
            raise RuntimeError(
                f"Demo teacher with email {TEACHER_EMAIL!r} does not exist. "
                "Create the teacher account through the application before seeding."
            )
        if teacher.role != UserRole.TEACHER:
            raise RuntimeError(
                f"User with email {TEACHER_EMAIL!r} exists but is not a teacher."
            )

        created_courses = 0
        created_lessons = 0
        skipped_courses = 0
        skipped_lessons = 0

        for demo_course in DEMO_COURSES:
            course = db.scalar(
                select(Course).where(
                    Course.teacher_id == teacher.id,
                    Course.title == demo_course.title,
                )
            )
            if course is None:
                course = Course(
                    teacher_id=teacher.id,
                    title=demo_course.title,
                    description=demo_course.description,
                )
                db.add(course)
                db.flush()
                created_courses += 1
            else:
                skipped_courses += 1

            existing_lesson_titles = set(
                db.scalars(
                    select(Lesson.title).where(Lesson.course_id == course.id)
                ).all()
            )
            for demo_lesson in demo_course.lessons:
                if demo_lesson.title in existing_lesson_titles:
                    skipped_lessons += 1
                    continue
                db.add(
                    Lesson(
                        course_id=course.id,
                        title=demo_lesson.title,
                        content=demo_lesson.content,
                        position=demo_lesson.position,
                    )
                )
                created_lessons += 1

        db.commit()
        print(f"Teacher: {teacher.name}")
        print(f"Created courses: {created_courses}")
        print(f"Created lessons: {created_lessons}")
        print(f"Skipped existing courses: {skipped_courses}")
        print(f"Skipped existing lessons: {skipped_lessons}")


if __name__ == "__main__":
    try:
        seed_demo()
    except RuntimeError as exc:
        raise SystemExit(f"Seed failed: {exc}") from None
