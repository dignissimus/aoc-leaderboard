# Start from the version of Judge0 you are currently using
FROM judge0/judge0:1.13.1-extra

# Switch to root to install system packages
USER root

# 1. Install Fortran 90 (gfortran) and Haskell (ghc)
RUN apt-get update && \
    apt-get install -y gfortran ghc && \
    rm -rf /var/lib/apt/lists/*

# 2. Install Custom Rust
ENV RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    PATH=/usr/local/cargo/bin:$PATH

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --no-modify-path && \
    chmod -R a+w $RUSTUP_HOME $CARGO_HOME

# Switch back to the unprivileged judge0 user for security
USER judge0
