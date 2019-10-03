use std::collections::BTreeMap;
use std::os::raw::c_void;
use std::sync::RwLock;

use exonum::runtime::ArtifactId;
use exonum_merkledb::Fork;

use super::{
    errors::PythonRuntimeError,
    pending_deployment::PendingDeployment,
    types::{RawArtifactId, RawCallInfo, RawInstanceDescriptor, RawInstanceSpec},
};

lazy_static! {
    pub(crate) static ref PYTHON_INTERFACE: RwLock<PythonRuntimeInterface> =
        RwLock::new(PythonRuntimeInterface::default());
}

#[derive(Debug, Default)]
pub struct PythonRuntimeInterface {
    pub methods: PythonMethods,

    pub(in crate::python_interface) ongoing_deployments: BTreeMap<ArtifactId, PendingDeployment>,
}

impl PythonRuntimeInterface {
    pub fn notify_deployment_started(
        &mut self,
        artifact: ArtifactId,
        deployment: PendingDeployment,
    ) {
        self.ongoing_deployments.insert(artifact, deployment);
    }

    pub fn error_code_to_result(code: u32) -> Result<(), PythonRuntimeError> {
        let error = match code {
            0 => return Ok(()),
            _ => PythonRuntimeError::from_value(code),
        };

        Err(error)
    }
}

// Types of the stored functions.
type PythonDeployArtifactMethod =
    unsafe extern "C" fn(artifact: RawArtifactId, spec: *const u8, spec_len: u64) -> u32;
type PythonIsArtifactDeployedMethod = unsafe extern "C" fn(artifact: RawArtifactId) -> bool;
type PythonStartServiceMethod = unsafe extern "C" fn(spec: RawInstanceSpec) -> u32;
type PythonInitializeServiceMethod = unsafe extern "C" fn(
    descriptor: RawInstanceDescriptor,
    parameters: *const u8,
    parameters_len: u64,
) -> u32;
type PythonStopServiceMethod = unsafe extern "C" fn(descriptor: RawInstanceDescriptor) -> u32;
type PythonExecuteMethod =
    unsafe extern "C" fn(call_info: RawCallInfo, payload: *const u8, payload_len: u32) -> u32;
type PythonArtifactProtobufSpecMethod = unsafe extern "C" fn();
type PythonStateHashesMethod = unsafe extern "C" fn();
type PythonBeforeCommitMethod = unsafe extern "C" fn();
type PythonAfterCommitMethod = unsafe extern "C" fn(fork: *const Fork);
type PythonFreeResourceMethod = unsafe extern "C" fn(resource: *const c_void);

/// Structure with the Python side API.
#[repr(C)]
#[derive(Debug, Clone, Copy)]
pub struct PythonMethods {
    pub deploy_artifact: PythonDeployArtifactMethod,
    pub is_artifact_deployed: PythonIsArtifactDeployedMethod,
    pub start_service: PythonStartServiceMethod,
    pub initialize_service: PythonInitializeServiceMethod,
    pub stop_service: PythonStopServiceMethod,
    pub execute: PythonExecuteMethod,
    pub artifact_protobuf_spec: PythonArtifactProtobufSpecMethod,
    pub state_hashes: PythonStateHashesMethod,
    pub before_commit: PythonBeforeCommitMethod,
    pub after_commit: PythonAfterCommitMethod,
    pub free_resource: PythonFreeResourceMethod,
}

impl Default for PythonMethods {
    fn default() -> Self {
        Self {
            deploy_artifact: default_deploy,
            is_artifact_deployed: default_is_artifact_deployed,
            start_service: default_start_service,
            initialize_service: default_initialize_service_method,
            stop_service: default_stop_service_method,
            execute: default_execute_method,
            artifact_protobuf_spec: default_artifact_protobuf_spec_method,
            state_hashes: default_state_hashes_method,
            before_commit: default_before_commit_method,
            after_commit: default_after_commit_method,
            free_resource: default_free_resource_method,
        }
    }
}

/// Initialize python interfaces.
/// This function is meant to be called by the python side during the initialization.
#[no_mangle]
pub unsafe extern "C" fn init_python_side(methods: *const PythonMethods) {
    let mut python_interface = PYTHON_INTERFACE.write().expect("Excepted write");

    (*python_interface).methods = *methods;
}

/// Removes an artifact from the pending deployments.
/// This function is meant to be called by the python after the deployment of the artifact.
#[no_mangle]
fn deployment_completed(python_artifact: RawArtifactId, result: u32) {
    let artifact = ArtifactId::from(python_artifact);
    let mut python_interface = PYTHON_INTERFACE.write().expect("Excepted write");

    let future = python_interface.ongoing_deployments.remove(&artifact);

    match future {
        Some(mut f) => match PythonRuntimeInterface::error_code_to_result(result) {
            Ok(()) => {
                f.complete();
            }
            Err(error) => {
                f.error(error.into());
            }
        },
        None => {
            panic!(
                "Python deployed an artifact that wasn't expected: {:?}",
                artifact
            );
        }
    }
}

// Blank implementations to avoid storing `Option`.

unsafe extern "C" fn default_deploy(
    _artifact: RawArtifactId,
    _spec: *const u8,
    _spec_len: u64,
) -> u32 {
    PythonRuntimeError::RuntimeNotReady as u32
}

unsafe extern "C" fn default_is_artifact_deployed(_artifact: RawArtifactId) -> bool {
    false
}

unsafe extern "C" fn default_start_service(_spec: RawInstanceSpec) -> u32 {
    PythonRuntimeError::RuntimeNotReady as u32
}

unsafe extern "C" fn default_initialize_service_method(
    _descriptor: RawInstanceDescriptor,
    _parameters: *const u8,
    _parameters_len: u64,
) -> u32 {
    PythonRuntimeError::RuntimeNotReady as u32
}

unsafe extern "C" fn default_stop_service_method(_descriptor: RawInstanceDescriptor) -> u32 {
    PythonRuntimeError::RuntimeNotReady as u32
}

unsafe extern "C" fn default_execute_method(
    _call_info: RawCallInfo,
    _payload: *const u8,
    _payload_len: u32,
) -> u32 {
    PythonRuntimeError::RuntimeNotReady as u32
}
unsafe extern "C" fn default_artifact_protobuf_spec_method() {}
unsafe extern "C" fn default_state_hashes_method() {}
unsafe extern "C" fn default_before_commit_method() {}
unsafe extern "C" fn default_after_commit_method(_fork: *const Fork) {}
unsafe extern "C" fn default_free_resource_method(_resource: *const c_void) {}
