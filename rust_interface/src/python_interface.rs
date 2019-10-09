use std::collections::BTreeMap;
use std::os::raw::c_void;
use std::sync::RwLock;

use exonum::runtime::ArtifactId;
use exonum_merkledb::Snapshot;

use super::{
    errors::PythonRuntimeResult,
    pending_deployment::PendingDeployment,
    types::{
        RawArtifactId, RawArtifactProtobufSpec, RawCallInfo, RawExecutionContext, RawIndexAccess,
        RawInstanceSpec, RawStateHashAggregator,
    },
};

lazy_static! {
    pub(crate) static ref PYTHON_INTERFACE: RwLock<PythonRuntimeInterface> =
        RwLock::new(PythonRuntimeInterface::default());

    // This variable (once DB is available) stores the snapshot of the current block
    // so API calls on the Python side can access the database.
    pub(crate) static ref BLOCK_SNAPSHOT: RwLock<Option<Box<dyn Snapshot>>> =
        RwLock::new(Default::default());
}

// Constant object that will be used by python side that
// it wants to access database to process API request.
const SNAPSHOT_TOKEN: RawIndexAccess = RawIndexAccess::SnapshotToken;

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
}

// Types of the stored functions.
type PythonDeployArtifactMethod =
    unsafe extern "C" fn(artifact: RawArtifactId, spec: *const u8, spec_len: u64) -> u8;
type PythonIsArtifactDeployedMethod = unsafe extern "C" fn(artifact: RawArtifactId) -> bool;
type PythonRestartServiceMethod = unsafe extern "C" fn(spec: RawInstanceSpec) -> u8;
type PythonAddServiceMethod = unsafe extern "C" fn(
    fork: *const RawIndexAccess,
    descriptor: RawInstanceSpec,
    parameters: *const u8,
    parameters_len: u64,
) -> u8;
type PythonExecuteMethod = unsafe extern "C" fn(
    context: RawExecutionContext,
    call_info: RawCallInfo,
    payload: *const u8,
    payload_len: u32,
) -> u8;
type PythonArtifactProtobufSpecMethod =
    unsafe extern "C" fn(_id: RawArtifactId, _spec: *const *mut RawArtifactProtobufSpec);
type PythonStateHashesMethod = unsafe extern "C" fn(
    fork: *const RawIndexAccess,
    _aggregator: *const *mut RawStateHashAggregator,
);
type PythonBeforeCommitMethod = unsafe extern "C" fn(fork: *const RawIndexAccess);
type PythonAfterCommitMethod = unsafe extern "C" fn(fork: *const RawIndexAccess);
type PythonFreeResourceMethod = unsafe extern "C" fn(resource: *const c_void);

/// Structure with the Python side API.
#[repr(C)]
#[derive(Clone, Copy)]
pub struct PythonMethods {
    pub deploy_artifact: PythonDeployArtifactMethod,
    pub is_artifact_deployed: PythonIsArtifactDeployedMethod,
    pub restart_service: PythonRestartServiceMethod,
    pub add_service: PythonAddServiceMethod,
    pub execute: PythonExecuteMethod,
    pub artifact_protobuf_spec: PythonArtifactProtobufSpecMethod,
    pub state_hashes: PythonStateHashesMethod,
    pub before_commit: PythonBeforeCommitMethod,
    pub after_commit: PythonAfterCommitMethod,
    pub free_resource: PythonFreeResourceMethod,
}

impl std::fmt::Debug for PythonMethods {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("PythonMethods").finish()
    }
}

impl Default for PythonMethods {
    // By default we have blank implementations of the functions.
    // When Python side will be initialized, it will provide actual
    // methods.
    fn default() -> Self {
        Self {
            deploy_artifact: default_deploy,
            is_artifact_deployed: default_is_artifact_deployed,
            restart_service: default_restart_service,
            add_service: default_add_service_method,
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
fn deployment_completed(python_artifact: RawArtifactId, result: u8) {
    let artifact = ArtifactId::from(python_artifact);
    let mut python_interface = PYTHON_INTERFACE.write().expect("Excepted write");

    let future = python_interface.ongoing_deployments.remove(&artifact);

    match future {
        Some(mut f) => match PythonRuntimeResult::from_value(result) {
            Ok(()) => {
                f.complete();
            }
            Err(error) => {
                f.error(error);
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

/// Returns a pointer to the Snapshot token for API requests.
#[no_mangle]
pub unsafe extern "C" fn get_snapshot_token() -> *const RawIndexAccess<'static> {
    &SNAPSHOT_TOKEN as *const RawIndexAccess
}

// Blank implementations to avoid storing `Option`.

unsafe extern "C" fn default_deploy(
    _artifact: RawArtifactId,
    _spec: *const u8,
    _spec_len: u64,
) -> u8 {
    PythonRuntimeResult::RuntimeNotReady as u8
}

unsafe extern "C" fn default_is_artifact_deployed(_artifact: RawArtifactId) -> bool {
    false
}

unsafe extern "C" fn default_restart_service(_spec: RawInstanceSpec) -> u8 {
    PythonRuntimeResult::RuntimeNotReady as u8
}

unsafe extern "C" fn default_add_service_method(
    _fork: *const RawIndexAccess,
    _descriptor: RawInstanceSpec,
    _parameters: *const u8,
    _parameters_len: u64,
) -> u8 {
    PythonRuntimeResult::RuntimeNotReady as u8
}

unsafe extern "C" fn default_execute_method(
    _context: RawExecutionContext,
    _call_info: RawCallInfo,
    _payload: *const u8,
    _payload_len: u32,
) -> u8 {
    PythonRuntimeResult::RuntimeNotReady as u8
}
unsafe extern "C" fn default_artifact_protobuf_spec_method(
    _id: RawArtifactId,
    _spec: *const *mut RawArtifactProtobufSpec,
) {
}
unsafe extern "C" fn default_state_hashes_method(
    _fork: *const RawIndexAccess,
    _aggregator: *const *mut RawStateHashAggregator,
) {
}
unsafe extern "C" fn default_before_commit_method(_fork: *const RawIndexAccess) {}
unsafe extern "C" fn default_after_commit_method(_fork: *const RawIndexAccess) {}
unsafe extern "C" fn default_free_resource_method(_resource: *const c_void) {}
