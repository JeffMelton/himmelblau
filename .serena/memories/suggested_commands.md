# Suggested Commands for Himmelblau Development

## Build Commands
- `cargo build --all-features --all-targets` - Build all targets with all features
- `cargo build` - Standard build
- `cargo build -p <package>` - Build specific package (e.g., `cargo build -p himmelblau_unix_common`)

## Testing Commands
- `cargo test` - Run all tests
- `cargo test -p <package>` - Run tests for specific package
- `make test` - Alternative test command via Makefile

## Linting and Code Quality
- `cargo clippy --all-features` - Run clippy linter with all features
- `cargo clippy` - Standard clippy run
- `cargo fmt` - Format code (uses rustfmt defaults)

## Packaging Commands
- `make` - Auto-detect host distro and build packages
- `make clean` - Remove cargo build artifacts
- `make install` - Install packages from ./packaging onto host
- `make uninstall` - Uninstall Himmelblau packages from host

## Development Utilities
- `cargo check` - Fast compilation check without producing binaries
- `cargo doc --open` - Generate and open documentation
- `cargo tree` - Show dependency tree
- `cargo update` - Update dependencies

## System Commands (Linux)
- `ls`, `cd`, `grep`, `find` - Standard Unix utilities
- `git` - Version control
- `systemctl` - Service management (for daemon)
- `journalctl` - View system logs

## Running Entrypoints
- Main daemon: Built as `himmelblaud` (requires root privileges)
- CLI tool: Built as `aad-tool` (in src/cli)
- Configuration file: `/etc/himmelblau/himmelblau.conf`