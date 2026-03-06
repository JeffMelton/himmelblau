#!/usr/bin/env python3
"""
Himmelblau AUR PKGBUILD + .SRCINFO generator

Reads workspace Cargo.toml for version metadata, then writes a ready-to-push
packaging/aur/PKGBUILD and packaging/aur/.SRCINFO.

Usage:
  # Update with explicit version and pre-computed checksum:
  python3 scripts/gen_pkgbuild.py --version 4.1.0 --sha256 <hex>

  # Fetch checksum automatically from the GitHub release tarball:
  python3 scripts/gen_pkgbuild.py --version 4.1.0 --fetch-sha256

  # Use the version already in Cargo.toml (and fetch checksum):
  python3 scripts/gen_pkgbuild.py --fetch-sha256

  # During pre-release / fork validation, override the repo used for the
  # tarball fetch (the PKGBUILD source= URL still points to the upstream
  # defined in Cargo.toml, but the SHA-256 can be seeded from your fork):
  python3 scripts/gen_pkgbuild.py --fetch-sha256 \\
      --upstream-repo https://github.com/MyFork/himmelblau

  # Skip checksum verification while a release is still being prepared:
  python3 scripts/gen_pkgbuild.py --sha256 SKIP

  # Override output directory (default: ./packaging/aur/):
  python3 scripts/gen_pkgbuild.py --version 4.1.0 --sha256 <hex> --out ./out/
"""

import argparse
import hashlib
import os
import urllib.error
import urllib.request
from pathlib import Path

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib          # type: ignore[no-redef]
    except ImportError:
        tomllib = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Package metadata
# ---------------------------------------------------------------------------

ARCH_DEPENDS = [
    "dbus",
    "krb5",
    "libcap",
    "openssl",
    "pam",
    "sqlite",
    "systemd",
    "systemd-libs",
]

ARCH_OPTDEPENDS = [
    "tpm2-tss: TPM 2.0 hardware security module support",
    "openssh: SSH certificate authentication",
]

ARCH_MAKEDEPENDS = [
    "cargo",
    "clang",
    "cmake",
    "libunistring",
    "pcre2",
    "pkgconf",
    "python",
]

ARCH_PROVIDES = [
    "aad-cli",
    "authd-msentraid",
    "linux-entra-sso",
    "intune-portal",
]

