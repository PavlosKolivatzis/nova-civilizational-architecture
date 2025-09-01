import asyncio
import pytest

from content_analysis import analyze_content, analyze_content_sync


@pytest.mark.asyncio
async def test_analyze_content_async() -> None:
    res = await analyze_content("hello world")
    assert res["characters"] == 11
    assert res["words"] == 2


def test_analyze_content_sync() -> None:
    res = analyze_content_sync("hi there")
    assert res == {"characters": 8, "words": 2}


@pytest.mark.asyncio
async def test_analyze_content_concurrent() -> None:
    texts = ["one", "two words", "three word test"]
    results = await asyncio.gather(*(analyze_content(t) for t in texts))
    assert [r["words"] for r in results] == [1, 2, 3]
