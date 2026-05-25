#!/usr/bin/env bash
# platform/arch/test/lint.sh — local validation harness for the AUR PKGBUILD.
#
# Renders PKGBUILD.in inside an archlinux:base-devel container, then either
# lints it (default, ~30s) or runs a full makepkg build (--build, 20–40 min).
#
# Targets: macOS or Linux host with podman + archlinux:base-devel.
# See platform/arch/test/README.md for usage, env caveats, and design notes.

set -euo pipefail

# ── Locate repo root (this script lives at platform/arch/test/lint.sh) ─────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

# ── CLI ────────────────────────────────────────────────────────────────────────
MODE="lint"
VERSION=""

usage() {
  cat <<'EOF'
Usage: platform/arch/test/lint.sh [--build] [--version X.Y.Z] [--help]

Validate platform/arch/PKGBUILD.in inside an archlinux:base-devel container.

Modes:
  (default)           Lint mode (~30s). Renders PKGBUILD with sha256=SKIP,
                      then runs: bash -n, namcap, makepkg --printsrcinfo.
  --build             Full build mode (20–40 min under qemu on Apple Silicon).
                      Computes real sha256 of the upstream tarball, then runs
                      makepkg -s end-to-end and namcaps the built .pkg.tar.zst.

Options:
  --version X.Y.Z     Use this version instead of the latest local git tag.
  --help              Print this message and exit.

Examples:
  platform/arch/test/lint.sh
  platform/arch/test/lint.sh --version 3.1.5
  platform/arch/test/lint.sh --build
  platform/arch/test/lint.sh --build --version 3.1.5
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --build)    MODE="build"; shift ;;
    --version)  VERSION="${2:?--version needs a value}"; shift 2 ;;
    --help|-h)  usage; exit 0 ;;
    *)          echo "error: unknown arg: $1" >&2; usage >&2; exit 2 ;;
  esac
done

# ── Default version = latest semver tag (no pre-release suffix) ────────────────
if [[ -z "${VERSION}" ]]; then
  VERSION="$(git -C "${REPO_ROOT}" tag --list --sort=-v:refname '[0-9]*' \
             | grep -Ev -- '-(alpha|beta|rc)' | head -n1 || true)"
  if [[ -z "${VERSION}" ]]; then
    echo "error: could not determine latest tag; pass --version explicitly" >&2
    exit 2
  fi
fi

# ── Host arch detection: Apple Silicon / aarch64 → qemu emulate amd64 ──────────
HOST_ARCH="$(uname -m)"
PLATFORM_FLAGS=()
if [[ "${HOST_ARCH}" != "x86_64" ]]; then
  PLATFORM_FLAGS=(--platform linux/amd64)
fi

command -v podman >/dev/null \
  || { echo "error: podman not found on PATH" >&2; exit 2; }

IMAGE="archlinux:base-devel"

