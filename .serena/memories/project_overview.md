# Himmelblau Project Overview

## Purpose
Himmelblau is an interoperability suite for Microsoft Azure Entra ID and Intune on Linux systems. The name comes from the German word for Azure (sky blue). The project enables:

- Linux authentication to Microsoft Azure Entra ID via PAM and NSS modules
- Intune device enrollment and policy enforcement
- Device compliance marking with Intune MDM policies
- Single Sign-On (SSO) capabilities

## Primary Sponsor
SUSE is the primary sponsor and maintainer of the project, with community funding for operating expenses.

## Tech Stack
- **Language**: Rust (minimum version 1.70)
- **Async Runtime**: Tokio
- **Database**: SQLite backend
- **Security**: TPM integration for secure key storage
- **IPC**: Unix sockets for inter-process communication
- **System Integration**: PAM/NSS modules
- **Logging**: Tracing framework
- **Build System**: Cargo workspace + Makefile for packaging

## Architecture
- Cargo workspace with 22 crates in `src/` directory
- Main daemon (`himmelblaud`) in `src/daemon`
- CLI tools in `src/cli`
- Common functionality in `src/common` (himmelblau_unix_common)
- PAM module in `src/pam`
- NSS module in `src/nss`
- Policy management in `src/policies`
- Crypto utilities in `src/crypto`
- Additional components: broker, SSO, QR greeter, SELinux integration

## Distribution Support
Available for multiple Linux distributions: openSUSE, SUSE Linux Enterprise, Fedora, Ubuntu, Debian, Red Hat Enterprise Linux (Rocky), and NixOS.