# mcodex templates

This directory contains project-local templates used by mcodex.

mcodex copies these files from its built-in defaults when you run:

```bash
mcodex init
```

## Structure

```text
.mcodex/templates/
├── pandoc/
│   ├── reference.docx
│   └── template.tex
├── latex/
│   └── main.tex
└── text/
    ├── todo.md
    ├── checklist.md
    └── README.txt
```

## Editing templates

You are expected to edit these files in your repository.

- Change `pandoc/reference.docx` to control DOCX styling.
- Change `pandoc/template.tex` to control the PDF build that uses Pandoc
  directly.
- Change `latex/main.tex` (and add more `.sty` files as needed) to control the
  LaTeX-based PDF build.

## Re-running init

Running `mcodex init` again is safe and does **not** overwrite existing template
files. It only adds missing files.

If you want to overwrite existing templates with the built-in defaults, use:

```bash
mcodex init --force
```
