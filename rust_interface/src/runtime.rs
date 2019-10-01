use std::process::Child;

use futures::{Future, IntoFuture};
use sysinfo::{Pid, ProcessExt, ProcessStatus, RefreshKind, System, SystemExt};

use exonum::{
    crypto::{PublicKey, SecretKey},
    node::ApiSender,
    runtime::{
        dispatcher::{DispatcherRef, DispatcherSender},
        ArtifactId, ArtifactProtobufSpec, CallInfo, ExecutionContext, ExecutionError,
        InstanceDescriptor, InstanceSpec, Runtime, StateHashAggregator,
    },
};
use exonum_merkledb::{Fork, Snapshot};

use super::{
    errors::PythonRuntimeError,
    pending_deployment::PendingDeployment,
    python_interface::{PythonRuntimeInterface, PYTHON_INTERFACE},
    types::{into_ptr_and_len, RawArtifactId, RawInstanceDescriptor, RawInstanceSpec},
};

/// Sample runtime.
#[derive(Debug)]
pub struct PythonRuntime {
    python_process: Child,
    process_pid: Pid,
}

impl PythonRuntime {
    /// Runtime identifier for the python runtime.
    const ID: u32 = 2;

    pub fn new(python_process: Child) -> Self {
        let process_pid: Pid = python_process.id() as Pid;

        Self {
            python_process,
            process_pid,
        }
    }

    /// Checks that process is still running.
    fn ensure_runtime(&self) -> Result<(), ExecutionError> {
        let mut system = System::new_with_specifics(RefreshKind::new());;

        system.refresh_process(self.process_pid);

        let process = system
            .get_process(self.process_pid)
            .ok_or_else(|| ExecutionError::from(PythonRuntimeError::RuntimeDead))?;

        match process.status() {
            ProcessStatus::Run => Ok(()),
            _ => Err(ExecutionError::from(PythonRuntimeError::RuntimeDead)),
        }
    }
}

impl Runtime for PythonRuntime {
    /// TODO
    fn deploy_artifact(
        &mut self,
        artifact: ArtifactId,
        spec: Vec<u8>,
    ) -> Box<dyn Future<Item = (), Error = ExecutionError>> {
        match self.ensure_runtime() {
            Ok(()) => {}
            Err(e) => return Box::new(Err(e).into_future()),
        }

        let mut python_interface = PYTHON_INTERFACE.write().expect("Interface read");

        // Call the python side of `deploy_artifact`.
        let result = unsafe {
            let python_artifact_id = RawArtifactId::from_artifact_id(&artifact);
            let (spec_bytes_ptr, spec_bytes_len) = into_ptr_and_len(&spec);
            (python_interface.methods.deploy_artifact)(
                python_artifact_id,
                spec_bytes_ptr,
                spec_bytes_len as u64,
            )
        };

        // Look at the result.
        match PythonRuntimeInterface::error_code_to_result(result) {
            Ok(()) => {
                // Everything is ok, deployment started, create a future and return it.
                let deployment_future = PendingDeployment::new();

                python_interface.notify_deployment_started(artifact, deployment_future.clone());

                Box::new(deployment_future)
            }
            Err(error) => {
                // Something went wrong on the initial stage, did not even stert.
                Box::new(Err(error.into()).into_future())
            }
        }
    }

    /// TODO
    fn is_artifact_deployed(&self, id: &ArtifactId) -> bool {
        if self.ensure_runtime().is_err() {
            return false;
        }

        let python_interface = PYTHON_INTERFACE.read().expect("Interface read");

        unsafe {
            let python_artifact_id = RawArtifactId::from_artifact_id(id);
            (python_interface.methods.is_artifact_deployed)(python_artifact_id)
        }
    }

    /// TODO
    fn start_service(&mut self, spec: &InstanceSpec) -> Result<(), ExecutionError> {
        self.ensure_runtime()?;

        let python_interface = PYTHON_INTERFACE.read().expect("Interface read");

        let result = unsafe {
            let python_instance_spec = RawInstanceSpec::from_instance_spec(spec);

            (python_interface.methods.start_service)(python_instance_spec)
        };

        PythonRuntimeInterface::error_code_to_result(result).map_err(From::from)
    }

    /// TODO
    fn initialize_service(
        &self,
        _context: &Fork,
        descriptor: InstanceDescriptor,
        parameters: Vec<u8>,
    ) -> Result<(), ExecutionError> {
        self.ensure_runtime()?;

        let python_interface = PYTHON_INTERFACE.read().expect("Interface read");

        let result = unsafe {
            let python_instance_descriptor =
                RawInstanceDescriptor::from_instance_descriptor(&descriptor);

            let (parameters_bytes_ptr, parameters_bytes_len) = into_ptr_and_len(&parameters);
            (python_interface.methods.initialize_service)(
                python_instance_descriptor,
                parameters_bytes_ptr,
                parameters_bytes_len as u64,
            )
        };

        PythonRuntimeInterface::error_code_to_result(result).map_err(From::from)
    }

    /// TODO
    fn stop_service(&mut self, _descriptor: InstanceDescriptor) -> Result<(), ExecutionError> {
        self.ensure_runtime()?;

        Ok(())
    }

    /// TODO
    fn execute(
        &self,
        _context: &ExecutionContext,
        _call_info: &CallInfo,
        _payload: &[u8],
    ) -> Result<(), ExecutionError> {
        self.ensure_runtime()?;

        Ok(())
    }

    /// TODO
    fn artifact_protobuf_spec(&self, _id: &ArtifactId) -> Option<ArtifactProtobufSpec> {
        self.ensure_runtime().ok()?;

        // self.deployed_artifacts
        //     .get(id)
        //     .map(|_| ArtifactProtobufSpec::default())
        None
    }

    /// TODO
    fn state_hashes(&self, _snapshot: &dyn Snapshot) -> StateHashAggregator {
        if self.ensure_runtime().is_err() {
            return StateHashAggregator::default();
        }

        StateHashAggregator::default()
    }

    /// TODO
    fn before_commit(&self, _dispatcher: &DispatcherRef, _fork: &mut Fork) {
        if self.ensure_runtime().is_err() {
            return;
        }
    }

    /// TODO
    fn after_commit(
        &self,
        _dispatcher: &DispatcherSender,
        _snapshot: &dyn Snapshot,
        _service_keypair: &(PublicKey, SecretKey),
        _tx_sender: &ApiSender,
    ) {
        if self.ensure_runtime().is_err() {
            return;
        }
    }
}

impl From<PythonRuntime> for (u32, Box<dyn Runtime>) {
    fn from(inner: PythonRuntime) -> Self {
        (PythonRuntime::ID, Box::new(inner))
    }
}
