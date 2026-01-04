# mcodex

**mcodex** is an opinionated CLI tool for managing *prose writing projects*.

It does **not** help you write text.  
It helps you manage **versions, snapshots, metadata, and editorial states**
around writing — in a way that is explicit, reproducible, and Git-based.

---

## What mcodex is for

mcodex answers questions like:

- Which versions of this text exist?
- In which state was the text when I sent it out?
- Can I reproduce *exactly* the document I sent months ago?
- Which snapshot corresponds to which Git tag?

mcodex is designed for authors who:

- write in Markdown,
- are comfortable with Git,
- prefer transparent, scriptable workflows over GUI-heavy writing apps.

---

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

---

## Core principles

### 1. Text-first, Markdown-only sources

All authoritative sources are plain text:

- `text.md`
- `metadata.yaml`
- snapshot copies

No proprietary formats are ever treated as sources of truth.

---

### 2. Snapshots are explicit and named

A snapshot is a **deliberate, named state** of a text.

- created intentionally
- stored as a directory copy
- labeled (`draft-1`, `rc-2`, `final-1`, …)
- frozen in Git (commit + tag)
- recorded with metadata

Snapshots are **not** accidental commits.

---

### 3. Reproducibility over convenience

If a document was sent out, it must be possible to reproduce it exactly:

- same content
- same metadata
- same authorship
- same snapshot label
- same Git tag

Hidden state is avoided.
Everything relevant lives in the repository.

---

### 4. Git is infrastructure, not UI

mcodex requires Git, but:

- does not replace Git concepts
- does not invent a parallel history model
- does not hide Git operations

Git is storage and history — not the user interface.

---

### 5. Editorial reality over software abstraction

mcodex adapts to how authors and editors actually work:

- PDFs with annotations
- DOCX files with comments
- email attachments
- manual review cycles

mcodex records outcomes.  
It does not attempt to automate human judgment.

---

## Conceptual model

### Repository

A mcodex project is a **Git repository** initialized with:

```bash
mcodex init
```

This creates:

```text
.mcodex/
├── config.yaml
└── templates/
```

`.mcodex/config.yaml` is the **single source of configuration truth**.

There is **no global `~/.config`**.

---

### Text

A **text** is represented by a directory.

Minimal structure:

```text
<text-slug>/
├── text.md
├── metadata.yaml
└── .snapshot/
```

- `text.md`  
  Authoritative Markdown source.

- `metadata.yaml`  
  Frozen metadata (title, slug, authors, creation time).

- `.snapshot/`  
  Versioned snapshot directories.

The directory name (`<text-slug>`) is stable and derived from the title.

---

### Metadata

Each text carries its own authoritative metadata.

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

Metadata is **self-contained**.

Even if configuration is lost, a text directory still carries everything
needed to identify authorship and origin.

---

### Author identity

Authors are identified by a stable **nickname**.

An author consists of:

- `nickname`
- `first_name`
- `last_name`
- `email`

Authors are stored in `.mcodex/config.yaml` for convenience,  
but **copied into `metadata.yaml`** when a text is created.

This guarantees reproducibility.

---

## Current capabilities

At the current stage, mcodex supports:

- initializing a repository (`mcodex init`)
- registering authors (repo-scoped)
- creating new texts
- attaching authors to texts
- creating labeled snapshots
- freezing snapshots via Git commit + tag

Example workflow:

```bash
mcodex init

mcodex author add celestian "Jan" "Novák" jan.novak@example.com
mcodex author add eva "Eva Marie" "Svobodová" eva@example.com

mcodex create "Článek o něčem" \
  --author=celestian \
  --author=eva

cd clanek_o_necem
mcodex snapshot create draft --note "first draft sent to editor"
```

Result:

```text
clanek_o_necem/
├── text.md
├── metadata.yaml
└── .snapshot/
    └── draft-1/
        ├── text.md
        ├── metadata.yaml
        └── snapshot.yaml
```

Git tag:

```text
mcodex/clanek_o_necem/draft-1
```

---

## Installation (development)

mcodex is a Python CLI tool.

### Using uv (recommended for development)

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

Verify:

```bash
mcodex --help
```

---

## Project status

mcodex is in an **early but stabilized architectural phase**.

Current priorities:

- correctness
- explicit filesystem state
- reproducibility
- test isolation and safety

Features will be added incrementally, with a strong preference for:

- simple CLI commands
- transparent file formats
- minimal hidden state
