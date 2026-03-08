#!/usr/bin/env python3
"""
Convert every file reference in PROJECT-DOCS .md files to a markdown link
[display](relative_path) so readers can click through. Paths are relative to
the file containing the reference. Run from repo root.
"""
import os
import re

PROJECT_DOCS = "PROJECT-DOCS"


def collect_doc_paths():
    """All .md paths relative to PROJECT_DOCS (with forward slashes)."""
    paths = []
    for root, _dirs, files in os.walk(PROJECT_DOCS):
        for f in files:
            if not f.endswith(".md"):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, PROJECT_DOCS).replace("\\", "/")
            paths.append(rel)
    return sorted(paths, key=len, reverse=True)  # longest first to avoid partial matches


def ref_to_link(content, target_path, rel_from_current, current_dir):
    """Replace references to target_path with [display](rel_from_current).
    Avoids replacing inside existing links (](path) or ](../path)).
    """
    display = target_path
    escaped = re.escape(target_path)
    # Replace **../path** and **path** first (bold reference)
    for prefix in (r"\*\*\.\./", r"\*\*"):
        bold_pattern = prefix + escaped + r"\*\*"
        bold_repl = "[" + display + "](" + rel_from_current + ")"
        content = re.sub(bold_pattern, bold_repl, content)
    # Replace ../path (plain) when not inside existing link
    prefix_escaped = r"\.\./" + escaped
    plain_prefix_pattern = r"(?<!\]\()(?<!\()\b" + re.escape("../" + target_path) + r"\b(?!\))"
    content = re.sub(plain_prefix_pattern, "[" + display + "](" + rel_from_current + ")", content)
    # Replace plain path when not already part of ](url)
    plain_pattern = r"(?<!\]\()(?<!\()\b" + escaped + r"\b(?!\))"
    plain_repl = "[" + display + "](" + rel_from_current + ")"
    content = re.sub(plain_pattern, plain_repl, content)
    return content


def main():
    doc_paths = collect_doc_paths()
    # Basenames that uniquely identify a doc (for same-folder refs)
    from collections import Counter
    basenames = [os.path.basename(p) for p in doc_paths]
    unique_basename_to_path = {b: p for p in doc_paths for b in [os.path.basename(p)] if basenames.count(b) == 1}
    for root, _dirs, files in os.walk(PROJECT_DOCS):
        for f in files:
            if not f.endswith(".md"):
                continue
            path = os.path.join(root, f)
            current_rel = os.path.relpath(path, PROJECT_DOCS).replace("\\", "/")
            current_dir = os.path.dirname(current_rel)
            if current_dir == ".":
                current_dir = ""
            with open(path, "r", encoding="utf-8") as fp:
                content = fp.read()
            original = content
            for target_path in doc_paths:
                if target_path == current_rel:
                    continue
                if current_dir:
                    rel_from_current = os.path.relpath(
                        os.path.join(PROJECT_DOCS, target_path),
                        os.path.join(PROJECT_DOCS, current_dir),
                    ).replace("\\", "/")
                else:
                    rel_from_current = target_path
                content = ref_to_link(content, target_path, rel_from_current, current_dir)
            for basename, full_path in unique_basename_to_path.items():
                if full_path == current_rel:
                    continue
                if current_dir:
                    rel_from_current = os.path.relpath(
                        os.path.join(PROJECT_DOCS, full_path),
                        os.path.join(PROJECT_DOCS, current_dir),
                    ).replace("\\", "/")
                else:
                    rel_from_current = full_path
                escaped = re.escape(basename)
                for prefix in (r"\*\*",):
                    bold_pattern = prefix + escaped + r"\*\*"
                    content = re.sub(bold_pattern, "[" + basename + "](" + rel_from_current + ")", content)
                plain_pattern = r"(?<!\[)(?<!\]\()(?<!\()\b" + escaped + r"\b(?!\))"
                content = re.sub(plain_pattern, "[" + basename + "](" + rel_from_current + ")", content)
            if content != original:
                with open(path, "w", encoding="utf-8") as fp:
                    fp.write(content)
                print(f"Updated: {path}")


if __name__ == "__main__":
    main()
