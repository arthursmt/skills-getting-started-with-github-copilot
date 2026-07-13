import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture(autouse=True)
def reset_activities_state():
    snapshot = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(snapshot)


@pytest.fixture
def client():
    return TestClient(app)


def activity_path(activity_name: str) -> str:
    return quote(activity_name, safe="")


def test_root_redirects_to_static_index(client: TestClient):
    response = client.get("/", follow_redirects=False)

    assert response.status_code in (307, 302)
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_all_activities(client: TestClient):
    response = client.get("/activities")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, dict)
    assert "Chess Club" in body
    assert "Programming Class" in body


def test_signup_success_adds_participant(client: TestClient):
    activity_name = "Soccer Team"
    email = "newstudent@mergington.edu"

    response = client.post(
        f"/activities/{activity_path(activity_name)}/signup", params={"email": email}
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities[activity_name]["participants"]


def test_signup_returns_404_when_activity_not_found(client: TestClient):
    response = client.post(
        f"/activities/{activity_path('Unknown Club')}/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_returns_400_when_student_already_signed_up(client: TestClient):
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    response = client.post(
        f"/activities/{activity_path(activity_name)}/signup", params={"email": email}
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Student is already signed up"}


def test_signup_returns_400_when_activity_is_full(client: TestClient):
    activity_name = "Math Olympiad"
    max_participants = activities[activity_name]["max_participants"]
    activities[activity_name]["participants"] = [
        f"student{i}@mergington.edu" for i in range(max_participants)
    ]

    response = client.post(
        f"/activities/{activity_path(activity_name)}/signup",
        params={"email": "overflow@mergington.edu"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Activity is full"}


def test_unregister_success_removes_participant(client: TestClient):
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    response = client.delete(
        f"/activities/{activity_path(activity_name)}/participants/{quote(email, safe='')}"
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert email not in activities[activity_name]["participants"]


def test_unregister_returns_404_when_activity_not_found(client: TestClient):
    response = client.delete(
        f"/activities/{activity_path('Unknown Club')}/participants/student%40mergington.edu"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_returns_404_when_participant_not_found(client: TestClient):
    activity_name = "Soccer Team"

    response = client.delete(
        f"/activities/{activity_path(activity_name)}/participants/ghost%40mergington.edu"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Participant not found"}
