# Exonum Python Runtime

Experimental implementation of the Exonum Python Runtime.

## Install

To install and launch the Exonum Python Runtime you should do the following:

1. Compile the `rust_interface` library:

   ```sh
   cargo build --lib
   ```

2. Create `config.toml` (you can just copy it from `sample_config.toml`):

    ```sh
    cp sample_config.toml config.toml
    ```

3. Edit `config.toml` to represent actual values (especially `rust_library_path`).

4. Install the `python_runtime` module (you need to have `python` 3.7+):

    ```sh
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -e python_runtime
    ```

5. Run the Python runtime (note that module name is not `python_runtime`):

    ```sh
    python -m exonum_runtime ./config.toml
    ```

If everything was done correctly, the node will be start with the following output:

```sh
DEBUG:exonum_runtime.lib:Started python runtime
DEBUG:asyncio:Using selector: EpollSelector
Creating database in temporary dir...
DEBUG:exonum_runtime.runtime.runtime:Initialized rust part
Starting a single node...
Blockchain is ready for transactions!
```

## Running the service

Description of how to run the service can be found in the [RUNNING.md](RUNNING.md).

## Cretating your own services

Description of the main prepequirements for creating new services can be found
at the [CREATING_SERVICES.md](CREATING_SERVICES.md).

## Examples

You can find the service examples in the [examples](examples) section.

## Known problems

The project is in the pre-alpha stage, so you can experience some troubles with it.

Feel free to report them by creating an issue.

### Linkage

If you will experience linkage problems, you may try the following (for linux):

```sh
source "$HOME/.cargo/env"
export RUST_SRC_PATH="$(rustc --print sysroot)/lib/rustlib/src/rust/src"
export LD_LIBRARY_PATH="$(rustc --print sysroot)/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="/home/popzxc/hobby/exonum-python-backend/target/debug/deps:$LD_LIBRARY_PATH"
```

For MacOS in theory you can replace `LD_LIBRARY_PATH` with `DYLD_LIBRARY_PATH` and it may work, but I didn't check.

## Licence

Exonum Python Runtime is licensed under the Apache License (Version 2.0).
See [LICENSE](LICENSE) for details.
