"""HTTP tests for the lyrics endpoint."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from migmusic.domain.entities.lyrics import LyricLine, Lyrics


class StubProvider:
    """Minimal ``LyricsProvider`` double installed on ``app.state``."""

    def __init__(self, result: Lyrics | None = None) -> None:
        self.result = result

    async def find(self, *, title: str, artist: str, duration: float = 0.0) -> Lyrics | None:
        return self.result


def _client_with_lyrics(settings: Any, result: Lyrics | None) -> TestClient:
    from migmusic.main import create_app

    app = create_app(settings)
    app.state.lyrics_service._provider = StubProvider(result)
    return TestClient(app)


def test_returns_lyrics_for_the_posted_track(settings: Any) -> None:
    client = _client_with_lyrics(settings, Lyrics(text="La\nLa", source="lrclib"))

    response = client.post(
        "/api/lyrics",
        json={"title": "Song", "artist": "Artist", "source": "local", "duration": 200},
    )

    assert response.status_code == 200
    assert response.json() == {"text": "La\nLa", "source": "lrclib", "synced": False, "lines": []}


def test_returns_timed_lines_when_synced(settings: Any) -> None:
    client = _client_with_lyrics(
        settings,
        Lyrics(
            text="One\nTwo",
            source="lrclib",
            synced=True,
            lines=(LyricLine(time=12.5, text="One"), LyricLine(time=15.0, text="Two")),
        ),
    )

    response = client.post("/api/lyrics", json={"title": "Song", "source": "local"})

    assert response.status_code == 200
    assert response.json()["synced"] is True
    assert response.json()["lines"] == [
        {"time": 12.5, "text": "One"},
        {"time": 15.0, "text": "Two"},
    ]


def test_answers_204_when_no_lyrics_exist(settings: Any) -> None:
    client = _client_with_lyrics(settings, None)

    response = client.post("/api/lyrics", json={"title": "Unknown", "source": "youtube"})

    assert response.status_code == 204
    assert response.content == b""


def test_rejects_a_blank_title(settings: Any) -> None:
    client = _client_with_lyrics(settings, Lyrics(text="x", source="lrclib"))

    response = client.post("/api/lyrics", json={"title": ""})

    assert response.status_code == 422


def test_rejects_an_oversized_title(settings: Any) -> None:
    client = _client_with_lyrics(settings, Lyrics(text="x", source="lrclib"))

    response = client.post("/api/lyrics", json={"title": "a" * 400})

    assert response.status_code == 422


def test_a_synced_payload_keeps_the_text_usable(settings: Any) -> None:
    client = _client_with_lyrics(
        settings,
        Lyrics(text="One\nTwo", source="lrclib", synced=True),
    )

    response = client.post("/api/lyrics", json={"title": "Song", "source": "local"})

    assert response.status_code == 200
    assert response.json()["text"] == "One\nTwo"
