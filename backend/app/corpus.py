"""Load markdown docs and split them into chunks, one chunk per '## ' section."""
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Chunk:
    id: str        # e.g. "refund-policy#limited-drops"
    doc: str       # file name without extension
    title: str     # document title (the '# ' line)
    section: str   # section heading (the '## ' line)
    text: str      # the section body

    def for_search(self) -> str:
        # Prefix the title and heading so a chunk keeps its context when it is read alone.
        return f"{self.title} > {self.section}\n{self.text}"

    def to_dict(self) -> dict:
        return asdict(self)


def slug(s: str) -> str:
    return "-".join("".join(c.lower() if c.isalnum() else " " for c in s).split())


def load_chunks(docs_dir: Path) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(docs_dir.glob("*.md")):
        title, section, body = path.stem, "Overview", []

        def flush():
            text = "\n".join(body).strip()
            if text:
                chunks.append(Chunk(f"{path.stem}#{slug(section)}", path.stem, title, section, text))

        for line in path.read_text().splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
            elif line.startswith("## "):
                flush()
                section, body = line[3:].strip(), []
            else:
                body.append(line)
        flush()
    return chunks
