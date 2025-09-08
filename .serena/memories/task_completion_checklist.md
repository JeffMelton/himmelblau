# Task Completion Checklist

## Required Steps After Code Changes

### 1. Code Quality Checks
- [ ] Run `cargo clippy --all-features` - Must pass without warnings
- [ ] Run `cargo fmt` - Ensure code is properly formatted
- [ ] Check that no `unwrap()`, `expect()`, `panic!()`, `todo!()` were introduced

### 2. Testing
- [ ] Run `cargo test` - All tests must pass
- [ ] Run `cargo test -p <specific-package>` for targeted testing if changes are localized
- [ ] Consider adding new tests for new functionality

### 3. Build Verification
- [ ] Run `cargo build --all-features --all-targets` - Must compile successfully
- [ ] Verify no new compiler warnings were introduced

### 4. Documentation
- [ ] Update doc comments for any public API changes
- [ ] Run `cargo doc` to verify documentation builds correctly
- [ ] Update README.md or other docs if user-facing changes

### 5. Integration Testing (if applicable)
- [ ] Test daemon functionality if changes affect `src/daemon`
- [ ] Test PAM/NSS integration if changes affect authentication
- [ ] Verify configuration changes work with example configs

### 6. Git Workflow
- [ ] Commit with descriptive commit messages
- [ ] Consider squashing commits for cleaner history
- [ ] Ensure commit follows project's contribution guidelines

## Optional but Recommended
- [ ] Run `make` to test packaging on current distro
- [ ] Check `cargo tree` for any unexpected dependency changes
- [ ] Review changes against security best practices
- [ ] Test with different feature flags if applicable

## Before Submitting PR
- [ ] Rebase on latest main branch
- [ ] Ensure CI will pass (all above checks)
- [ ] Write clear PR description explaining changes