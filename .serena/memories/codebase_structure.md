# Codebase Structure

## Top-Level Organization
```
himmelblau/
├── src/                    # All Rust crates (22 total)
├── man/                    # Manual pages
├── platform/               # Platform-specific configs (debian, opensuse, el)
├── scripts/                # Build and utility scripts
├── images/                 # Docker build files
├── .github/                # GitHub workflows and templates
├── Cargo.toml              # Workspace configuration
├── Makefile                # Packaging and build automation
├── clippy.toml             # Clippy configuration
└── flake.nix               # Nix package definition
```

## Core Crates in src/
- **daemon/**: Main `himmelblaud` daemon - handles authentication requests
- **cli/**: Command-line tool `aad-tool` for administration
- **common/**: Shared functionality (`himmelblau_unix_common`)
- **pam/**: PAM module for system authentication
- **nss/**: NSS module for user/group resolution
- **broker/**: D-Bus broker service
- **crypto/**: Cryptographic utilities and TPM integration
- **proto/**: Protocol definitions and serialization
- **policies/**: Intune policy management
- **sketching/**: Logging and tracing utilities

## Supporting Crates
- **broker-client/**: Client library for broker communication
- **file_permissions/**: File permission utilities
- **idmap/**: ID mapping functionality
- **o365/**: Office 365 integration
- **qr-greeter/**: QR code authentication UI
- **selinux/**: SELinux policy integration
- **sshd-config/**: SSH daemon configuration
- **sso/**: Single Sign-On components
- **users/**: User management utilities

## Key Files
- **Cargo.lock**: Dependency lock file
- **CRUSH.md**: Development guide (created by this analysis)
- **README.md**: Project documentation and installation guide
- **CONTRIBUTING.md**: Contribution guidelines
- **LICENSE**: GPL-3.0-or-later license

## Configuration
- Main config: `/etc/himmelblau/himmelblau.conf`
- Platform configs in `platform/` directory
- Example configs in `src/config/`