cat <<EOF
─── AUR PKGBUILD validation harness ───────────────────────────────────
  mode:        ${MODE}
  version:     ${VERSION}
  host arch:   ${HOST_ARCH}$([[ ${#PLATFORM_FLAGS[@]} -gt 0 ]] && echo "  (qemu-emulating linux/amd64)")
  image:       ${IMAGE}
  repo root:   ${REPO_ROOT}
───────────────────────────────────────────────────────────────────────
EOF

# ── In-container driver. /src is the repo (read-only); /work is scratch. ───────
# Reads PKGVER + MODE from the environment we pass via `podman run -e`.
CONTAINER_SCRIPT=$(cat <<'INNER'
set -euo pipefail

: "${PKGVER:?}"
: "${MODE:?}"

# pacman 6.1+ sandbox segfaults under rootless podman. Documented workaround.
sed -i 's/^#DisableSandboxSyscalls$/DisableSandboxSyscalls/' /etc/pacman.conf

echo ">> installing namcap + curl"
pacman -Sy --noconfirm --needed namcap curl >/dev/null

mkdir -p /work && cd /work
cp /src/platform/arch/PKGBUILD.in     PKGBUILD
cp /src/platform/arch/himmelblau.install .

# Guard the *definition* lines (not just any mention) so a sabotaged template
# like `pkgver=BOGUS` is caught even though the comments still mention @PKGVER@.
if ! grep -qE '^pkgver=@PKGVER@$' PKGBUILD; then
  echo "!! PKGBUILD.in is missing the literal 'pkgver=@PKGVER@' line" >&2
  exit 1
fi
if ! grep -qE "^sha256sums=\('@SHA256@'\)$" PKGBUILD; then
  echo "!! PKGBUILD.in is missing the literal sha256sums=('@SHA256@') line" >&2
  exit 1
fi

# Compute sha256 of the upstream tarball for build mode; SKIP for lint mode.
if [[ "${MODE}" == "build" ]]; then
  echo ">> fetching upstream tarball to compute sha256"
  TARBALL_URL="https://github.com/himmelblau-idm/himmelblau/archive/refs/tags/${PKGVER}.tar.gz"
  curl -fsSL "${TARBALL_URL}" -o "himmelblau-${PKGVER}.tar.gz"
  SHA256="$(sha256sum "himmelblau-${PKGVER}.tar.gz" | awk '{print $1}')"
  echo "   sha256=${SHA256}"
else
  SHA256="SKIP"
fi

sed -i -e "s|@PKGVER@|${PKGVER}|g" -e "s|@SHA256@|${SHA256}|g" PKGBUILD

# makepkg refuses to run as root; create a builder and hand it the work dir.
useradd -m builder
chown -R builder:builder /work

echo ">> bash -n PKGBUILD"
bash -n PKGBUILD

echo ">> namcap PKGBUILD"
# namcap exits 0 even on W:/E: lines, so we grep the output ourselves.
namcap PKGBUILD | tee namcap-pkgbuild.log
if grep -E '^(PKGBUILD )?[A-Za-z0-9_.-]+ (W|E): ' namcap-pkgbuild.log; then
  echo "!! namcap reported warnings or errors on PKGBUILD" >&2
  exit 1
fi

echo ">> makepkg --printsrcinfo (as builder)"
su builder -c 'cd /work && makepkg --printsrcinfo' > .SRCINFO
head -n5 .SRCINFO

if [[ "${MODE}" == "build" ]]; then
  echo ">> makepkg -s (full build, this is the long one)"
  # SKIP integrity already, but we computed a real sha256 above so makepkg
  # will verify it. --noconfirm for unattended dep install.
  su builder -c 'cd /work && makepkg -s --noconfirm --skipinteg=false'

  PKG_FILE="$(ls /work/*.pkg.tar.zst | head -n1)"
  echo ">> namcap on built package: ${PKG_FILE}"
  namcap "${PKG_FILE}" | tee namcap-pkg.log
  if grep -E ' (W|E): ' namcap-pkg.log; then
    echo "!! namcap reported warnings or errors on built package" >&2
    exit 1
  fi
fi

echo ">> in-container checks PASSED"
INNER
)

# ── Run it ─────────────────────────────────────────────────────────────────────
set +e
podman run --rm \
  "${PLATFORM_FLAGS[@]}" \
  -e PKGVER="${VERSION}" \
  -e MODE="${MODE}" \
  -v "${REPO_ROOT}:/src:ro" \
  "${IMAGE}" \
  bash -c "${CONTAINER_SCRIPT}"
RC=$?
set -e

echo "───────────────────────────────────────────────────────────────────────"
if [[ ${RC} -eq 0 ]]; then
  echo "PASS — ${MODE} mode, version ${VERSION}"
else
  echo "FAIL — ${MODE} mode, version ${VERSION} (exit ${RC})"
fi
echo "───────────────────────────────────────────────────────────────────────"
exit ${RC}
