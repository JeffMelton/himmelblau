# AUR Publishing Setup Guide

This document explains every prerequisite that must be satisfied **before** the
[`aur-publish.yml`](../.github/workflows/aur-publish.yml) workflow can push
successfully to the Arch User Repository (AUR).

---

## 1. Register an AUR account

The workflow authenticates with AUR using an SSH key tied to a named AUR
account.  If you do not already have one:

1. Visit <https://aur.archlinux.org/register>.
2. Fill in a **username**, **email address**, and **password**.
3. Confirm your email address via the link sent to you.

> [!TIP]
> Use a dedicated machine account (e.g. `himmelblau-bot`) rather than a
> personal account so that the secret key is scoped only to CI.

---

## 2. Generate a dedicated SSH key pair

Generate an **Ed25519** key pair on a trusted machine (not inside GitHub
Actions):

```bash
ssh-keygen -t ed25519 -C "himmelblau-aur-ci" -f ~/.ssh/aur_ci_ed25519
```

This creates two files:

| File | Purpose |
|------|---------|
| `~/.ssh/aur_ci_ed25519` | **Private key** – goes into GitHub Secrets |
| `~/.ssh/aur_ci_ed25519.pub` | **Public key** – registered with AUR |

> [!CAUTION]
> Never commit the private key to git or paste it anywhere other than the
> GitHub repository secret described in step 4.

---

## 3. Add the public key to your AUR account

1. Log in to <https://aur.archlinux.org>.
2. Click your username in the top-right corner → **My Account**.
3. Paste the contents of `~/.ssh/aur_ci_ed25519.pub` into the
   **SSH Public Key** field.
4. Click **Update**.

Verify the key works from a local terminal:

```bash
ssh -i ~/.ssh/aur_ci_ed25519 aur@aur.archlinux.org
# Expected output:
#   Welcome to AUR, <username>! Interactive shell is disabled.
```

---

## 4. Add the private key as a GitHub repository secret

1. Open your repository on GitHub.
2. Go to **Settings → Secrets and variables → Actions**.
3. Click **New repository secret**.
4. Set the name to exactly:
   ```
   AUR_SSH_PRIVATE_KEY
   ```
5. Paste the **entire** contents of `~/.ssh/aur_ci_ed25519` (including the
   `-----BEGIN OPENSSH PRIVATE KEY-----` header and footer) as the value.
6. Click **Add secret**.

The workflow references this secret as `${{ secrets.AUR_SSH_PRIVATE_KEY }}`.

---

## 5. Create the AUR package repository (first push only)

An AUR package repository is created automatically the **first time** a valid
`PKGBUILD` is pushed.  You need to do this once from a local machine because
the git remote must already contain a valid initial commit.

### 5a. Generate the initial PKGBUILD and .SRCINFO locally

The `packaging/` directory is excluded from git (it holds build artifacts).
`gen_pkgbuild.py` generates both files fresh each time — the workflow does this
automatically on every release, and you can do the same locally for the first push.

Use `--use-latest-release` to generate a PKGBUILD that targets the most recently
published upstream release.  This is always safe because it queries the GitHub
Releases API and only uses tags that already exist:

```bash
# From the root of this repository:
python3 scripts/gen_pkgbuild.py --use-latest-release
# Output written to packaging/aur/PKGBUILD and packaging/aur/.SRCINFO
```

### 5b. Clone the (empty) AUR repository

```bash
GIT_SSH_COMMAND="ssh -i ~/.ssh/aur_ci_ed25519" \
  git clone ssh://aur@aur.archlinux.org/himmelblau.git /tmp/aur-himmelblau
```

AUR returns an empty repository if the package does not exist yet – this is
expected.

### 5c. Commit and push the initial files

```bash
cp packaging/aur/PKGBUILD  /tmp/aur-himmelblau/
cp packaging/aur/.SRCINFO  /tmp/aur-himmelblau/

cd /tmp/aur-himmelblau
git add PKGBUILD .SRCINFO
git commit -m "Initial release"
GIT_SSH_COMMAND="ssh -i ~/.ssh/aur_ci_ed25519" git push origin master
```

After this first push the package page will be visible at
<https://aur.archlinux.org/packages/himmelblau>.

---

## 6. Validate the workflow end-to-end

Because the `aur-publish` workflow triggers on version-shaped tags, you can
trigger a test run in your fork by pushing any matching dummy tag:

```bash
git tag 0.0.0-test
git push origin 0.0.0-test
```

Watch the **Actions** tab on GitHub.  The `aur-publish` job will:

