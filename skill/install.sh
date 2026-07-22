#!/usr/bin/env bash
# ANAPANA Skills installer — copies (or symlinks) the five bare skills into an
# agent's skills directory. Pure instruction skills: no code runs, no deps.
#
# Usage:
#   ./install.sh claude          # -> ~/.claude/skills/
#   ./install.sh codex           # -> ~/.agents/skills/
#   ./install.sh both            # both of the above
#   ./install.sh <target> --link # symlink instead of copy (live edits propagate)
#
# Folder names must match each SKILL.md `name:` field, so we never rename them.

set -euo pipefail

SKILLS=(satori crucible whetstone touchstone lianxi)
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

TARGET="${1:-}"
MODE="copy"
if [[ "${2:-}" == "--link" ]]; then
  MODE="link"
fi

if [[ -z "$TARGET" ]]; then
  echo "Usage: ./install.sh {claude|codex|both} [--link]" >&2
  exit 1
fi

install_into() {
  local dest_root="$1"
  mkdir -p "$dest_root"
  for skill in "${SKILLS[@]}"; do
    local src="$SRC_DIR/$skill"
    local dest="$dest_root/$skill"
    if [[ ! -f "$src/SKILL.md" ]]; then
      echo "  ! missing $src/SKILL.md — skipping" >&2
      continue
    fi
    rm -rf "$dest"
    if [[ "$MODE" == "link" ]]; then
      ln -s "$src" "$dest"
      echo "  linked  $skill -> $dest"
    else
      cp -R "$src" "$dest"
      echo "  copied  $skill -> $dest"
    fi
  done
}

do_claude() {
  echo "Installing ANAPANA skills into Claude Code (~/.claude/skills):"
  install_into "$HOME/.claude/skills"
}

do_codex() {
  echo "Installing ANAPANA skills into Codex (~/.agents/skills):"
  install_into "$HOME/.agents/skills"
}

case "$TARGET" in
  claude) do_claude ;;
  codex)  do_codex ;;
  both)   do_claude; echo; do_codex ;;
  *) echo "Unknown target '$TARGET' (use claude|codex|both)" >&2; exit 1 ;;
esac

echo
echo "Done. Restart Codex if it was running; Claude Code picks up new skills live."
echo "Verify with: \"What skills are available?\" or /satori /crucible /whetstone /touchstone /lianxi"
