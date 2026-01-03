#!/usr/bin/env bash
set -euo pipefail

COMMAND="${1:-}"

usage() {
    echo "Usage:"
    echo "  ./tool-box.sh check   Run ruff, mypy, pytest (via uv)"
    echo "  ./tool-box.sh sc      Create staged_commit.txt (staged files + diff + template)"
    echo "  ./tool-box.sh pr [base-ref]"
    echo "                        Create pull_request.txt (new commits above base-ref,"
    echo "                        default origin/main)"
    echo "  ./tool-box.sh src     Create mcodex.tar.gz (for discussion with ChatGPT)"
}

require_cmd() {
    local cmd="$1"
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "❌ Missing required command: $cmd"
        exit 127
    fi
}

if [[ -z "$COMMAND" ]]; then
    usage
    exit 1
fi

require_cmd uv
require_cmd git
require_cmd tar

case "$COMMAND" in
    check)
        echo "🔧 Syncing dependencies (including dev extras)..."
        uv sync --extra dev

        echo "🎨 Running ruff format..."
        uv run --extra dev ruff format .

        echo "🔍 Running ruff check..."
        uv run --extra dev ruff check .

        echo "🧠 Running mypy..."
        uv run --extra dev mypy mcodex

        echo "🧪 Running pytest..."
        uv run --extra dev python -m pytest

        echo "✅ All checks passed!"
        ;;

    sc)
        OUT_FILE="staged_commit.txt"

        git diff --cached --name-only > "${OUT_FILE}"
        printf "\n--- FULL DIFF (STAGED) ---\n\n" >> "${OUT_FILE}"
        git diff --cached >> "${OUT_FILE}"
        printf "\n\n--- COMMIT TEMPLATE ---\n\n" >> "${OUT_FILE}"
        cat .git-commit-template >> "${OUT_FILE}"

        echo "✅ ${OUT_FILE} successfully created."
        ;;

    pr)
        BASE_REF="${2:-origin/main}"

        (
            echo "## Commits"
            echo
            git log --oneline "${BASE_REF}"..HEAD
            echo
            echo "## Diff"
            echo
            git diff "${BASE_REF}"...HEAD
        ) > pull_request.txt

        echo "✅ pull_request.txt successfully created (base: ${BASE_REF})."
        ;;

    src)
        tar --exclude-vcs \
            --exclude='.venv' \
            --exclude='.ruff_cache' \
            --exclude='.mypy_cache' \
            --exclude='__pycache__' \
            --exclude='*.pyc' \
            --exclude='*.pyo' \
            -czf mcodex.tar.gz \
                mcodex/ \
                tests/ \
                README.md \
                tool-box.sh \
                pyproject.toml \
                uv.lock \
                .gitignore

        echo "✅ mcodex.tar.gz package successfully created."
        ;;

    *)
        echo "❌ Unknown command: ${COMMAND}"
        usage
        exit 1
        ;;
esac

