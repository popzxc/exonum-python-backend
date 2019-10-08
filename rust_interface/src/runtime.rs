use std::os::raw::c_void;
use std::sync::RwLock;

use futures::{Future, IntoFuture};
// use sysinfo::{Pid, ProcessExt, ProcessStatus, RefreshKind, System, SystemExt};

use exonum::{
    api::ApiContext,
    crypto::{PublicKey, SecretKey},
    node::ApiSender,
    runtime::{
        dispatcher::{DispatcherRef, DispatcherSender},
        ApiChange, ArtifactId, ArtifactProtobufSpec, CallInfo, ExecutionContext, ExecutionError,
        InstanceDescriptor, InstanceSpec, Runtime, StateHashAggregator,
    },
};
use exonum_merkledb::{Fork, Snapshot};

use super::{
    errors::PythonRuntimeResult,
    pending_deployment::PendingDeployment,
    python_interface::{BLOCK_SNAPSHOT, PYTHON_INTERFACE},
    types::{
        convert_string, into_ptr_and_len, RawArtifactId, RawArtifactProtobufSpec, RawCallInfo,
        RawExecutionContext, RawIndexAccess, RawInstanceDescriptor, RawInstanceSpec,
        RawStateHashAggregator,
    },
};

/// Sample runtime.
#[derive(Debug, Default)]
pub struct PythonRuntime {
    api_context: RwLock<Option<ApiContext>>,
}

impl PythonRuntime {
    /// Runtime identifier for the python runtime.
    const ID: u32 = 2;

    pub fn new() -> Self {
        Default::default()
    }

    /// Checks that process is still running.
    fn ensure_runtime(&self) -> Result<(), ExecutionError> {
        Ok(())
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

        info!("Deploy request of the artifact {}", artifact.name);

        let mut python_interface = PYTHON_INTERFACE.write().expect("Interface read");

        // Call the python side of `deploy_artifact`.
        let result = unsafe {
            let artifact_name = convert_string(&artifact.name);

            let python_artifact_id = RawArtifactId::from_artifact_id(&artifact, &artifact_name);
            let (spec_bytes_ptr, spec_bytes_len) = into_ptr_and_len(&spec);
            (python_interface.methods.deploy_artifact)(
                python_artifact_id,
                spec_bytes_ptr,
                spec_bytes_len as u64,
            )
        };

        // Look at the result.
        match PythonRuntimeResult::from_value(result) {
            Ok(()) => {
                // Everything is ok, deployment started, create a future and return it.
                let deployment_future = PendingDeployment::new();

                python_interface.notify_deployment_started(artifact, deployment_future.clone());

                Box::new(deployment_future)
            }
            Err(error) => {
                // Something went wrong on the initial stage, did not even stert.
                Box::new(Err(error).into_future())
            }
        }
    }

    fn is_artifact_deployed(&self, id: &ArtifactId) -> bool {
        if self.ensure_runtime().is_err() {
            return false;
        }

        let python_interface = PYTHON_INTERFACE.read().expect("Interface read");

        unsafe {
            let artifact_name = convert_string(&id.name);
            let python_artifact_id = RawArtifactId::from_artifact_id(id, &artifact_name);
            (python_interface.methods.is_artifact_deployed)(python_artifact_id)
        }
    }

    fn start_service(&mut self, spec: &InstanceSpec) -> Result<(), ExecutionError> {
        self.ensure_runtime()?;

        let python_interface = PYTHON_INTERFACE.read().expect("Interface read");

        let result = unsafe {
            let artifact_name = convert_string(&spec.artifact.name);
            let instance_name = convert_string(&spec.name);
            let python_instance_spec =
                RawInstanceSpec::from_instance_spec(spec, &instance_name, &artifact_name);

            (python_interface.methods.start_service)(python_instance_spec)
        };

        PythonRuntimeResult::from_value(result)
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
            let name = convert_string(descriptor.name);

            let python_instance_descriptor =
                RawInstanceDescriptor::from_instance_descriptor(&descriptor, &name);

            let access = RawIndexAccess::Fork(fork);

            let (parameters_bytes_ptr, parameters_bytes_len) = into_ptr_and_len(&parameters);
            (python_interface.methods.initialize_service)(
                &access as *const RawIndexAccess,
                python_instance_descriptor,
                parameters_bytes_ptr,
                parameters_bytes_len as u64,
            )
        };

