# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Himmelblau is an interoperability suite for Microsoft Azure Entra ID and Intune on Linux systems. It provides Linux authentication to Azure Entra ID via PAM/NSS modules and supports Intune device enrollment and policy enforcement.

## Build System

This is a Rust workspace project with 19 crates organized under `src/`. The minimum Rust version is 1.70.

### Essential Build Commands

- `cargo build` - Standard build for development
- `cargo build --all-features --all-targets` - Full build with all features
- `cargo build -p <package>` - Build specific crate (e.g., `cargo build -p himmelblau_unix_common`)
- `make` - Auto-detect host distro and build platform packages
- `make test` - Alternative test runner via Makefile

### Testing

- `cargo test` - Run all tests
- `cargo test -p <package>` - Test specific crate
- `cargo clippy --all-features` - Linting with all features
- `cargo fmt` - Code formatting

### Package Management

- `make clean` - Remove cargo build artifacts  
- `make install` - Install packages from ./packaging onto host
- `make uninstall` - Remove Himmelblau packages from host

## Architecture

### Core Components

- **daemon** (`himmelblaud`) - Main authentication daemon, requires root privileges
- **cli** (`aad-tool`) - Command-line administration tool
- **common** (`himmelblau_unix_common`) - Shared functionality across crates
- **pam** - PAM module for system authentication
- **nss** - NSS module for user/group resolution

### Key Supporting Components

- **broker** - D-Bus broker service with client library in `broker-client`
- **crypto** - Cryptographic utilities and TPM integration
- **policies** - Intune policy management  
- **proto** - Protocol definitions and serialization
- **sketching** - Logging and tracing utilities

### System Integration Components

- **sso** - Single Sign-On functionality
- **qr-greeter** - QR code authentication UI
- **selinux** - SELinux policy integration
- **o365** - Office 365 integration

### Utility Crates

- **idmap** - ID mapping functionality
- **users** - User management utilities
- **file_permissions** - File permission utilities
- **sshd-config** - SSH daemon configuration

## Configuration

- Main configuration: `/etc/himmelblau/himmelblau.conf`
- Platform-specific configs in `platform/` directory
- The daemon communicates via Unix sockets for IPC

## Key Dependencies

- **Tokio** - Async runtime with multi-threading support
- **SQLite** - Database backend via `rusqlite`
- **TPM integration** - Via `tss-esapi` for secure key storage
- **Tracing** - Comprehensive logging framework
- **D-Bus** - System service communication
- **Cryptography** - OpenSSL and custom crypto libraries

## Development Notes

- All crates share workspace-level dependencies defined in root `Cargo.toml`
- Version is currently 2.0.0 across all workspace members
- License: GPL-3.0-or-later
- Minimum Rust version: 1.70 (specified in workspace.package)
- The project uses Cargo workspace resolver version 2

## Platform Support

Targets multiple Linux distributions with distribution-specific packaging in the `platform/` directory and automated package building via Makefile.