1. Query the GitHub Releases API for the **latest published upstream release**.
2. Compute the SHA-256 of that release's tarball.
3. Regenerate `PKGBUILD` and `.SRCINFO`.
4. Clone the AUR repo, copy the files, and push.

> [!NOTE]
> The version packaged is always the *latest upstream release*, not the tag you
> pushed — the tag is just the workflow trigger.

Check the result at <https://aur.archlinux.org/packages/himmelblau>.

> [!NOTE]
> Remove the test tag when you are done:
> ```bash
> git push origin --delete 0.0.0-test
> git tag -d 0.0.0-test
> ```

---

## 7. (Optional) Test the PKGBUILD locally

### 7a. Native Arch Linux

On any Arch Linux machine you can validate the package builds cleanly before
relying on CI:

```bash
# Install build dependencies
sudo pacman -S --needed base-devel rust cmake clang pkgconf python krb5 \
    libcap pam sqlite systemd

# Build (without installing)
cd packaging/aur/
makepkg -s --noconfirm

# Verify .SRCINFO matches expectations
makepkg --printsrcinfo
```

---

### 7b. Using `podman` — fast metadata check (no compilation)

This validates the PKGBUILD syntax and regenerates `.SRCINFO` without
downloading sources or compiling anything.  Takes only a few seconds.

First, generate the PKGBUILD targeting the latest published upstream release:

```bash
# From the root of the repository:
python3 scripts/gen_pkgbuild.py --use-latest-release
```

Then spin up a throwaway Arch Linux container and run the check:

```bash
podman run --rm \
  -v "$(pwd)/packaging/aur:/pkgbuild:z" \
  archlinux:latest \
  bash -c "
    pacman -Sy --noconfirm base-devel &&
    cd /pkgbuild &&
    makepkg --printsrcinfo
  "
```

The `:z` volume flag relabels the mount for SELinux-enforcing hosts (Fedora,
RHEL, etc.); it is harmless on non-SELinux systems.

---

### 7c. Using `podman` — full build test (~20–40 minutes)

This mirrors what a real `makepkg` run on an Arch user's machine would do:
downloads the release tarball, runs `cargo fetch`, compiles the whole workspace,
and produces a `.pkg.tar.zst` in `packaging/aur/`.

> [!IMPORTANT]
> The container needs outbound internet access (to download the source tarball
> and Rust crates).  The build takes 20–40 minutes on typical hardware.
> `makepkg` deliberately refuses to run as `root` (a security design choice that
> prevents build scripts from silently modifying your system), so the script
> creates a `builder` user inside the container.

First, generate the PKGBUILD targeting the latest published upstream release:

```bash
python3 scripts/gen_pkgbuild.py --use-latest-release
```

Then run the container build:

```bash
podman run --rm \
  -v "$(pwd)/packaging/aur:/pkgbuild:z" \
  archlinux:latest \
  bash -c "
    # Refresh keyring and install every build dependency up-front
    pacman -Syu --noconfirm &&
    pacman -S --noconfirm --needed \
        base-devel cargo cmake clang pkgconf python \
        krb5 libcap pam sqlite systemd tpm2-tss &&

    # makepkg must not run as root
    useradd -m builder &&
    chown -R builder /pkgbuild &&

    # Build the package (downloads tarball, compiles, packages)
    su - builder -c 'cd /pkgbuild && makepkg --noconfirm'
  "
```

On success the `.pkg.tar.zst` archive appears in `packaging/aur/`.  Inspect it
with:

```bash
ls -lh packaging/aur/himmelblau-*.pkg.tar.zst

# List every installed file without extracting
podman run --rm \
  -v "$(pwd)/packaging/aur:/pkgbuild:z" \
  archlinux:latest \
  bash -c "pacman -Qlp /pkgbuild/himmelblau-*.pkg.tar.zst"
```

> [!TIP]
> Pass `-e CARGO_NET_OFFLINE=false` explicitly if the container blocks outbound
> traffic by default in your environment (this is the correct default, but some
> rootless-podman network configurations restrict it).

---

## Quick-reference checklist

- [ ] AUR account created (or existing account confirmed)
- [ ] Ed25519 SSH key pair generated
- [ ] Public key added to AUR account (**My Account** → SSH Public Key)
- [ ] Private key added to GitHub repository secret as `AUR_SSH_PRIVATE_KEY`
- [ ] Initial PKGBUILD pushed to AUR manually (step 5 above)
- [ ] Workflow validated with a test tag (step 6 above)
- [ ] (Optional) PKGBUILD metadata validated with `podman` (step 7b above)
- [ ] (Optional) Full build tested with `podman` (step 7c above)
