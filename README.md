# Lightweight Git

A small, educational, **lightweight Python implementation** of essential Git internals: objects (blobs, trees, commits), repository initialization, a simple `clone` that downloads a packfile, and a few plumbing commands.
This project is intended as a learning tool to demonstrate **how Git stores objects, writes trees, and creates commits**, not as a production replacement for `git`.

---

## Features

* Initialize a minimal `.git` directory (`init`)
* Hash and store blobs (`hash-object -w <file>`)
* Read stored objects (`cat-file -p <hash>`)
* Create tree objects from a working directory (`write-tree`)
* List tree contents (`ls-tree <tree-hash>` / `ls-tree --name-only <tree-hash>`)
* Create commit objects that reference a tree (and optional parent) (`commit-tree`)
* Lightweight HTTP `clone` implementation that fetches refs, downloads a packfile, writes objects to `.git/objects`, and renders the default tree into the working directory

**Implementation notes:** Uses only Python standard libraries (`os`, `zlib`, `hashlib`, `time`, `urllib.request`, `struct`, `urllib.parse`, etc.). Objects are stored under `.git/objects/` in the same layout as upstream Git.

---

## Installation

This is a small script/package. You can use it in one of two ways:

1. Run the script/module directly from the repository folder:

   ```bash
   python path/to/main.py <command> [args...]
   ```

2. Install as a package (recommended if you add packaging and entry points) and then run:

   ```bash
   python -m <your_package> <command> [args...]
   ```

*Tip: Add a simple `console_scripts` entrypoint or a small wrapper script if you want `mygit` on your `$PATH`.*

---

## Usage / CLI Reference

The program accepts a first positional argument (the command) followed by command-specific arguments.

```bash
python main.py <command> [args...]
```

### `init`

Create a minimal `.git` directory.

```bash
python main.py init
# -> "Initialized git directory"
```

Creates:

* `.git/objects/`
* `.git/refs/`
* `.git/HEAD` (points to `refs/heads/main`)

---

### `hash-object -w <path>`

Hash a file as a blob and write it into `.git/objects/`. Prints the object SHA.

```bash
python main.py hash-object -w README.md
# -> prints SHA1 hash
```

---

### `cat-file -p <hash>`

Read an object from `.git/objects/`, decompress, and pretty-print its content.

```bash
python main.py cat-file -p <sha1>
```

---

### `write-tree`

Walk the current directory (ignores `.git`) and write tree objects recursively. Prints the resulting tree hash.

```bash
python main.py write-tree
# -> prints tree SHA
```

---

### `ls-tree [--name-only] <tree-hash>`

List entries of a tree object.

* `ls-tree <tree-hash>` → prints `mode type sha\tname` lines (sorted).
* `ls-tree --name-only <tree-hash>` → prints only file/directory names.

```bash
python main.py ls-tree <tree-hash>
python main.py ls-tree --name-only <tree-hash>
```

*Note: The implementation expects `--name-only` before the hash.*

---

### `commit-tree <tree-hash> [-p <parent-hash>] [-m <message>]`

Create a commit object referencing `tree-hash`. Optional parent and commit message. Prints the commit SHA.

Examples:

```bash
# Simple commit with message
python main.py commit-tree <tree-sha> -m "Initial commit"

# Commit with parent
python main.py commit-tree <tree-sha> -p <parent-sha> -m "Fix"
```

Commit object format:

```
tree <tree-sha>
parent <parent-sha>    # optional
author You <you@example.com> <timestamp> <tz>
committer You <you@example.com> <timestamp> <tz>

<message>
```

---

### `clone <remote-url> [local-dir]`

A small HTTP-based clone that:

1. Queries `<remote-url>/info/refs?service=git-upload-pack`
2. Requests `<remote-url>/git-upload-pack` to obtain a packfile
3. Processes the packfile (supports commit/tree/blob and ref-deltas), writes objects into `.git/objects/`
4. Writes `.git/HEAD` and default branch ref
5. Renders the default tree into the working directory

Example:

```bash
python main.py clone https://example.com/some-repo.git
python main.py clone https://example.com/some-repo.git my-local-dir
```

---

## Repository Layout

What the code creates:

```
.git/
  objects/   # two-letter dirs with zlib-compressed object files
  refs/      # branch refs (writes default branch file)
  HEAD       # text ref: refs/heads/main or branch ref
```

Objects are stored like Git: compressed zlib blobs with header `b"<type> <len>\0" + content`.

---

## Design & Implementation Notes

* **Objects:** `hashObject` / `hashObjectFile` create blobs; `writeTree` builds trees; `commitTree` builds commits.
* **Object format:** stored as header + content (compressed). SHA computed over raw header+content (before compression).
* **Packfiles (clone):** parses upload-pack, decodes packfile, applies `ref_delta`s, writes objects to `.git/objects/`.
* **Rendering:** `renderTree` reads a tree and writes files/dirs into the working directory.

---

## Limitations & Safety

* **Not a Git replacement** — educational only.
* Missing features: reflogs, index, branches, GC, pruning.
* Minimal argument parsing (position-sensitive for `commit-tree` and `ls-tree`).
* Clone supports only anonymous HTTP (no auth).
* Clone writes files to disk (may overwrite existing files). Use a new directory.

---

## Troubleshooting

* **`FileNotFoundError` for `.git/objects/...`** → Run `init` or `clone` first.
* **`hash-object`** → Use `-w` flag.
* **`commit-tree`** → Arguments must be in correct order.
