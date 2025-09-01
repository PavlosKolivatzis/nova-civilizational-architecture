import asyncio
from typing import Any, Dict

async def analyze_content(content: str) -> Dict[str, Any]:
    """Asynchronously analyze textual content.

    The implementation is intentionally lightweight – it simply counts
    characters and words.  The coroutine structure mirrors the async
    patterns used elsewhere in the project and allows call sites to
    ``await`` the analysis when running inside an event loop.
    """
    # Yield control to ensure cooperative scheduling with other coroutines
    await asyncio.sleep(0)
    words = content.split()
    return {"characters": len(content), "words": len(words)}

def analyze_content_sync(content: str) -> Dict[str, Any]:
    """Synchronous wrapper around :func:`analyze_content`.

    This provides backward compatibility for call sites that are not
    ``async``-aware.  It runs the coroutine to completion using
    ``asyncio.run``, mirroring the approach taken in other modules of the
    repository.
    """
    return asyncio.run(analyze_content(content))
