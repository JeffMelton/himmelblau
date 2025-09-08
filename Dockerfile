FROM rust:1.89.0

# Set environment variables for Himmelblau build
ENV HIMMELBLAU_ALLOW_MISSING_SELINUX=1
ENV RUSTC_WRAPPER=""

# Install system dependencies required for building and testing Himmelblau
RUN apt-get update && apt-get install -y \
    # Core build dependencies
    libpam0g-dev \
    libudev-dev \
    libssl-dev \
    pkg-config \
    # TPM and security dependencies
    tpm-udev \
    libtss2-dev \
    libcap-dev \
    # Authentication and directory service dependencies
    libdhash-dev \
    libkrb5-dev \
    libpcre2-dev \
    # Clang for bindgen (required for some crates)
    libclang-dev \
    # Build tools
    autoconf \
    gettext \
    # D-Bus support
    libdbus-1-dev \
    # Unicode support
    libunistring-dev \
    # GTK/UI dependencies (for qr-greeter and desktop components)
    libgirepository1.0-dev \
    libcairo2-dev \
    libgdk-pixbuf-2.0-dev \
    libsoup-3.0-dev \
    libpango1.0-dev \
    libatk1.0-dev \
    libgtk-3-dev \
    libwebkit2gtk-4.1-dev \
    # Additional utilities
    git \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for testing
RUN useradd -m -u 1000 testuser

# Set working directory
WORKDIR /workspace

# Copy source code
COPY . .

# Change ownership to testuser
RUN chown -R testuser:testuser /workspace

# Initialize and update submodules if they exist
RUN git submodule update --init --recursive || true

# Switch to non-root user
USER testuser

# Build the project with all features and targets
RUN cargo build --all-features --all-targets

# Default command runs tests
CMD ["cargo", "test"]