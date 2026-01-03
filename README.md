# mcodex

**mcodex** is an opinionated CLI tool for managing *prose writing projects*.

It does **not** help you write text.  
It helps you manage **versions, snapshots, exports, and editorial states** around writing — in a way that is explicit, reproducible, and Git-based.

## What mcodex is for

mcodex answers questions like:

- Which versions of this text exist?
- In which state was the text when I sent it out?
- Can I reproduce *exactly* the document I sent months ago?
- How do I keep drafts, snapshots, and exports organized without friction?

mcodex is designed for authors who:

- write in Markdown,
- are comfortable with Git,
- prefer transparent, scriptable workflows over GUI-heavy writing apps.

## What mcodex is *not*

mcodex deliberately does **not** try to be:

- a text editor
- a writing application (Scrivener, Ulysses, etc.)
- a CMS or publishing platform
- a collaborative web tool
- a Git replacement
- a diff or annotation system

Writing happens elsewhere.  
mcodex manages what *surrounds* writing.

## Core principles

### 1. Text-first, Markdown-only sources

All authoritative sources are plain text (Markdown + TOML/YAML metadata).

No proprietary formats are ever treated as sources of truth.

### 2. Snapshots are explicit

A snapshot is a **deliberate, named state** of a text.

- It is created intentionally.
- It has a human-readable label (`draft-2`, `beta-1`, `final`, …).
- It is recorded as part of the project history.
- It is frozen via Git (commit + tag).

Snapshots are **not** just commits you happen to make.

### 3. Reproducibility over convenience

If a document was sent out, it must be possible to reproduce it exactly:

- same content
- same structure
- same metadata
- same author identity
- same point in time

Dynamic values are avoided; frozen metadata is preferred.

### 4. Git is infrastructure, not UI

mcodex requires Git, but:

- does not enforce a specific Git workflow,
- does not hide Git operations,
- does not replace Git concepts with abstractions.

Git is used as a reliable storage and history mechanism — not as the primary interface.

### 5. Editorial reality over software abstraction

mcodex adapts to how authors and editors actually work:

- PDFs with annotations
- DOCX / ODT files with comments

mcodex records outcomes.  
It does not attempt to automate human judgment.

## Conceptual model

### Text

A **text** is represented by a directory.

At minimum, a text directory contains:

```text
<text-slug>/
├── text.md
├── metadata.yaml
└── stages/
```

- `text.md`  
  The authoritative Markdown source of the text.

- `metadata.yaml`  
  Frozen metadata describing the text (title, authors, creation time).

- `stages/`  
  Reserved for editorial states, snapshots, and future exports.

The directory name (`<text-slug>`) is derived from the text title and is stable.

### Metadata

Each text has explicit metadata stored in `metadata.yaml`.

Example:

```yaml
id: "a3c0e7d2-1d7f-4b6e-8a6f-9f6a9d1e2c44"
title: "Článek o něčem"
slug: "clanek_o_necem"
created_at: "2026-01-03T14:22:10+01:00"
authors:
  - nickname: celestian
    first_name: Jan
    last_name: Novák
    email: jan.novak@example.com
```

Metadata is **authoritative and self-contained**.

Even if global configuration is lost, a text directory still carries all
information needed to identify authorship and origin.

### Author identity

Authors are managed explicitly and identified by a stable **nickname**.

An author consists of:

- `nickname` (stable handle, used in CLI)
- `first_name`
- `last_name`
- `email`

Authors are stored globally for convenience, but **copied into text metadata**
when a text is created.

This guarantees reproducibility and independence from user configuration.

## Current capabilities

At the current stage, mcodex supports:

- registering authors
- listing known authors
- creating new text directories
- attaching one or more authors to a text at creation time
- generating stable metadata
- enforcing reproducible structure

Example workflow:

```bash
mcodex author add celestian "Jan" "Novák" jan.novak@example.com
mcodex author add eva "Eva Marie" "Svobodová" eva@example.com

mcodex create "Článek o něčem" \
  --author=celestian \
  --author=eva
```

Result:

```text
clanek_o_necem/
├── text.md
├── metadata.yaml
└── stages/
```

## Configuration

mcodex stores user-level configuration in:

```text
~/.config/mcodex/config.yaml
```

This configuration currently contains:

- the registry of known authors

Configuration is treated as **cache and convenience**, not as a source of truth.
Texts remain valid even if the configuration file is removed.

## Installation

mcodex is a Python CLI tool and is designed to be used with **uv**.

### Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart your shell, then verify:

```bash
uv --version
```

### Install mcodex (editable)

From the project root:

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

Verify:

```bash
mcodex --help
```

## Project status

mcodex is currently in an **early, opinionated stage**.

The focus is on:

- correctness
- explicitness
- reproducibility
- testability

Features will be added incrementally, with a strong preference for:
- simple CLI commands
- transparent file formats
- minimal hidden state
