# Code Style and Conventions

## Rust-Specific Guidelines

### Error Handling (Strict)
- **MUST USE**: `Result<T, E>` types for fallible operations
- **FORBIDDEN**: `unwrap()`, `expect()`, `panic!()`, `todo!()`, `unimplemented!()`
- **REQUIRED**: Proper error propagation with `?` operator
- All crates have `#![deny(clippy::unwrap_used)]` and similar lint denials

### Naming Conventions
- **Functions/Variables**: `snake_case`
- **Types/Structs/Enums**: `PascalCase`
- **Constants**: `SCREAMING_SNAKE_CASE`
- **Modules**: `snake_case`

### Import Organization
1. Standard library imports first
2. External crate imports second
3. Local module imports last
4. Group related imports together

### Type Usage
- Prefer explicit types over type inference where clarity helps
- Use `async/await` for asynchronous code
- Leverage tokio runtime features
- Use strong typing to prevent errors

### Logging
- Use `tracing` macros: `trace!()`, `debug!()`, `info!()`, `warn!()`, `error!()`
- Structured logging with fields where appropriate
- Avoid `println!()` in production code

### Comments and Documentation
- Avoid unnecessary comments - code should be self-documenting
- Use doc comments (`///`) for public APIs
- Include examples in doc comments where helpful

## Clippy Configuration
- Custom thresholds in `clippy.toml`:
  - Max 9 function arguments (increased from default 7)
  - Type complexity threshold: 300 (increased from 250)
- All clippy lints are enforced

## Formatting
- Use `rustfmt` with default settings
- Consistent indentation and spacing
- Line length follows rustfmt defaults

## Async/Concurrency Patterns
- Use tokio runtime throughout
- Prefer `async/await` over manual Future implementations
- Use appropriate tokio synchronization primitives
- Handle cancellation and timeouts properly