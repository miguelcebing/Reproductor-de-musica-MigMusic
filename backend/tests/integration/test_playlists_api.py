"""Tests for the playlist CRUD endpoints."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi.testclient import TestClient

PlaylistPayload = dict[str, Any]
CreatePlaylist = Callable[..., PlaylistPayload]
FilledPlaylist = Callable[..., PlaylistPayload]


def test_create_playlist_returns_201(client: TestClient, create_playlist: CreatePlaylist) -> None:
    """``PLAYLIST-002`` over HTTP: an empty playlist with a generated id."""
    response = client.post("/api/playlists", json={"name": "Road trip"})

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Road trip"
    assert body["size"] == 0
    assert body["songs"] == []
    assert body["current_index"] is None
    assert body["id"]


def test_create_playlist_rejects_an_empty_name(
    client: TestClient, create_playlist: CreatePlaylist
) -> None:
    """The domain rule surfaces as the uniform 422 envelope."""
    response = client.post("/api/playlists", json={"name": "   "})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert "playlist name" in error["message"]


def test_list_playlists_returns_every_playlist(
    client: TestClient, create_playlist: CreatePlaylist
) -> None:
    """``PLAYLIST-001 = B``: the collection endpoint lists them all."""
    create_playlist("First")
    create_playlist("Second")

    response = client.get("/api/playlists")

    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == ["First", "Second"]


def test_playlists_are_scoped_by_the_device_header(client: TestClient) -> None:
    """`X-Device-Id` isolates playlists per device (UX isolation, not auth)."""
    phone = {"X-Device-Id": "device-a"}
    laptop = {"X-Device-Id": "device-b"}
    assert (
        client.post("/api/playlists", json={"name": "Phone mix"}, headers=phone).status_code == 201
    )
    assert (
        client.post("/api/playlists", json={"name": "Laptop mix"}, headers=laptop).status_code
        == 201
    )

    from_a = client.get("/api/playlists", headers=phone)
    from_b = client.get("/api/playlists", headers=laptop)

    assert [item["name"] for item in from_a.json()] == ["Phone mix"]
    assert [item["name"] for item in from_b.json()] == ["Laptop mix"]


def test_a_missing_device_header_is_rejected(client: TestClient) -> None:
    """Without the header there is no owner, so the call is refused (400)."""
    response = client.get("/api/playlists", headers={"X-Device-Id": ""})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "http_error"


def test_a_blank_device_header_is_rejected(client: TestClient) -> None:
    """Whitespace-only headers are not a device either."""
    response = client.get("/api/playlists", headers={"X-Device-Id": "   "})

    assert response.status_code == 400


def test_a_device_cannot_read_anothers_playlist(client: TestClient) -> None:
    """A foreign UUID answers 404 instead of exposing its songs (IDOR)."""
    created = client.post(
        "/api/playlists", json={"name": "Phone mix"}, headers={"X-Device-Id": "device-a"}
    ).json()

    response = client.get(
        f"/api/playlists/{created['id']}", headers={"X-Device-Id": "device-b"}
    )

    assert response.status_code == 404


def test_a_device_cannot_mutate_anothers_playlist(client: TestClient) -> None:
    """Rename, delete and add are all refused (404) for a foreign playlist."""
    created = client.post(
        "/api/playlists", json={"name": "Phone mix"}, headers={"X-Device-Id": "device-a"}
    ).json()
    other = {"X-Device-Id": "device-b"}
    url = f"/api/playlists/{created['id']}"

    assert client.patch(url, json={"name": "Hijacked"}, headers=other).status_code == 404
    assert (
        client.post(
            f"{url}/songs",
            json={"song": {"id": "x", "title": "x", "artist": "x", "source": "local"}},
            headers=other,
        ).status_code
        == 404
    )
    assert client.delete(url, headers=other).status_code == 404
    # The owner still sees the untouched playlist.
    from_owner = client.get(url, headers={"X-Device-Id": "device-a"})
    assert from_owner.status_code == 200
    assert from_owner.json()["name"] == "Phone mix"


def test_get_playlist_returns_its_songs_in_order(
    client: TestClient, filled_playlist: FilledPlaylist
) -> None:
    """Songs come back in list order, with the computed duration label."""
    payload = filled_playlist(count=3)

    response = client.get(f"/api/playlists/{payload['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["size"] == 3
    assert [song["title"] for song in body["songs"]] == ["Song 0", "Song 1", "Song 2"]
    assert body["songs"][0]["duration_label"] == "3:00"


def test_get_unknown_playlist_returns_a_404_envelope(client: TestClient) -> None:
    """404s are structured the same way everywhere."""
    response = client.get("/api/playlists/nope")

    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "not_found"
    assert error["request_id"]


def test_rename_playlist(client: TestClient, create_playlist: CreatePlaylist) -> None:
    """``PLAYLIST-003`` over HTTP."""
    payload = create_playlist("Old")

    response = client.patch(f"/api/playlists/{payload['id']}", json={"name": "New"})

    assert response.status_code == 200
    assert response.json()["name"] == "New"


def test_rename_with_an_empty_name_is_422(
    client: TestClient, create_playlist: CreatePlaylist
) -> None:
    """Validation happens once, in the domain."""
    payload = create_playlist("Old")

    response = client.patch(f"/api/playlists/{payload['id']}", json={"name": ""})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_delete_playlist_then_404(client: TestClient, create_playlist: CreatePlaylist) -> None:
    """Deletion answers 204 and the playlist disappears."""
    payload = create_playlist()

    deleted = client.delete(f"/api/playlists/{payload['id']}")

    assert deleted.status_code == 204
    assert deleted.content == b""
    assert client.get(f"/api/playlists/{payload['id']}").status_code == 404


def test_delete_unknown_playlist_returns_404(client: TestClient) -> None:
    """Deleting nothing is not a success."""
    response = client.delete("/api/playlists/nope")

    assert response.status_code == 404


def test_append_song(client: TestClient, create_playlist: CreatePlaylist) -> None:
    """Default insertion is at the tail."""
    payload = create_playlist()

    response = client.post(
        f"/api/playlists/{payload['id']}/songs",
        json={
            "song": {"id": "local-1", "title": "Nocturne", "artist": "Chopin", "source": "local"}
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["size"] == 1
    assert body["songs"][0]["title"] == "Nocturne"


def test_insert_song_at_a_position(client: TestClient, filled_playlist: FilledPlaylist) -> None:
    """``UX-003``: the modal can target an arbitrary position."""
    payload = filled_playlist(count=3)

    response = client.post(
        f"/api/playlists/{payload['id']}/songs",
        json={
            "song": {
                "id": "local-mid",
                "title": "Inserted",
                "artist": "MigMusic",
                "source": "local",
            },
            "index": 1,
        },
    )

    assert response.status_code == 201
    titles = [song["title"] for song in response.json()["songs"]]
    assert titles == ["Song 0", "Inserted", "Song 1", "Song 2"]


def test_add_song_with_invalid_domain_data_is_422(
    client: TestClient, create_playlist: CreatePlaylist
) -> None:
    """Structurally valid but domain-invalid data still fails uniformly."""
    payload = create_playlist()

    response = client.post(
        f"/api/playlists/{payload['id']}/songs",
        json={"song": {"id": "local-1", "title": "  ", "artist": "x", "source": "local"}},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_remove_song_returns_it(client: TestClient, filled_playlist: FilledPlaylist) -> None:
    """The removed song comes back so the UI can undo."""
    payload = filled_playlist(count=3)

    response = client.delete(f"/api/playlists/{payload['id']}/songs/1")

    assert response.status_code == 200
    assert response.json()["title"] == "Song 1"
    assert response.json()["id"] == "local-1"


def test_remove_song_out_of_range_is_422(
    client: TestClient, filled_playlist: FilledPlaylist
) -> None:
    """Index bounds are enforced by the list."""
    payload = filled_playlist(count=2)

    response = client.delete(f"/api/playlists/{payload['id']}/songs/9")

    assert response.status_code == 422


def test_move_song_reorders_the_list(client: TestClient, filled_playlist: FilledPlaylist) -> None:
    """``FEAT-001-e``: reorder through the API."""
    payload = filled_playlist(count=3)

    response = client.put(
        f"/api/playlists/{payload['id']}/songs/order",
        json={"from_index": 0, "to_index": 2},
    )

    assert response.status_code == 200
    ids = [song["id"] for song in response.json()["songs"]]
    assert ids == ["local-1", "local-2", "local-0"]


def test_move_song_out_of_range_is_422(client: TestClient, filled_playlist: FilledPlaylist) -> None:
    """Both bounds are checked before anything moves."""
    payload = filled_playlist(count=3)

    response = client.put(
        f"/api/playlists/{payload['id']}/songs/order",
        json={"from_index": 0, "to_index": 9},
    )

    assert response.status_code == 422


def test_select_song_returns_the_playback_state(
    client: TestClient, filled_playlist: FilledPlaylist
) -> None:
    """Selecting a row activates the playlist and reports the transport state."""
    payload = filled_playlist(count=3)

    response = client.post(f"/api/playlists/{payload['id']}/songs/2/select")

    assert response.status_code == 200
    body = response.json()
    assert body["playlist_id"] == payload["id"]
    assert body["index"] == 2
    assert body["playing"] is True
    assert body["position"] == 0.0
    assert body["song"]["title"] == "Song 2"


def test_select_out_of_range_is_422(client: TestClient, filled_playlist: FilledPlaylist) -> None:
    """Selecting a row that does not exist is a validation error."""
    payload = filled_playlist(count=2)

    response = client.post(f"/api/playlists/{payload['id']}/songs/7/select")

    assert response.status_code == 422


def test_select_on_an_unknown_playlist_is_404(client: TestClient) -> None:
    """Unknown ids answer 404 across every endpoint."""
    response = client.post("/api/playlists/nope/songs/0/select")

    assert response.status_code == 404


def test_find_song_returns_the_first_match(
    client: TestClient, filled_playlist: FilledPlaylist
) -> None:
    """``FEAT-001-c``: GET .../songs/find answers index + song in one payload."""
    payload = filled_playlist(count=3)

    response = client.get(f"/api/playlists/{payload['id']}/songs/find", params={"text": "song 1"})

    assert response.status_code == 200
    body = response.json()
    assert body["index"] == 1
    assert body["song"]["title"] == "Song 1"


def test_find_song_without_matches_is_404(
    client: TestClient, filled_playlist: FilledPlaylist
) -> None:
    """A quiet miss: the uniform envelope, so the UI can show 'no results'."""
    payload = filled_playlist(count=3)

    response = client.get(f"/api/playlists/{payload['id']}/songs/find", params={"text": "zzz"})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_find_song_rejects_blank_text(client: TestClient, filled_playlist: FilledPlaylist) -> None:
    """Empty queries never walk the list."""
    payload = filled_playlist(count=3)

    response = client.get(f"/api/playlists/{payload['id']}/songs/find", params={"text": "   "})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_favorite_round_trip(client: TestClient, filled_playlist: FilledPlaylist) -> None:
    """``FEAT-001-b``: mark, read back through the listing, then clear."""
    payload = filled_playlist(count=2)
    url = f"/api/playlists/{payload['id']}/songs/1/favorite"

    marked = client.put(url, json={"favorite": True})

    assert marked.status_code == 200
    assert marked.json()["favorite"] is True

    listed = client.get(f"/api/playlists/{payload['id']}")
    songs = listed.json()["songs"]
    assert songs[1]["favorite"] is True
    assert songs[0]["favorite"] is False

    cleared = client.put(url, json={"favorite": False})
    assert cleared.status_code == 200
    assert cleared.json()["favorite"] is False


def test_favorite_on_a_missing_index_is_422(
    client: TestClient, filled_playlist: FilledPlaylist
) -> None:
    """Index bounds keep the standard validation envelope."""
    payload = filled_playlist(count=2)

    response = client.put(
        f"/api/playlists/{payload['id']}/songs/9/favorite", json={"favorite": True}
    )

    assert response.status_code == 422
