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
automatically on every release, and you can do the same locally for the first push:

```bash
# From the root of this repository:
python3 scripts/gen_pkgbuild.py --fetch-sha256
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

Because the upstream tagging workflow runs on `stable-*` branches, you can
trigger a test run in your fork by pushing a dummy tag:

```bash
git tag 4.0.0-test
git push origin 4.0.0-test
```

Watch the **Actions** tab on GitHub.  The `aur-publish` job will:

1. Compute the SHA-256 of the release tarball.
2. Regenerate `PKGBUILD` and `.SRCINFO`.
3. Clone the AUR repo, copy the files, and push.

Check the result at <https://aur.archlinux.org/packages/himmelblau>.

> [!NOTE]
> Remove the test tag when you are done:
> ```bash
> git push origin --delete 4.0.0-test
> git tag -d 4.0.0-test
> ```

---

## 7. (Optional) Test the PKGBUILD locally on Arch Linux

On any Arch Linux machine (or an `archlinux` Docker container) you can
validate the package builds and installs cleanly before relying on CI:

```bash
# Install build dependencies
sudo pacman -S --needed base-devel rust cmake clang pkgconf python krb5 \
    libcap pam sqlite systemd

# Build (without installing)
cd packaging/aur/
makepkg -s --noconfirm

# Inspect the built package
makepkg --printsrcinfo    # verify .SRCINFO matches expectations
```

---

## Quick-reference checklist

- [ ] AUR account created (or existing account confirmed)
- [ ] Ed25519 SSH key pair generated
- [ ] Public key added to AUR account (**My Account** → SSH Public Key)
- [ ] Private key added to GitHub repository secret as `AUR_SSH_PRIVATE_KEY`
- [ ] Initial PKGBUILD pushed to AUR manually (step 5 above)
- [ ] Workflow validated with a test tag (step 6 above)
