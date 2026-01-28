import time
import subprocess
import sys
from pathlib import Path


PYTHON = sys.executable


def wait_for_content(
    path: Path,
    expected: bytes,
    timeout: float = 1.0,
) -> None:
    """
    Wait until a file contains the expected content.

    Raises
    ------
    TimeoutError
        If the content does not match in time.
    """
    deadline = time.monotonic() + timeout
    last: bytes | None = None

    while time.monotonic() < deadline:
        if path.exists():
            data = path.read_bytes()
            if data == expected:
                return
            last = data
        time.sleep(0.01)

    raise TimeoutError(
        f"{path} content did not converge\nexpected={expected!r}\nlast={last!r}"
    )


def start_log_follow(
    args: list[str],
) -> subprocess.Popen[bytes]:
    """
    Start log in follow mode with stdin piped.

    Parameters
    ----------
    args : list[str]
        CLI arguments.

    Returns
    -------
    subprocess.Popen[bytes]
        Running process.

    """
    return subprocess.Popen(
        [PYTHON, "-m", "log", *args],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def test_follow_lines(tmp_path: Path) -> None:
    output = tmp_path / "out.txt"

    proc = start_log_follow(
        ["--follow", "--lines", "3", "--output", str(output)],
    )

    assert proc.stdin is not None

    lines = ["a\n", "b\n", "c\n", "d\n"]

    for i, line in enumerate(lines):
        proc.stdin.write(line.encode())
        proc.stdin.flush()

        expected = "".join(lines[max(0, i - 2) : i + 1])
        wait_for_content(output, expected.encode())

    proc.stdin.close()
    proc.wait(timeout=2)


def test_follow_size(tmp_path: Path) -> None:
    output = tmp_path / "out.bin"

    proc = start_log_follow(
        ["--follow", "--size", "5", "--output", str(output)],
    )

    assert proc.stdin is not None

    chunks = [b"123", b"45", b"678"]

    expected_states = [
        b"123",
        b"12345",
        b"45678",
    ]

    for chunk, expected in zip(chunks, expected_states):
        proc.stdin.write(chunk)
        proc.stdin.flush()

        wait_for_content(output, expected)

    proc.stdin.close()
    proc.wait(timeout=2)


def test_follow_requires_limit() -> None:
    proc = subprocess.run(
        [PYTHON, "-m", "log", "--follow", "--output", "out"],
        stderr=subprocess.PIPE,
    )

    assert proc.returncode != 0
    assert b"--follow requires" in proc.stderr


def test_follow_rejects_file_input(tmp_path: Path) -> None:
    input_file = tmp_path / "input.txt"
    input_file.write_text("test\n")

    proc = subprocess.run(
        [
            PYTHON,
            "-m",
            "log",
            "--follow",
            "--lines",
            "1",
            "--output",
            "out",
            str(input_file),
        ],
        stderr=subprocess.PIPE,
    )

    assert proc.returncode != 0
    assert b"--follow can only be used with stdin" in proc.stderr
