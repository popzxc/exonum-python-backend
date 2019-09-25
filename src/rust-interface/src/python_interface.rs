// use std::ffi::CStr;

use super::types::{PythonArtifactId, PythonInstanceSpec};

// TODO have an enum to return statuses.
type PythonDeployArtifactMethod =
    unsafe extern "C" fn(artifact: PythonArtifactId, spec: *const u8, spec_len: usize);
type PythonIsArtifactDeployedMethod = unsafe extern "C" fn(artifact: PythonArtifactId) -> bool;
type PythonStartServiceMethod = unsafe extern "C" fn(spec: PythonInstanceSpec);

#[derive(Debug)]
pub struct PythonRuntimeInterface {
    pub deploy_artifact: PythonDeployArtifactMethod,
    pub is_artifact_deployed: PythonIsArtifactDeployedMethod,
    pub start_service: PythonStartServiceMethod,
}

impl Default for PythonRuntimeInterface {
    fn default() -> Self {
        Self {
            deploy_artifact: default_deploy,
            is_artifact_deployed: default_is_artifact_deployed,
            start_service: default_start_service,
        }
    }
}

unsafe extern "C" fn default_deploy(
    _artifact: PythonArtifactId,
    _spec: *const u8,
    _spec_len: usize,
) {
    // TODO return error.
    panic!("Not ready");
}

unsafe extern "C" fn default_is_artifact_deployed(_artifact: PythonArtifactId) -> bool {
    // TODO return error.
    panic!("Not ready");
}

unsafe extern "C" fn default_start_service(_spec: PythonInstanceSpec) {
    // TODO return error.
    panic!("Not ready");
}
