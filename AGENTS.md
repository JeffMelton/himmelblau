Agent Working Guide (Rust)

Scope
- This file lives at the repo root and applies to the entire repository, unless a more specific AGENTS.md exists in a subdirectory. Deeper AGENTS.md files take precedence.

Goals
- Keep changes minimal, focused, and idiomatic for Rust.
- Fix root causes; avoid band‑aid fixes and unrelated edits.
- Preserve public APIs and behavior unless the task explicitly requires change.

Code Style
- Use `rustfmt` conventions. When in doubt, run `cargo fmt` locally.
- Keep code clear and readable; avoid one‑letter variable names.
- Prefer small, well‑named functions over deeply nested logic.
- Follow existing module and file organization under `src/`.
- Avoid adding new dependencies unless necessary and justified.

Quality
- Prefer `clippy`-friendly code. Check locally with `cargo clippy` if available.
- Add/adjust tests only when the task requires it; keep tests focused and fast.
- Don’t change or add unrelated tests.

Build & Test
- Build: `cargo build` (use the `Makefile` targets if present and appropriate).
- Test: `cargo test` for the subset you touched, then the whole suite if time allows.
- If features or examples exist, preserve their behavior. Update docs/help text if you alter CLI arguments or output formats.

Editing Workflow (for agents)
- Use `apply_patch` for all file edits. Keep diffs surgical.
- Avoid renames or file moves unless necessary for the task.
- Prefer `rg` for repository searches; read files in small chunks when inspecting.
- Do not commit or create branches unless explicitly requested in the task.

Documentation
- Update `README.md`, `man/`, or in‑code docs when behavior or usage changes.
- Keep comments concise and purposeful; avoid noisy inline commentary.

Security & Safety
- Avoid introducing unsafe code. If `unsafe` is required, justify and minimize it.
- Validate inputs and handle errors explicitly. Prefer `Result`-based flows over panics.

When Unsure
- Mirror existing patterns in this codebase.
- Ask for confirmation before large refactors or dependency changes.

