#!/usr/bin/env python3

"""Write streams or files with size or line limits."""

from __future__ import annotations

import argparse
import os
import sys
import tempfile

from collections import deque
from pathlib import Path
from typing import BinaryIO, TextIO, Optional, Protocol, cast

_SIZE_MULTIPLIERS = {
    "K": 1024,
    "M": 1024**2,
    "G": 1024**3,
    "T": 1024**4,
}


class ReadableBinaryStream(Protocol):
    """
    Binary stream supporting non-blocking partial reads.
    """

    def read1(self, size: int) -> bytes: ...


def parse_size(value: str) -> int:
    """Parse a human-readable size string.

    Parameters
    ----------
    value : str
        Size specification, e.g. "1024", "10K", "5M", "1G".

    Returns
    -------
    int
        Size in bytes.

    Raises
    ------
    ValueError
        If the format is invalid.

    """
    value = value.strip().upper()
    if value[-1].isdigit():
        return int(value)

    multiplier = _SIZE_MULTIPLIERS.get(value[-1])
    if multiplier is None:
        raise ValueError(f"Invalid size suffix: {value[-1]!r}")

    return int(value[:-1]) * multiplier


def read_all_binary(stream: BinaryIO) -> bytes:
    """Read all data from a binary stream.

    Parameters
    ----------
    stream : BinaryIO
        Input stream.

    Returns
    -------
    bytes
        Stream content.

    """
    return stream.read()


def tail_bytes(data: bytes, max_size: int) -> bytes:
    """Keep only the last N bytes.

    Parameters
    ----------
    data : bytes
        Input data.
    max_size : int
        Maximum size in bytes.

    Returns
    -------
    bytes
        Truncated data.

    """
    if len(data) <= max_size:
        return data
    return data[-max_size:]


def tail_lines(text: str, max_lines: int) -> str:
    """Keep only the last N lines.

    Parameters
    ----------
    text : str
        Input text.
    max_lines : int
        Maximum number of lines.

    Returns
    -------
    str
        Truncated text.

    """
    lines = text.splitlines(keepends=True)
    if len(lines) <= max_lines:
        return text
    return "".join(lines[-max_lines:])


def atomic_write(path: Path, data: bytes) -> None:
    """Atomically write data to a file.

    Parameters
    ----------
    path : Path
        Destination path.
    data : bytes
        Data to write.

    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=str(path.parent),
        delete=False,
    ) as tmp:
        tmp.write(data)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_path = Path(tmp.name)

    tmp_path.replace(path)


def stream_tail_bytes(
    stream: ReadableBinaryStream,
    max_size: int,
    output: Path,
    chunk_size: int = 8192,
) -> None:
    """
    Continuously read bytes and keep only the last max_size bytes.

    Parameters
    ----------
    stream : ReadableBinaryStream
        Input stream.
    max_size : int
        Maximum size in bytes.
    output : Path
        Output file.
    chunk_size : int
        Read chunk size.
    """
    buffer = bytearray()

    while True:
        chunk = stream.read1(chunk_size)
        if not chunk:
            break

        buffer.extend(chunk)
        if len(buffer) > max_size:
            del buffer[:-max_size]

        atomic_write(output, bytes(buffer))


def get_binary_stdin() -> ReadableBinaryStream:
    stream = sys.stdin.buffer
    assert hasattr(stream, "read1")
    return cast(ReadableBinaryStream, stream)


def stream_tail_lines(
    stream: TextIO,
    max_lines: int,
    output: Path,
) -> None:
    """
    Continuously read lines and keep only the last max_lines lines.

    Parameters
    ----------
    stream : TextIO
        Input stream.
    max_lines : int
        Maximum number of lines.
    output : Path
        Output file.
    """
    lines: deque[str] = deque(maxlen=max_lines)

    for line in stream:
        lines.append(line)
        atomic_write(output, "".join(lines).encode())


def main() -> None:
    """Handle command line arguments."""
    parser = argparse.ArgumentParser(
        prog="log",
        description="Write streams or files with size or line limits.",
    )

    parser.add_argument(
        "input",
        nargs="?",
        help="Input file (defaults to stdin)",
    )

    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output file path",
    )
    parser.add_argument(
        "-f",
        "--follow",
        action="store_true",
        help="Read stdin incrementally and keep output bounded",
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-s",
        "--size",
        help="Maximum size (bytes, supports K/M/G/T)",
    )
    group.add_argument(
        "-l",
        "--lines",
        type=int,
        help="Maximum number of lines",
    )

    args = parser.parse_args()

    if args.follow and args.input:
        parser.error("--follow can only be used with stdin")

    if args.follow and args.size is None and args.lines is None:
        parser.error("--follow requires --size or --lines")

    input_path: Optional[Path] = Path(args.input) if args.input else None
    output_path = Path(args.output)

    if args.lines is not None and args.lines <= 0:
        parser.error("--lines must be > 0")

    if args.size is not None:
        try:
            max_size = parse_size(args.size)
        except ValueError as e:
            parser.error(str(e))
    else:
        max_size = None

    if input_path:
        if args.lines is not None:
            text = input_path.read_text()
            result = tail_lines(text, args.lines)
            atomic_write(output_path, result.encode())
        else:
            data = input_path.read_bytes()
            if max_size is not None:
                data = tail_bytes(data, max_size)
            atomic_write(output_path, data)
    else:
        if args.follow:
            if args.lines is not None:
                stream_tail_lines(
                    sys.stdin,
                    args.lines,
                    output_path,
                )
            else:
                assert max_size is not None
                stream_tail_bytes(
                    get_binary_stdin(),
                    max_size,
                    output_path,
                )
        else:
            if args.lines is not None:
                text = sys.stdin.read()
                result = tail_lines(text, args.lines)
                atomic_write(output_path, result.encode())
            else:
                data = read_all_binary(sys.stdin.buffer)
                if max_size is not None:
                    data = tail_bytes(data, max_size)
                atomic_write(output_path, data)


if __name__ == "__main__":
    main()
