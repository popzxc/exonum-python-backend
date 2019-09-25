use std::ffi::CStr;
use std::os::raw::c_char;

#[repr(C)]
pub struct PythonArtifactId {
    pub runtim_ide: u32,
    pub name: *const c_char,
}

#[repr(C)]
pub struct PythonInstanceSpec {
    pub name: *const c_char,
    pub artifact: PythonArtifactId,
}

// TODO have an enum to return statuses.
type PythonDeployArtifactMethod = unsafe extern "C" fn(artifact: PythonArtifactId, spec: *const u8);
type PythonIsArtifactDeployedMethod = unsafe extern "C" fn(artifact: PythonArtifactId) -> bool;
type PythonStartServiceMethod = unsafe extern "C" fn(spec: PythonInstanceSpec);
// type PythonConfigureService = unsafe extern "C"

#[repr(C)]
#[derive(Debug)]
pub struct PythonRuntimeInterface {
    pub deploy_artifact: PythonDeployArtifactMethod,
    pub is_artifact_deployes: PythonIsArtifactDeployedMethod,
    pub start_service: PythonStartServiceMethod,
}
