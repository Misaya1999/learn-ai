import uuid

from fastapi.testclient import TestClient


def create_user_and_headers(
    client: TestClient, email: str, role: str
) -> tuple[dict[str, object], dict[str, str]]:
    password = "correct-horse-battery-staple"
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "name": f"Test {role.title()}",
            "email": email,
            "password": password,
            "role": role,
        },
    )
    assert registration.status_code == 201
    login = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    return registration.json(), headers


def create_course(client: TestClient, headers: dict[str, str]) -> dict[str, object]:
    response = client.post(
        "/api/v1/courses",
        json={"title": "Practical AI", "description": "A grounded introduction."},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def create_lesson(
    client: TestClient,
    course_id: str,
    headers: dict[str, str],
    *,
    title: str = "Foundations",
    position: int = 1,
) -> dict[str, object]:
    response = client.post(
        f"/api/v1/courses/{course_id}/lessons",
        json={"title": title, "content": f"Content for {title}", "position": position},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def test_teacher_creates_course(client: TestClient) -> None:
    teacher, headers = create_user_and_headers(client, "teacher@example.com", "teacher")

    course = create_course(client, headers)

    assert course["teacher_id"] == teacher["id"]
    assert course["title"] == "Practical AI"


def test_student_cannot_create_course(client: TestClient) -> None:
    _, headers = create_user_and_headers(client, "student@example.com", "student")

    response = client.post(
        "/api/v1/courses", json={"title": "Forbidden Course"}, headers=headers
    )

    assert response.status_code == 403


def test_course_creation_rejects_client_supplied_teacher_id(client: TestClient) -> None:
    _, headers = create_user_and_headers(client, "teacher@example.com", "teacher")

    response = client.post(
        "/api/v1/courses",
        json={"title": "Untrusted Owner", "teacher_id": str(uuid.uuid4())},
        headers=headers,
    )

    assert response.status_code == 422


def test_teacher_updates_own_course(client: TestClient) -> None:
    _, headers = create_user_and_headers(client, "teacher@example.com", "teacher")
    course = create_course(client, headers)

    response = client.patch(
        f"/api/v1/courses/{course['id']}",
        json={"title": "Updated Practical AI"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Updated Practical AI"


def test_teacher_cannot_update_another_teachers_course(client: TestClient) -> None:
    _, owner_headers = create_user_and_headers(client, "owner@example.com", "teacher")
    _, other_headers = create_user_and_headers(client, "other@example.com", "teacher")
    course = create_course(client, owner_headers)

    response = client.patch(
        f"/api/v1/courses/{course['id']}",
        json={"title": "Taken Over"},
        headers=other_headers,
    )

    assert response.status_code == 403


def test_course_retrieval(client: TestClient) -> None:
    _, headers = create_user_and_headers(client, "teacher@example.com", "teacher")
    course = create_course(client, headers)

    detail = client.get(f"/api/v1/courses/{course['id']}")
    listing = client.get("/api/v1/courses")

    assert detail.status_code == 200
    assert detail.json() == course
    assert listing.status_code == 200
    assert [item["id"] for item in listing.json()] == [course["id"]]


def test_owner_creates_lesson(client: TestClient) -> None:
    _, headers = create_user_and_headers(client, "teacher@example.com", "teacher")
    course = create_course(client, headers)

    lesson = create_lesson(client, course["id"], headers)

    assert lesson["course_id"] == course["id"]
    assert lesson["position"] == 1


def test_non_owner_cannot_create_or_change_lesson(client: TestClient) -> None:
    _, owner_headers = create_user_and_headers(client, "owner@example.com", "teacher")
    _, other_headers = create_user_and_headers(client, "other@example.com", "teacher")
    course = create_course(client, owner_headers)
    lesson = create_lesson(client, course["id"], owner_headers)

    create_response = client.post(
        f"/api/v1/courses/{course['id']}/lessons",
        json={"title": "Intrusion", "position": 2},
        headers=other_headers,
    )
    update_response = client.patch(
        f"/api/v1/lessons/{lesson['id']}",
        json={"title": "Hijacked"},
        headers=other_headers,
    )

    assert create_response.status_code == 403
    assert update_response.status_code == 403


def test_lessons_are_ordered_by_position_deterministically(client: TestClient) -> None:
    _, headers = create_user_and_headers(client, "teacher@example.com", "teacher")
    course = create_course(client, headers)
    create_lesson(client, course["id"], headers, title="Third", position=3)
    create_lesson(client, course["id"], headers, title="First B", position=1)
    create_lesson(client, course["id"], headers, title="First A", position=1)

    response = client.get(f"/api/v1/courses/{course['id']}/lessons")

    assert response.status_code == 200
    lessons = response.json()
    assert [lesson["position"] for lesson in lessons] == [1, 1, 3]
    assert [lesson["id"] for lesson in lessons] == sorted(
        [lesson["id"] for lesson in lessons[:2]]
    ) + [lessons[2]["id"]]


def test_invalid_lesson_position_is_rejected(client: TestClient) -> None:
    _, headers = create_user_and_headers(client, "teacher@example.com", "teacher")
    course = create_course(client, headers)

    response = client.post(
        f"/api/v1/courses/{course['id']}/lessons",
        json={"title": "Invalid", "position": 0},
        headers=headers,
    )

    assert response.status_code == 422


def test_student_enrolls_and_lists_current_enrollments(client: TestClient) -> None:
    _, teacher_headers = create_user_and_headers(client, "teacher@example.com", "teacher")
    student, student_headers = create_user_and_headers(
        client, "student@example.com", "student"
    )
    course = create_course(client, teacher_headers)

    enrolled = client.post(
        f"/api/v1/courses/{course['id']}/enroll", headers=student_headers
    )
    listing = client.get("/api/v1/users/me/enrollments", headers=student_headers)

    assert enrolled.status_code == 201
    assert enrolled.json()["student_id"] == student["id"]
    assert enrolled.json()["course_id"] == course["id"]
    assert listing.status_code == 200
    assert listing.json() == [enrolled.json()]


def test_teacher_cannot_enroll_as_student(client: TestClient) -> None:
    _, headers = create_user_and_headers(client, "teacher@example.com", "teacher")
    course = create_course(client, headers)

    response = client.post(
        f"/api/v1/courses/{course['id']}/enroll", headers=headers
    )

    assert response.status_code == 403


def test_duplicate_enrollment_is_rejected(client: TestClient) -> None:
    _, teacher_headers = create_user_and_headers(client, "teacher@example.com", "teacher")
    _, student_headers = create_user_and_headers(client, "student@example.com", "student")
    course = create_course(client, teacher_headers)
    url = f"/api/v1/courses/{course['id']}/enroll"

    first = client.post(url, headers=student_headers)
    duplicate = client.post(url, headers=student_headers)

    assert first.status_code == 201
    assert duplicate.status_code == 409


def test_unauthenticated_protected_writes_are_rejected(client: TestClient) -> None:
    random_id = uuid.uuid4()

    responses = [
        client.post("/api/v1/courses", json={"title": "No Auth"}),
        client.post(
            f"/api/v1/courses/{random_id}/lessons",
            json={"title": "No Auth", "position": 1},
        ),
        client.patch(f"/api/v1/lessons/{random_id}", json={"title": "No Auth"}),
        client.post(f"/api/v1/courses/{random_id}/enroll"),
    ]

    assert all(response.status_code == 401 for response in responses)