BACKUP_FILES = [
    "etc/himmelblau/himmelblau.conf",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_workspace_metadata(repo_root: Path) -> dict:
    """Return version / license / homepage from the workspace Cargo.toml."""
    cargo_toml = repo_root / "Cargo.toml"
    if tomllib is None:
        raise RuntimeError(
            "tomllib / tomli not available — install tomli for Python < 3.11"
        )
    with cargo_toml.open("rb") as fh:
        data = tomllib.load(fh)
    workspace_pkg = data.get("workspace", {}).get("package", {})
    return {
        "version": workspace_pkg.get("version", "0.0.0"),
        "license": workspace_pkg.get("license", "GPL-3.0-or-later"),
        "homepage": workspace_pkg.get(
            "homepage", "https://github.com/himmelblau-idm/himmelblau"
        ),
        "repository": workspace_pkg.get(
            "repository", "https://github.com/himmelblau-idm/himmelblau"
        ),
    }


def _download_sha256(url: str) -> str:
    """Download *url* and return its SHA-256 hex digest.

    Raises ``urllib.error.HTTPError`` on a non-2xx response.
    """
    req = urllib.request.Request(url, headers={"User-Agent": "gen_pkgbuild/1.0"})
    h = hashlib.sha256()
    with urllib.request.urlopen(req, timeout=120) as resp:
        while True:
            chunk = resp.read(1 << 16)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def fetch_sha256(repo_url: str, version: str) -> str:
    """Return the SHA-256 of the release tarball for *version* in *repo_url*.

    GitHub tags may be bare (``4.0.0``) or ``v``-prefixed (``v4.0.0``).
    Both variants are tried automatically.

    Raises ``SystemExit`` with a helpful message if neither URL resolves.
    """
    base = repo_url.rstrip("/").removesuffix(".git")
    candidates = [
        f"{base}/archive/refs/tags/{version}.tar.gz",
        f"{base}/archive/refs/tags/v{version}.tar.gz",
    ]
    for url in candidates:
        try:
            print(f"Fetching {url} …")
            return _download_sha256(url)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                print(f"  → not found (404), trying next …")
                continue
            # Surface non-404 HTTP errors immediately with a clear message
            raise SystemExit(
                f"\nError: HTTP {exc.code} fetching {url}\n"
                f"  {exc.reason}\n"
                "Check your network connection and repository permissions."
            ) from exc

    # Both candidates returned 404
    tried = "\n  ".join(candidates)
    raise SystemExit(
        f"\nError: no release tarball found for version {version!r}.\n"
        f"Tried:\n  {tried}\n\n"
        "The release may not be published yet on that repository.\n"
        "Options:\n"
        "  • Use --sha256 SKIP while the release is still being prepared.\n"
        "  • Use --upstream-repo <url> to fetch from a different repository\n"
        "    (e.g. your fork) for pre-release / validation purposes.\n"
        "  • Use --sha256 <hex> to supply a pre-computed checksum."
    )


def tarball_url(repo_url: str, version: str) -> str:
    """Return the GitHub archive tarball URL for *version*.

    Uses the bare version tag (no ``v`` prefix) because that is the convention
    used by this project.  The ``v``-prefix fallback is only used when
    *fetching* the tarball to compute a checksum.
    """
    # Normalise: strip trailing slash / .git
    base = repo_url.rstrip("/").removesuffix(".git")
    return f"{base}/archive/refs/tags/{version}.tar.gz"


# ---------------------------------------------------------------------------
# PKGBUILD template
# ---------------------------------------------------------------------------

PKGBUILD_TEMPLATE = """\
# Maintainer: David Mulder <dmulder@suse.com>
pkgname=himmelblau
pkgver={version}
pkgrel=1
pkgdesc="Entra ID / Azure AD authentication for Linux (PAM, NSS, broker, SSO)"
arch=('x86_64' 'aarch64')
url="{homepage}"
license=('{license}')
depends=(
{depends}
)
optdepends=(
{optdepends}
)
makedepends=(
{makedepends}
)
provides=({provides})
backup=({backup})
source=("${{pkgname}}-${{pkgver}}.tar.gz::{source_url}")
sha256sums=('{sha256sums}')

prepare() {{
    cd "${{pkgname}}-${{pkgver}}"
    export CARGO_HOME="${{srcdir}}/cargo-home"
    cargo fetch --locked --target "${{CARCH}}-unknown-linux-gnu"
}}

build() {{
    cd "${{pkgname}}-${{pkgver}}"
    export CARGO_HOME="${{srcdir}}/cargo-home"

    # Generate systemd unit files with directives appropriate for Arch Linux.
    # Arch ships systemd 254+ so we pin to 254 to get all modern directives
    # (TypeNotifyReload, DynamicUser, ProtectHostname, etc.) without
    # requiring a live systemd-detect-virt call inside the build environment.
    python3 scripts/gen_servicefiles.py --out-dir ./platform/opensuse/ --assume-version 254

    cargo build \\
        --release \\
        --frozen \\
        --target "${{CARCH}}-unknown-linux-gnu"
}}

package() {{
    cd "${{pkgname}}-${{pkgver}}"
    local _t="target/${{CARCH}}-unknown-linux-gnu/release"

    # ── Binaries ──────────────────────────────────────────────────────────────
    install -Dm755 "${{_t}}/aad-tool"          "${{pkgdir}}/usr/bin/aad-tool"
    install -Dm755 "${{_t}}/himmelblaud"        "${{pkgdir}}/usr/bin/himmelblaud"
    install -Dm755 "${{_t}}/himmelblaud_tasks"  "${{pkgdir}}/usr/bin/himmelblaud_tasks"
    install -Dm755 "${{_t}}/broker"             "${{pkgdir}}/usr/bin/himmelblau_broker"
    install -Dm755 "${{_t}}/linux-entra-sso"    "${{pkgdir}}/usr/bin/linux-entra-sso"

    # ── Init helper ───────────────────────────────────────────────────────────
    install -Dm755 src/daemon/scripts/himmelblau-init-hsm-pin \\
        "${{pkgdir}}/usr/libexec/himmelblau-init-hsm-pin"

    # ── NSS library ───────────────────────────────────────────────────────────
    install -Dm755 "${{_t}}/libnss_himmelblau.so" \\
        "${{pkgdir}}/usr/lib/libnss_himmelblau.so.2"

    # ── PAM module ────────────────────────────────────────────────────────────
    install -Dm755 "${{_t}}/libpam_himmelblau.so" \\
        "${{pkgdir}}/usr/lib/security/pam_himmelblau.so"

    # ── Systemd system units ──────────────────────────────────────────────────
    install -Dm644 platform/opensuse/himmelblaud.service \\
        "${{pkgdir}}/usr/lib/systemd/system/himmelblaud.service"
    install -Dm644 platform/opensuse/himmelblaud-tasks.service \\
        "${{pkgdir}}/usr/lib/systemd/system/himmelblaud-tasks.service"
    install -Dm644 platform/opensuse/himmelblau-hsm-pin-init.service \\
        "${{pkgdir}}/usr/lib/systemd/system/himmelblau-hsm-pin-init.service"
    install -Dm644 src/config/gdm3_service_override.conf \\
        "${{pkgdir}}/usr/lib/systemd/system/display-manager.service.d/himmelblau-gdm-override.conf"

    # ── Systemd user unit (broker) ────────────────────────────────────────────
    install -Dm644 platform/debian/himmelblau-broker.service \\
        "${{pkgdir}}/usr/lib/systemd/user/himmelblau-broker.service"

    # ── D-Bus activation service ──────────────────────────────────────────────
    install -Dm644 platform/opensuse/com.microsoft.identity.broker1.service \\
        "${{pkgdir}}/usr/share/dbus-1/services/com.microsoft.identity.broker1.service"

    # ── Configuration ─────────────────────────────────────────────────────────
    install -Dm644 src/config/himmelblau.conf.example \\
        "${{pkgdir}}/etc/himmelblau/himmelblau.conf"
    install -Dm644 src/config/krb5_himmelblau.conf \\
        "${{pkgdir}}/etc/krb5.conf.d/krb5_himmelblau.conf"

    # ── tmpfiles.d ────────────────────────────────────────────────────────────
    install -Dm644 src/daemon/src/himmelblaud.tmpfiles.conf \\
        "${{pkgdir}}/usr/lib/tmpfiles.d/himmelblaud.conf"
    install -Dm644 src/daemon/src/himmelblau-policies.tmpfiles.conf \\
        "${{pkgdir}}/usr/lib/tmpfiles.d/himmelblau-policies.conf"
    install -Dm644 src/nss/src/nss-himmelblau.tmpfiles.conf \\
        "${{pkgdir}}/usr/lib/tmpfiles.d/nss-himmelblau.conf"

    # ── Browser SSO (native messaging hosts) ──────────────────────────────────
    install -Dm644 src/sso/src/firefox/linux_entra_sso.json \\
        "${{pkgdir}}/usr/lib/mozilla/native-messaging-hosts/linux_entra_sso.json"
    install -Dm644 src/sso/src/chrome/linux_entra_sso.json \\
        "${{pkgdir}}/etc/opt/chrome/native-messaging-hosts/linux_entra_sso.json"
    install -Dm644 src/sso/src/chrome/linux_entra_sso.json \\
        "${{pkgdir}}/etc/chromium/native-messaging-hosts/linux_entra_sso.json"

    # ── Browser SSO policies ──────────────────────────────────────────────────
    install -Dm644 src/sso-policies/src/chrome/policies.json \\
        "${{pkgdir}}/etc/opt/chrome/policies/managed/himmelblau.json"
    install -Dm644 src/sso-policies/src/chrome/policies.json \\
        "${{pkgdir}}/etc/chromium/policies/managed/himmelblau.json"

    # ── Man pages ─────────────────────────────────────────────────────────────
    install -Dm644 man/man1/aad-tool.1         "${{pkgdir}}/usr/share/man/man1/aad-tool.1"
    install -Dm644 man/man5/himmelblau.conf.5  "${{pkgdir}}/usr/share/man/man5/himmelblau.conf.5"
    install -Dm644 man/man8/himmelblaud.8      "${{pkgdir}}/usr/share/man/man8/himmelblaud.8"
    install -Dm644 man/man8/himmelblaud_tasks.8 \\
        "${{pkgdir}}/usr/share/man/man8/himmelblaud_tasks.8"

    # ── Documentation ─────────────────────────────────────────────────────────
    install -Dm644 README.md \\
        "${{pkgdir}}/usr/share/doc/${{pkgname}}/README.md"
    install -Dm644 src/config/himmelblau.conf.example \\
        "${{pkgdir}}/usr/share/doc/${{pkgname}}/himmelblau.conf.example"
}}
"""


# ---------------------------------------------------------------------------
# .SRCINFO generation
# ---------------------------------------------------------------------------

def _lines(items: list, key: str) -> str:
    return "".join(f"\t{key} = {v}\n" for v in items)


def generate_srcinfo(
    version: str,
    pkgrel: str,
    homepage: str,
    license_id: str,
    sha256: str,
    source_url: str,
    source_name: str,
) -> str:
    """Return a .SRCINFO string matching makepkg --printsrcinfo output."""
    depends_lines   = _lines(ARCH_DEPENDS,     "depends")
    optdepends_lines = _lines(ARCH_OPTDEPENDS, "optdepends")
    makedepends_lines = _lines(ARCH_MAKEDEPENDS, "makedepends")
    provides_lines  = _lines(ARCH_PROVIDES,    "provides")
    backup_lines    = _lines(BACKUP_FILES,     "backup")
    arch_lines      = "\tarch = x86_64\n\tarch = aarch64\n"

    pkgbase_block = (
        "pkgbase = himmelblau\n"
        f"\tpkgdesc = Entra ID / Azure AD authentication for Linux (PAM, NSS, broker, SSO)\n"
        f"\tpkgver = {version}\n"
        f"\tpkgrel = {pkgrel}\n"
        f"\turl = {homepage}\n"
        f"{arch_lines}"
        f"\tlicense = {license_id}\n"
        f"{makedepends_lines}"
        f"{depends_lines}"
        f"{optdepends_lines}"
        f"{provides_lines}"
        f"{backup_lines}"
        f"\tsource = {source_name}::{source_url}\n"
        f"\tsha256sums = {sha256}\n"
    )

    pkgname_block = (
        "\npkgname = himmelblau\n"
    )

    return pkgbase_block + pkgname_block


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Generate AUR PKGBUILD and .SRCINFO for himmelblau"
    )
    ap.add_argument(
        "--version",
        default=None,
        help="Package version (default: read from Cargo.toml)",
    )
    ap.add_argument(
        "--pkgrel",
        default="1",
        help="pkgrel value (default: 1)",
    )
    ap.add_argument(
        "--sha256",
        default=None,
        help="SHA-256 checksum of the release tarball (hex string)",
    )
    ap.add_argument(
        "--fetch-sha256",
        action="store_true",
        help="Fetch the release tarball and compute its SHA-256 automatically",
    )
    ap.add_argument(
        "--upstream-repo",
        default=None,
        metavar="URL",
        help=(
            "Override the repository URL used to fetch the release tarball "
            "when --fetch-sha256 is set (default: repository field from "
            "Cargo.toml).  Useful during pre-release or fork validation, e.g. "
            "--upstream-repo https://github.com/MyFork/himmelblau"
        ),
    )
    ap.add_argument(
        "--out",
        default="./packaging/aur",
        help="Output directory (default: ./packaging/aur)",
    )
    ap.add_argument(
        "--repo-root",
        default=None,
        help="Repository root (default: parent of the scripts/ directory)",
    )
    args = ap.parse_args()

    # Resolve repo root
    if args.repo_root:
        repo_root = Path(args.repo_root).resolve()
    else:
        repo_root = Path(__file__).parent.parent.resolve()

    # Load metadata
    meta = load_workspace_metadata(repo_root)
    version  = args.version or meta["version"]
    homepage = meta["homepage"]
    repo_url = meta["repository"]
    license_id = meta["license"]

    # Resolve source URL / name
    src_url  = tarball_url(repo_url, version)
    src_name = f"himmelblau-{version}.tar.gz"

    # The repo used to *fetch* the tarball for SHA-256 calculation.
    # This defaults to the canonical upstream URL from Cargo.toml but can be
    # overridden (e.g. to a fork) for pre-release / validation purposes.
    fetch_repo_url = args.upstream_repo or repo_url

    # Resolve SHA-256
    if args.sha256:
        sha256 = args.sha256
    elif args.fetch_sha256:
        sha256 = fetch_sha256(fetch_repo_url, version)
    else:
        sha256 = "SKIP"

    # Render PKGBUILD
    # The source URL uses the PKGBUILD variable ${pkgver} (shell convention)
    # so that the line stays consistent if pkgver is bumped manually.
    pkgbuild_source_url = f"{repo_url.rstrip('/').removesuffix('.git')}/archive/refs/tags/${{pkgver}}.tar.gz"
    pkgbuild = PKGBUILD_TEMPLATE.format(
        version=version,
        homepage=homepage,
        license=license_id,
        depends="\n".join(f"    '{d}'" for d in ARCH_DEPENDS),
        optdepends="\n".join(f"    '{d}'" for d in ARCH_OPTDEPENDS),
        makedepends="\n".join(f"    '{d}'" for d in ARCH_MAKEDEPENDS),
        provides=" ".join(f"'{p}'" for p in ARCH_PROVIDES),
        backup=" ".join(f"'{b}'" for b in BACKUP_FILES),
        source_url=pkgbuild_source_url,
        sha256sums=sha256,
    )

    # Render .SRCINFO
    srcinfo = generate_srcinfo(
        version=version,
        pkgrel=args.pkgrel,
        homepage=homepage,
        license_id=license_id,
        sha256=sha256,
        source_url=src_url,
        source_name=src_name,
    )

    # Write output files
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    pkgbuild_path = out_dir / "PKGBUILD"
    srcinfo_path  = out_dir / ".SRCINFO"

    pkgbuild_path.write_text(pkgbuild, encoding="utf-8")
    srcinfo_path.write_text(srcinfo,   encoding="utf-8")

    print(f"Generated: {pkgbuild_path}")
    print(f"Generated: {srcinfo_path}")
    print(f"  pkgver = {version}")
    print(f"  sha256 = {sha256}")


if __name__ == "__main__":
    main()
