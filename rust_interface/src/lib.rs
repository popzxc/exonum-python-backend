#[macro_use]
extern crate lazy_static;

use std::process::Command;

mod errors;
pub mod merkledb_interface;
mod pending_deployment;
mod python_interface;
mod runtime;
mod types;

pub use runtime::PythonRuntime;

// Functions for python side.
pub use merkledb_interface::{
    list_index::merkledb_list_index, map_index::merkledb_map_index,
    proof_list_index::merkledb_proof_list_index, proof_map_index::merkledb_proof_map_index,
};
pub use python_interface::{get_snapshot_token, init_python_side};

// TODO return result
pub fn initialize_python_backend(python_config_path: &str) -> Option<PythonRuntime> {
    let python_run_command = Command::new("python")
        .arg("-m")
        .arg("exonum_runtime")
        .arg(python_config_path)
        .spawn();

    let python_process = match python_run_command {
        Ok(handle) => handle,
        Err(_) => return None,
    };

    let python_runtime = PythonRuntime::new(python_process);

    Some(python_runtime)
}
