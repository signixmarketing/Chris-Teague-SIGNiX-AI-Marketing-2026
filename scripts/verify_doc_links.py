#!/usr/bin/env python3
"""
Verify that every markdown link [text](path) in PROJECT-DOCS resolves to an existing file.
Path is relative to the file containing the link. Run from repo root.
"""
import os
import re

PROJECT_DOCS = "PROJECT-DOCS"

def main():
    errors = []
    link_re = re.compile(r'\[([^\]]*)\]\(([^)]+)\)')
    for root, _dirs, files in os.walk(PROJECT_DOCS):
        for f in files:
            if not f.endswith('.md'):
                continue
            path = os.path.join(root, f)
            file_dir = os.path.dirname(path)
            with open(path, 'r', encoding='utf-8') as fp:
                content = fp.read()
            for m in link_re.finditer(content):
                link_text, link_path = m.group(1), m.group(2)
                if link_path.startswith('http://') or link_path.startswith('https://') or link_path.startswith('#'):
                    continue
                resolved = os.path.normpath(os.path.join(file_dir, link_path))
                if not os.path.isfile(resolved):
                    rel_path = os.path.relpath(path, PROJECT_DOCS)
                    errors.append((rel_path, link_path, resolved))
    if errors:
        print("Broken links:")
        for rel_path, link_path, resolved in errors:
            print(f"  In {rel_path}: [{link_path}] -> {resolved}")
        return 1
    print("All links resolve.")
    return 0

if __name__ == "__main__":
    exit(main())
