use std::collections::BTreeMap;
use std::sync::RwLock;

use exonum::runtime::ArtifactId;

use super::{
    errors::PythonRuntimeError,
    pending_deployment::PendingDeployment,
    types::{PythonArtifactId, PythonInstanceSpec, PythonResult},
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
}

// Types of the stored functions.
type PythonDeployArtifactMethod = unsafe extern "C" fn(
    artifact: PythonArtifactId,
    spec: *const u8,
    spec_len: usize,
) -> PythonResult;
type PythonIsArtifactDeployedMethod = unsafe extern "C" fn(artifact: PythonArtifactId) -> bool;
type PythonStartServiceMethod = unsafe extern "C" fn(spec: PythonInstanceSpec) -> PythonResult;

/// Structure with the Python side API.
#[repr(C)]
#[derive(Debug)]
pub struct PythonMethods {
    pub deploy_artifact: PythonDeployArtifactMethod,
    pub is_artifact_deployed: PythonIsArtifactDeployedMethod,
    pub start_service: PythonStartServiceMethod,
}

impl Default for PythonMethods {
    fn default() -> Self {
        Self {
            deploy_artifact: default_deploy,
            is_artifact_deployed: default_is_artifact_deployed,
            start_service: default_start_service,
        }
    }
}

/// Initialize python interfaces.
/// This function is meant to be called by the python side during the initialization.
#[no_mangle]
fn init_python_side(methods: PythonMethods) {
    let mut python_interface = PYTHON_INTERFACE.write().expect("Excepted write");

    (*python_interface).methods = methods;
}

/// Removes an artifact from the pending deployments.
/// This function is meant to be called by the python after the deployment of the artifact.
#[no_mangle]
fn deployment_completed(python_artifact: PythonArtifactId, result: PythonResult) {
    let artifact = ArtifactId::from(python_artifact);
    let mut python_interface = PYTHON_INTERFACE.write().expect("Excepted write");

    let future = python_interface.ongoing_deployments.remove(&artifact);

    match future {
        Some(mut f) => {
            if result.success {
                f.comlpete();
            } else {
                f.error(PythonRuntimeError::from_value(result.error_code).into());
            }
        }
        None => {
            panic!(
                "Python deployed an artifact that wasn't expected: {:?}",
                artifact
            );
        }
    }
}

unsafe extern "C" fn default_deploy(
    _artifact: PythonArtifactId,
    _spec: *const u8,
    _spec_len: usize,
) -> PythonResult {
    PythonResult {
        success: false,
        error_code: PythonRuntimeError::RuntimeNotReady as u32,
    }
}

unsafe extern "C" fn default_is_artifact_deployed(_artifact: PythonArtifactId) -> bool {
    false
}

unsafe extern "C" fn default_start_service(_spec: PythonInstanceSpec) -> PythonResult {
    PythonResult {
        success: false,
        error_code: PythonRuntimeError::RuntimeNotReady as u32,
    }
}
