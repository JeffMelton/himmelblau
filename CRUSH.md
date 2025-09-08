# Himmelblau Development Guide

## Build Commands
- `cargo build --all-features --all-targets` - Build all targets with all features
- `cargo test` - Run all tests
- `cargo test -p <package>` - Run tests for specific package (e.g., `cargo test -p himmelblau_unix_common`)
- `cargo clippy --all-features` - Run clippy linter
- `make` - Auto-detect host distro and build packages
- `make test` - Run cargo tests
- `make clean` - Remove cargo build artifacts

## Code Style Guidelines
- **Error Handling**: Use `Result<T, E>` types, avoid `unwrap()`, `expect()`, `panic!()`, `todo!()`, `unimplemented!()`
- **Imports**: Group std imports first, then external crates, then local modules
- **Naming**: Use snake_case for functions/variables, PascalCase for types, SCREAMING_SNAKE_CASE for constants
- **Types**: Prefer explicit types, use `async/await` for async code, leverage `tokio` runtime
- **Formatting**: Use `rustfmt` defaults, max 9 function arguments (clippy config)
- **Logging**: Use `tracing` macros (`trace!`, `debug!`, `info!`, `warn!`, `error!`)
- **Comments**: Avoid unnecessary comments, use doc comments for public APIs
- **Clippy**: Follow all clippy lints, see `clippy.toml` for custom thresholds

## Architecture Notes
- Workspace with 22 crates in `src/` directory
- Main daemon in `src/daemon`, CLI tools in `src/cli`
- Common functionality in `src/common` (himmelblau_unix_common)
- Uses tokio async runtime, Unix sockets for IPC
- Database layer with SQLite backend
- TPM integration for secure key storage
- PAM/NSS modules for system integration