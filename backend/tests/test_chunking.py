import pytest

from app.services.chunking import chunk_text


def test_short_text_produces_one_chunk() -> None:
    assert chunk_text("  short text  ", chunk_size=20, overlap=5) == ["short text"]


def test_empty_text_produces_no_chunks() -> None:
    assert chunk_text(" \n\t ", chunk_size=20, overlap=5) == []


def test_chunks_use_deterministic_overlap() -> None:
    text = "abcdefghijklmnopqrstuvwxyz"

    chunks = chunk_text(text, chunk_size=10, overlap=3)

    assert chunks == ["abcdefghij", "hijklmnopq", "opqrstuvwx", "vwxyz"]
    assert chunks[0][-3:] == chunks[1][:3]
    assert chunks[1][-3:] == chunks[2][:3]


@pytest.mark.parametrize(
    ("chunk_size", "overlap"),
    [(0, 0), (10, -1), (10, 10), (10, 11)],
)
def test_invalid_chunk_configuration_is_rejected(
    chunk_size: int, overlap: int
) -> None:
    with pytest.raises(ValueError):
        chunk_text("content", chunk_size=chunk_size, overlap=overlap)
