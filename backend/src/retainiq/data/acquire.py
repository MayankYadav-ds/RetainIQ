"""Private raw objects, staged in the destination filesystem."""

import io
import os
import stat
import tempfile
import time
import zipfile
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO

import httpx

from .contract import CSV_SHA, DEMO, HEADERS, UCI, URL, ZIP_SHA, checked_id, encoded, file_sha

LIMIT = 2_000_000
MEMBER = "Customer Churn.csv"


def download(out: BinaryIO) -> None:
    with httpx.Client(timeout=httpx.Timeout(15, connect=5), follow_redirects=False) as client:
        for attempt in range(3):
            out.seek(0)
            out.truncate()
            try:
                with client.stream("GET", URL, headers={"Accept-Encoding": "identity"}) as resp:
                    if resp.is_redirect:
                        raise ValueError("redirect_denied")
                    resp.raise_for_status()
                    if resp.headers.get("Content-Encoding", "identity").lower() != "identity":
                        raise ValueError("unsupported_transport_encoding")
                    if int(resp.headers.get("Content-Length", "0")) > LIMIT:
                        raise ValueError("download_limit")
                    for b in resp.iter_bytes(65536):
                        if out.tell() + len(b) > LIMIT:
                            raise ValueError("download_limit")
                        out.write(b)
                return
            except httpx.TransportError:
                if attempt == 2:
                    raise ValueError("download_interrupted") from None
                time.sleep(0.2 * (attempt + 1))


def csv_bytes(raw: bytes) -> bytes:
    if not raw.startswith(b"PK"):
        return raw
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        entries = z.infolist()
        if len(entries) != 1:
            raise ValueError("archive_inventory")
        item = entries[0]
        mode = stat.S_IFMT(item.external_attr >> 16)
        if item.filename != MEMBER or mode not in (0, stat.S_IFREG) or item.flag_bits & 1:
            raise ValueError("unsupported_archive_member")
        if item.file_size > LIMIT or item.file_size > 100 * max(1, item.compress_size):
            raise ValueError("archive_expansion")
        with z.open(item) as f:
            result = f.read(LIMIT + 1)
        if len(result) != item.file_size or len(result) > LIMIT:
            raise ValueError("archive_size")
        return result


def fixture() -> bytes:
    import csv

    s = io.StringIO(newline="")
    w = csv.writer(s, lineterminator="\n")
    w.writerow(HEADERS)
    for i in range(40):
        w.writerow(
            [i % 4, i % 2, 8 + i, 3, i * 9, 4 + i, i, 4, 2, 1, 1, 30, i + 0.25, int(i % 5 == 0)]
        )
    return s.getvalue().encode()


@contextmanager
def staging(root: Path) -> Iterator[Path]:
    base = root / "staging"
    base.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=base) as tmp:
        yield Path(tmp)


def publish_dir(stage: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.rename(stage, dest)
    except OSError:
        if not dest.is_dir():
            raise
        # A concurrent publisher won. Caller must verify the committed version.


def acquire(root: Path, dataset: str, local: Path | None = None) -> str:
    checked_id(dataset)
    if dataset == DEMO and local:
        raise ValueError("fixture_is_generated")
    with staging(root) as temp:
        folder = temp / "raw"
        folder.mkdir()
        path = folder / "source"
        with path.open("wb") as out:
            if dataset == DEMO:
                out.write(fixture())
            elif local:
                with local.open("rb") as f:
                    while b := f.read(65536):
                        if out.tell() + len(b) > LIMIT:
                            raise ValueError("download_limit")
                        out.write(b)
            else:
                download(out)
        sha = file_sha(path)
        if dataset == UCI and sha not in (ZIP_SHA, CSV_SHA):
            raise ValueError("official_checksum_mismatch")
        csv_bytes(path.read_bytes())
        (folder / "receipt.json").write_bytes(
            encoded({"acquired_at": datetime.now(UTC).isoformat(), "sha256": sha})
        )
        dest = root / "raw" / dataset / sha
        publish_dir(folder, dest)
        if file_sha(dest / "source") != sha:
            raise ValueError("raw_corruption")
        return sha
