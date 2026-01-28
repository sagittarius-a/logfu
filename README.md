# logfu

[![CI](https://github.com/Sagittarius-a/logfu/actions/workflows/ci.yml/badge.svg)](https://github.com/Sagittarius-a/logfu/actions/workflows/ci.yml)

> Write streams or files to a bounded file (by size or line count).

`logfu` provides the `log` CLI, a small Unix-style utility that acts as a bounded sink: it consumes
data (from `stdin` or a file), writes it to a file, and guarantees that the file never exceeds a
given size or number of lines, always keeping the most recent content.

## Installation

### Using pip

`logfu` can be installed as a regular Python package:

```sh
pip install logfu
```

### Single-file installation

It can also be installed as a standalone executable by copying the entry point
to a standard location such as `/usr/local/bin`:

```sh
sudo cp ./log/__main__.py /usr/local/bin/log
sudo chmod +x /usr/local/bin/log
```

## Usage

```sh
$ log --help
usage: log [-h] -o OUTPUT [-f] [-s SIZE | -l LINES] [input]

Write streams or files with size or line limits.

positional arguments:
  input                Input file (defaults to stdin)

options:
  -h, --help           show this help message and exit
  -o, --output OUTPUT  Output file path
  -f, --follow         Read stdin incrementally and keep output bounded
  -s, --size SIZE      Maximum size (bytes, supports K/M/G/T)
  -l, --lines LINES    Maximum number of lines
```

## Examples

### Keep the last 10MB of a command’s output

```sh
some_command | log --size 10M --output app.log
```

### Keep the last 1000 lines of a live stream

```sh
journalctl -f | log --follow --lines 1000 --output journal.log
```

### Truncate an existing file in place

```sh
log --size 5M --output app.log app.log
```

### Line-based truncation of a text file

```sh
log -l 200 -o notes.txt notes.txt
```

## Follow mode (`--follow`)

When `--follow` is enabled, `log` reads from stdin incrementally and updates the output file as new data arrives.

```sh
some_long_running_command | log --follow --size 20M --output output.log
```

Properties:

- streaming (no full buffering)
- bounded memory usage
- atomic file updates
- suitable for long-running pipelines

**Note**: `--follow` keeps running until stdin closes or the process is terminated.

## Size format

`--size` accepts human-readable units:

| Suffix | Meaning     |
|--------|-------------|
| `K`    | 1024 bytes  |
| `M`    | 1024² bytes |
| `G`    | 1024³ bytes |
| `T`    | 1024⁴ bytes |


### Examples

```sh
log --size 512  # Limit to 512 bytes
log --size 10K  # Limit to 10 kilobytes
log --size 2M   # Limit to 2 megabytes
```

## Atomicity and safety

All writes are performed via a temporary file followed by an atomic rename.

This guarantees that:

- readers never observe partial writes
- in-place truncation is safe
- crashes do not corrupt the output file

---

## Why creating `logfu`

Unix has excellent tools for reading, selecting, and duplicating data:

- `tail` selects the end of a stream or file
- `tee` duplicates a stream to files
- `truncate` changes file size
- `logrotate` rotates files offline

What Unix lacks is a tool that can continuously write data to a file while enforcing bounds on that file.

That gap is exactly what `log` fills.

### What `log` does that coreutils don’t

### `tail` is a reader, not a writer

`tail` can select the last N lines or bytes, but it only writes to stdout.

```sh
tail -n 100 file.log
```

It cannot do this:

```sh
tail -n 100 file.log > file.log
```

And it cannot act as a sink in a pipeline.

### `tee` writes, but never limits

```sh
some_command | tee app.log
```

This file grows forever. There is no way to tell `tee`:

> Keep only the last 10MB of what you write.

### `truncate` is blind to content

```sh
truncate -s 10M app.log
```

- works only on files
- truncates from the end
- has no notion of _most recent data_
- cannot be used on streams

## What `log` provides

`log` combines the missing pieces into a single, composable primitive:

- consumes `stdin` or a file
- writes to a file atomically
- enforces limits by:
    - raw size (`--size`)
    - number of lines (`--lines`)
- always keeps the most recent content
- can run continuously (`--follow`)

In other words, `log` is a **bounded sink**.

### Non-goals

`log` intentionally does not:

- rotate files
- compress logs
- multiplex outputs
- act as a logging framework

It is a small, sharp Unix tool designed to compose with others.
