# Exonum python backend

Work in progress, readme will be updated soon.

## Linkage

To avoid linkage issues, you have to do (for linux):

```sh
source "$HOME/.cargo/env"
export RUST_SRC_PATH="$(rustc --print sysroot)/lib/rustlib/src/rust/src"
export LD_LIBRARY_PATH="$(rustc --print sysroot)/lib:$LD_LIBRARY_PATH"
```

For MacOS in theory you can replace `LD_LIBRARY_PATH` with `DYLD_LIBRARY_PATH` and it may work, but I didn't check.
