import html
import re


def test_dashboard_includes_book_summary(client):
    form_response = client.get("/books/new")
    game_system_id = re.search(
        rf'<option value="(\d+)">{re.escape(html.escape("D&D 5e"))}</option>',
        form_response.text,
    ).group(1)
    client.post(
        "/books/new",
        data={
            "title": "Physical Book",
            "game_system_id": game_system_id,
            "owns_physical": "on",
        },
    )
    client.post(
        "/books/new",
        data={
            "title": "Digital Book",
            "game_system_id": game_system_id,
            "owns_digital": "on",
        },
    )

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert 'class="stat-label">Total Books</div>' in response.text
    assert 'class="stat-label">Physical Books</div>' in response.text
    assert 'class="stat-label">Digital Books</div>' in response.text
    assert 'class="dashboard-section books-dashboard-section"' in response.text
    assert 'id="bookCollectionChart"' in response.text
    assert 'href="/books?game_system_id=' in response.text
