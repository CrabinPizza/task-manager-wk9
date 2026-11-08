"""Tests for search_tasks in app/services/tasks.py and GET /tasks/search."""

import pytest

from app.errors import ValidationError
from app.services import tasks as svc


def _ids(tasks):
    return [t.id for t in tasks]


# --------------------------------------------------------------------------- matching


class TestSearchMatching:
    def test_matches_substring_in_title(self, app):
        hit = svc.create_task("Buy groceries")
        svc.create_task("Walk dog")

        assert _ids(svc.search_tasks("grocer")) == [hit.id]

    def test_matches_substring_in_description(self, app):
        hit = svc.create_task("Errand", description="Pick up the dry cleaning")
        svc.create_task("Other", description="Nothing relevant")

        assert _ids(svc.search_tasks("cleaning")) == [hit.id]

    def test_match_is_case_insensitive_on_title(self, app):
        hit = svc.create_task("Write REPORT")

        assert _ids(svc.search_tasks("report")) == [hit.id]
        assert _ids(svc.search_tasks("RePoRt")) == [hit.id]

    def test_match_is_case_insensitive_on_description(self, app):
        hit = svc.create_task("Errand", description="call the BANK")

        assert _ids(svc.search_tasks("Bank")) == [hit.id]

    def test_matches_title_or_description(self, app):
        by_title = svc.create_task("Plan holiday")
        by_desc = svc.create_task("Book flights", description="for the holiday")
        svc.create_task("Unrelated", description="nothing here")

        assert set(_ids(svc.search_tasks("holiday"))) == {by_title.id, by_desc.id}

    def test_task_matching_both_fields_appears_once(self, app):
        hit = svc.create_task("Budget", description="monthly budget review")

        assert _ids(svc.search_tasks("budget")) == [hit.id]

    def test_no_match_returns_empty_list(self, app):
        svc.create_task("Buy milk")

        assert svc.search_tasks("zebra") == []


# --------------------------------------------------------------------------- whitespace


class TestSearchWhitespace:
    def test_leading_and_trailing_spaces_are_ignored(self, app):
        hit = svc.create_task("Buy milk")

        assert _ids(svc.search_tasks("   milk   ")) == [hit.id]

    def test_inner_spaces_are_kept(self, app):
        hit = svc.create_task("Buy milk")
        svc.create_task("Buy", description="milk later")

        assert _ids(svc.search_tasks("  buy milk  ")) == [hit.id]


# --------------------------------------------------------------------------- order


class TestSearchOrder:
    def test_results_are_newest_first(self, app):
        first = svc.create_task("Report one")
        svc.create_task("Unrelated")
        second = svc.create_task("Other", description="report two")
        third = svc.create_task("Report three")

        assert _ids(svc.search_tasks("report")) == [third.id, second.id, first.id]


# --------------------------------------------------------------------------- empty query


class TestSearchEmptyQuery:
    @pytest.mark.parametrize("query", ["", "   ", "\t\n", None])
    def test_empty_or_missing_query_raises(self, app, query):
        svc.create_task("Buy milk")

        with pytest.raises(ValidationError) as exc:
            svc.search_tasks(query)

        assert "query" in exc.value.message


# --------------------------------------------------------------------------- special characters


class TestSearchSpecialCharacters:
    def test_percent_matches_literally(self, app):
        hit = svc.create_task("50% off sale")
        svc.create_task("Order 500 units")

        assert _ids(svc.search_tasks("50%")) == [hit.id]

    def test_percent_alone_does_not_match_everything(self, app):
        hit = svc.create_task("Discount 10%")
        svc.create_task("Buy milk")

        assert _ids(svc.search_tasks("%")) == [hit.id]

    def test_underscore_matches_literally(self, app):
        hit = svc.create_task("rename file_name")
        svc.create_task("rename fileXname")

        assert _ids(svc.search_tasks("file_name")) == [hit.id]

    def test_underscore_alone_does_not_match_everything(self, app):
        hit = svc.create_task("snake_case")
        svc.create_task("Buy milk")

        assert _ids(svc.search_tasks("_")) == [hit.id]

    def test_backslash_matches_literally(self, app):
        hit = svc.create_task(r"Fix C:\temp path")
        svc.create_task("Fix temp path")

        assert _ids(svc.search_tasks("\\temp")) == [hit.id]


# --------------------------------------------------------------------------- route


class TestSearchRoute:
    def test_returns_matching_tasks_as_json_list(self, client):
        oldest = client.post("/tasks", json={"title": "Buy milk"}).get_json()
        older = client.post("/tasks", json={"title": "Milk the cow"}).get_json()
        newer = client.post("/tasks", json={"title": "x", "description": "oat MILK"}).get_json()
        client.post("/tasks", json={"title": "Walk dog"})

        response = client.get("/tasks/search", query_string={"q": "  milk "})

        assert response.status_code == 200
        body = response.get_json()
        assert isinstance(body, list)
        assert [t["id"] for t in body] == [newer["id"], older["id"], oldest["id"]]
        assert body[0]["description"] == "oat MILK"

    def test_no_match_returns_empty_list(self, client):
        client.post("/tasks", json={"title": "Buy milk"})

        response = client.get("/tasks/search", query_string={"q": "zebra"})

        assert response.status_code == 200
        assert response.get_json() == []

    def test_percent_is_literal_via_route(self, client):
        hit = client.post("/tasks", json={"title": "50% off"}).get_json()
        client.post("/tasks", json={"title": "500 units"})

        response = client.get("/tasks/search", query_string={"q": "50%"})

        assert response.status_code == 200
        assert [t["id"] for t in response.get_json()] == [hit["id"]]

    @pytest.mark.parametrize("params", [{"q": ""}, {"q": "   "}, {}])
    def test_empty_or_missing_query_returns_400(self, client, params):
        response = client.get("/tasks/search", query_string=params)

        assert response.status_code == 400
        assert "query" in response.get_json()["error"]