        PythonRuntimeResult::from_value(result)
    }

    fn stop_service(&mut self, descriptor: InstanceDescriptor) -> Result<(), ExecutionError> {
        self.ensure_runtime()?;

        let python_interface = PYTHON_INTERFACE.read().expect("Interface read");

        let result = unsafe {
            let name = convert_string(descriptor.name);
            let python_instance_descriptor =
                RawInstanceDescriptor::from_instance_descriptor(&descriptor, &name);

            (python_interface.methods.stop_service)(python_instance_descriptor)
        };

        PythonRuntimeResult::from_value(result)
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

            let interface_name = convert_string(context.interface_name);

            let python_execution_context = RawExecutionContext::from_execution_context(
                context,
                &access as *const RawIndexAccess,
                &interface_name,
            );
            let python_call_info = RawCallInfo::from_call_info(call_info);

            (python_interface.methods.execute)(
                python_execution_context,
                python_call_info,
                payload_bytes_ptr,
                payload_bytes_len as u32,
            )
        };

        PythonRuntimeResult::from_value(result)
    }

    fn artifact_protobuf_spec(&self, id: &ArtifactId) -> Option<ArtifactProtobufSpec> {
        self.ensure_runtime().ok()?;
        let python_interface = PYTHON_INTERFACE.read().expect("Interface read");

        unsafe {
            let artifact_name = convert_string(&id.name);
            let python_artifact_id = RawArtifactId::from_artifact_id(id, &artifact_name);
            let mut raw_protobuf_spec_ptr: *mut RawArtifactProtobufSpec =
                std::ptr::null::<RawArtifactProtobufSpec>() as *mut RawArtifactProtobufSpec;

            (python_interface.methods.artifact_protobuf_spec)(
                python_artifact_id,
                &mut raw_protobuf_spec_ptr as *mut *mut RawArtifactProtobufSpec,
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
            let mut raw_state_hash_aggregator_ptr: *mut RawStateHashAggregator =
                std::ptr::null::<RawStateHashAggregator>() as *mut RawStateHashAggregator;

            let access = RawIndexAccess::Snapshot(snapshot);

            (python_interface.methods.state_hashes)(
                &access as *const RawIndexAccess,
                &mut raw_state_hash_aggregator_ptr as *mut *mut RawStateHashAggregator,
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

        // Update the stored snapshot.
        if let Some(ref api_context) = self.api_context.read().expect("Database read").as_ref() {
            let mut snapshot = BLOCK_SNAPSHOT.write().expect("Block snapshot write");
            *snapshot = Some(api_context.snapshot());
        }

        // Call `after_commit` on the python side.

        let python_interface = PYTHON_INTERFACE.read().expect("Interface read");

        unsafe {
            let access = RawIndexAccess::Snapshot(snapshot);

            (python_interface.methods.before_commit)(&access as *const RawIndexAccess);
        }
    }

    fn notify_api_changes(&self, context: &ApiContext, _changes: &[ApiChange]) {
        // If we've not received a context yet, store it
        // so API calls will be able to get a snapshot.
        if self.api_context.read().expect("Database read").is_none() {
            let mut api_context = self.api_context.write().expect("Database write");

            *api_context = Some(context.clone());
        }
    }
}

impl From<PythonRuntime> for (u32, Box<dyn Runtime>) {
    fn from(inner: PythonRuntime) -> Self {
        (PythonRuntime::ID, Box::new(inner))
    }
}
