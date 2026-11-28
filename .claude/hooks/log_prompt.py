#!/usr/bin/env python3
"""Keep docs/prompt-history.md up to date with the prompts given to Claude Code.

As a UserPromptSubmit hook (see .claude/settings.json) it reads the hook's JSON
from stdin and appends the prompt. It never blocks a prompt: any error is
reported on stderr and the hook still exits 0.

    --backfill TRANSCRIPT.jsonl...   rebuild the file from Claude Code transcripts
                                     (~/.claude/projects/<project>/<session>.jsonl)

Standard library only, so it runs with any python3.
"""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]
HISTORY = PROJECT_DIR / "docs" / "prompt-history.md"
HEADER = """# Prompt history

Prompts given to Claude Code while building BakeMagic, oldest first. Times are local.

New prompts are appended automatically by `.claude/hooks/log_prompt.py`, a
`UserPromptSubmit` hook configured in `.claude/settings.json`.
"""

# Exact prompt texts to leave out of the history (whitespace-trimmed).
EXCLUDED: set[str] = set()


def entry(prompt: str, when: datetime, session_id: str) -> str:
    stamp = when.astimezone().strftime("%Y-%m-%d %H:%M %Z")
    quoted = "\n".join(f"> {line}" if line else ">" for line in prompt.strip().splitlines())
    return f"\n### {stamp} · session `{session_id[:8]}`\n\n{quoted}\n"


def is_real_prompt(text: str) -> bool:
    """Skip interruptions, harness notices (task notifications, system tags) and EXCLUDED."""
    text = text.strip()
    return (
        bool(text)
        and not text.startswith(("[Request interrupted", "<"))
        and text not in EXCLUDED
    )


def append(prompt: str, when: datetime, session_id: str) -> None:
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    if not HISTORY.exists():
        HISTORY.write_text(HEADER)
    with HISTORY.open("a") as f:
        f.write(entry(prompt, when, session_id))


def active_path(records: list[dict]) -> set[str]:
    """Uuids on the conversation as it stands: from the newest record back to the start.

    A transcript is a tree; editing and resending a message leaves the abandoned
    branch in the file, and those prompts shouldn't be listed.
    """
    by_uuid = {r["uuid"]: r for r in records if "uuid" in r}
    main = [r for r in records if "uuid" in r and not r.get("isSidechain")]
    path, uuid = set(), main[-1]["uuid"] if main else None
    while uuid and uuid not in path:
        path.add(uuid)
        uuid = by_uuid.get(uuid, {}).get("parentUuid")
    return path


def prompts_from_transcript(path: Path):
    """(timestamp, session id, text) for each prompt the user typed in a transcript."""
    records = [json.loads(line) for line in path.open()]
    on_path = active_path(records)
    for record in records:
        if record.get("type") != "user" or record.get("isMeta") or record.get("isSidechain"):
            continue
        if record.get("uuid") not in on_path:
            continue
        content = record.get("message", {}).get("content")
        if isinstance(content, list):  # tool results have no text parts
            content = "\n".join(p.get("text", "") for p in content if p.get("type") == "text")
        if not isinstance(content, str) or not is_real_prompt(content):
            continue
        when = datetime.fromisoformat(record["timestamp"].replace("Z", "+00:00"))
        yield when, record.get("sessionId", path.stem), content


def backfill(transcripts: list[str]) -> None:
    prompts = sorted(p for t in transcripts for p in prompts_from_transcript(Path(t)))
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    HISTORY.write_text(HEADER + "".join(entry(text, when, sid) for when, sid, text in prompts))
    print(f"Wrote {len(prompts)} prompts to {HISTORY.relative_to(PROJECT_DIR)}")


def hook() -> None:
    payload = json.load(sys.stdin)
    prompt = payload.get("prompt", "")
    if is_real_prompt(prompt):
        append(prompt, datetime.now(UTC), payload.get("session_id", "unknown"))


if __name__ == "__main__":
    if sys.argv[1:2] == ["--backfill"]:
        backfill(sys.argv[2:])
    else:
        try:
            hook()
        except Exception as exc:  # never block the user's prompt over logging
            print(f"log_prompt: {exc}", file=sys.stderr)
