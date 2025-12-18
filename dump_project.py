import os
from pathlib import Path

# ===== CONFIG =====

OUTPUT_FILE = "PROJECT_DUMP.txt"

# Pastas ignoradas automaticamente
DEFAULT_IGNORES = {
    ".git",
    ".venv",
    "__pycache__",
    ".idea",
    ".vscode",
    "node_modules",
    "dist",
    "build",
    ".pytest_cache",
    ".mypy_cache",
}

# Arquivos ignorados automaticamente
DEFAULT_IGNORE_FILES = {
    OUTPUT_FILE,
    ".DS_Store",
    "tailwind.min.css"
}


def load_ignorelist():
    """Carrega padrões adicionais de um .ignorelist se existir."""
    ignore_file = Path(".ignorelist")
    if not ignore_file.exists():
        return set()

    with ignore_file.open("r", encoding="utf-8") as f:
        return {
            line.strip()
            for line in f.readlines()
            if line.strip() and not line.startswith("#")
        }


def is_binary(filepath: Path) -> bool:
    """Detecta grosseiramente se é arquivo binário."""
    try:
        with filepath.open("rb") as f:
            chunk = f.read(1024)
            return b"\x00" in chunk
    except:
        return True


def should_ignore(path: Path, ignorelist):
    for part in path.parts:
        if part in DEFAULT_IGNORES or part in ignorelist:
            return True

    if path.name in DEFAULT_IGNORE_FILES:
        return True

    return False


def collect_files(root: Path, ignorelist):
    files = []
    for item in root.rglob("*"):
        if not item.is_file():
            continue

        if should_ignore(item, ignorelist):
            continue

        if is_binary(item):
            continue

        files.append(item)

    return sorted(files)


def write_tree(file, files, root):
    file.write("==== PROJECT TREE ====\n\n")
    for f in files:
        file.write(str(f.relative_to(root)) + "\n")
    file.write("\n\n")


def dump_contents(file, files, root):
    file.write("==== FILE CONTENTS ====\n\n")
    for f in files:
        rel = f.relative_to(root)
        file.write(f"\n\n{'=' * 90}\n")
        file.write(f"FILE: {rel}\n")
        file.write(f"{'=' * 90}\n\n")
        try:
            file.write(f.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            file.write("[ERROR: Arquivo não pode ser decodificado como UTF-8]")


def main():
    root = Path.cwd()
    ignorelist = load_ignorelist()

    files = collect_files(root, ignorelist)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        write_tree(out, files, root)
        dump_contents(out, files, root)

    print(f"\n✅ Projeto exportado com sucesso!")
    print(f"📄 Arquivo gerado: {OUTPUT_FILE}")
    print(f"📦 Arquivos incluídos: {len(files)}")


if __name__ == "__main__":
    main()
