use std::os::raw::c_void;
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
    types::{
        into_ptr_and_len, RawArtifactId, RawArtifactProtobufSpec, RawCallInfo, RawExecutionContext,
        RawIndexAccess, RawInstanceDescriptor, RawInstanceSpec, RawStateHashAggregator,
    },
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

    fn start_service(&mut self, spec: &InstanceSpec) -> Result<(), ExecutionError> {
        self.ensure_runtime()?;

        let python_interface = PYTHON_INTERFACE.read().expect("Interface read");

        let result = unsafe {
            let python_instance_spec = RawInstanceSpec::from_instance_spec(spec);

            (python_interface.methods.start_service)(python_instance_spec)
        };

        PythonRuntimeInterface::error_code_to_result(result).map_err(From::from)
    }

    fn initialize_service(
        &self,
        fork: &Fork,
        descriptor: InstanceDescriptor,
        parameters: Vec<u8>,
    ) -> Result<(), ExecutionError> {
        self.ensure_runtime()?;

        let python_interface = PYTHON_INTERFACE.read().expect("Interface read");

        let result = unsafe {
            let python_instance_descriptor =
                RawInstanceDescriptor::from_instance_descriptor(&descriptor);

            let access = RawIndexAccess::Fork(fork);

            let (parameters_bytes_ptr, parameters_bytes_len) = into_ptr_and_len(&parameters);
            (python_interface.methods.initialize_service)(
                &access as *const RawIndexAccess,
                python_instance_descriptor,
                parameters_bytes_ptr,
                parameters_bytes_len as u64,
            )
        };

        PythonRuntimeInterface::error_code_to_result(result).map_err(From::from)
    }

    fn stop_service(&mut self, descriptor: InstanceDescriptor) -> Result<(), ExecutionError> {
        self.ensure_runtime()?;

        let python_interface = PYTHON_INTERFACE.read().expect("Interface read");

        let result = unsafe {
            let python_instance_descriptor =
                RawInstanceDescriptor::from_instance_descriptor(&descriptor);

            (python_interface.methods.stop_service)(python_instance_descriptor)
        };

        PythonRuntimeInterface::error_code_to_result(result).map_err(From::from)
    }

    fn execute(
        &self,
        context: &ExecutionContext,
        call_info: &CallInfo,
        payload: &[u8],
    ) -> Result<(), ExecutionError> {
        self.ensure_runtime()?;

        let python_interface = PYTHON_INTERFACE.read().expect("Interface read");

        let result = unsafe {
            let (payload_bytes_ptr, payload_bytes_len) = into_ptr_and_len(&payload);

            let access = RawIndexAccess::Fork(context.fork);

            let python_execution_context = RawExecutionContext::from_execution_context(
                context,
                &access as *const RawIndexAccess,
            );
            let python_call_info = RawCallInfo::from_call_info(call_info);

            (python_interface.methods.execute)(
                python_execution_context,
                python_call_info,
                payload_bytes_ptr,
                payload_bytes_len as u32,
            )
        };

        PythonRuntimeInterface::error_code_to_result(result).map_err(From::from)
    }

    fn artifact_protobuf_spec(&self, id: &ArtifactId) -> Option<ArtifactProtobufSpec> {
        self.ensure_runtime().ok()?;
        let python_interface = PYTHON_INTERFACE.read().expect("Interface read");

        unsafe {
            let python_artifact_id = RawArtifactId::from_artifact_id(id);
            let raw_protobuf_spec_ptr: *mut RawArtifactProtobufSpec =
                std::ptr::null::<RawArtifactProtobufSpec>() as *mut RawArtifactProtobufSpec;

            (python_interface.methods.artifact_protobuf_spec)(
                python_artifact_id,
                &raw_protobuf_spec_ptr as *const *mut RawArtifactProtobufSpec,
            );

            // Pointer will be nullptr if there is no protobuf spec for requested artifact.
            if raw_protobuf_spec_ptr
                != std::ptr::null::<RawArtifactProtobufSpec>() as *mut RawArtifactProtobufSpec
            {
                let spec = ArtifactProtobufSpec::from(*raw_protobuf_spec_ptr);

                // Python allocated resources for us, don't forget to free it.
                (python_interface.methods.free_resource)(raw_protobuf_spec_ptr as *const c_void);

                Some(spec)
            } else {
                None
            }
        }
    }

    fn state_hashes(&self, snapshot: &dyn Snapshot) -> StateHashAggregator {
        if self.ensure_runtime().is_err() {
            return StateHashAggregator::default();
        }

        let python_interface = PYTHON_INTERFACE.read().expect("Interface read");

        unsafe {
            let raw_state_hash_aggregator_ptr: *mut RawStateHashAggregator =
                std::ptr::null::<RawStateHashAggregator>() as *mut RawStateHashAggregator;

            let access = RawIndexAccess::Snapshot(snapshot);

            (python_interface.methods.state_hashes)(
                &access as *const RawIndexAccess,
                &raw_state_hash_aggregator_ptr as *const *mut RawStateHashAggregator,
            );

            // Check agains nullptr just in case.
            if raw_state_hash_aggregator_ptr
                != std::ptr::null::<RawStateHashAggregator>() as *mut RawStateHashAggregator
            {
                let state_hash_aggregator =
                    StateHashAggregator::from(*raw_state_hash_aggregator_ptr);

                // Python allocated resources for us, don't forget to free it.
                (python_interface.methods.free_resource)(
                    raw_state_hash_aggregator_ptr as *const c_void,
                );

                state_hash_aggregator
            } else {
                StateHashAggregator::default()
            }
        }
    }

    fn before_commit(&self, _dispatcher: &DispatcherRef, fork: &mut Fork) {
        if self.ensure_runtime().is_err() {
            return;
        }

        let python_interface = PYTHON_INTERFACE.read().expect("Interface read");

        unsafe {
            let access = RawIndexAccess::Fork(fork);

            (python_interface.methods.before_commit)(&access as *const RawIndexAccess);
        }
    }

    /// TODO
    fn after_commit(
        &self,
        _dispatcher: &DispatcherSender,
        snapshot: &dyn Snapshot,
        _service_keypair: &(PublicKey, SecretKey),
        _tx_sender: &ApiSender,
    ) {
        if self.ensure_runtime().is_err() {
            return;
        }

        let python_interface = PYTHON_INTERFACE.read().expect("Interface read");

        unsafe {
            let access = RawIndexAccess::Snapshot(snapshot);

            (python_interface.methods.before_commit)(&access as *const RawIndexAccess);
        }
    }
}

impl From<PythonRuntime> for (u32, Box<dyn Runtime>) {
    fn from(inner: PythonRuntime) -> Self {
        (PythonRuntime::ID, Box::new(inner))
    }
}
