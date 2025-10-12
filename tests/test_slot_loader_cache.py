# ruff: noqa: E402
import time
from src_bootstrap import ensure_src_on_path

ensure_src_on_path()

from nova import slot_loader


def test_find_file_uses_cache(tmp_path, monkeypatch):
    # Create a dummy file to locate
    target = tmp_path / "foo.txt"
    target.write_text("data")

    # Ensure cache is empty
    slot_loader._FILE_CACHE.clear()

    call_count = 0
    real_walk = slot_loader.os.walk

    def counting_walk(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        yield from real_walk(*args, **kwargs)

    monkeypatch.setattr(slot_loader.os, "walk", counting_walk)

    slot_loader.find_file("foo", base_dir=str(tmp_path))
    assert call_count == 1

    # Second call should use cache and avoid os.walk
    slot_loader.find_file("foo", base_dir=str(tmp_path))
    assert call_count == 1

    # Refresh should trigger another walk
    slot_loader.find_file("foo", base_dir=str(tmp_path), refresh=True)
    assert call_count == 2


def test_cached_lookup_faster(tmp_path, monkeypatch):
    for i in range(10):
        (tmp_path / f"file{i}.py").write_text("data")

    slot_loader._FILE_CACHE.clear()

    real_walk = slot_loader.os.walk

    def slow_walk(*args, **kwargs):
        time.sleep(0.01)
        yield from real_walk(*args, **kwargs)

    monkeypatch.setattr(slot_loader.os, "walk", slow_walk)

    start = time.perf_counter()
    slot_loader.find_file("file1", base_dir=str(tmp_path))
    uncached = time.perf_counter() - start

    start = time.perf_counter()
    slot_loader.find_file("file2", base_dir=str(tmp_path))
    cached = time.perf_counter() - start

    assert cached < uncached / 2
