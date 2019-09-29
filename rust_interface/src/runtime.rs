use futures::{Future, IntoFuture};

use exonum::{
    crypto::{PublicKey, SecretKey},
    node::ApiSender,
    proto::Any,
    runtime::{
        dispatcher::{Dispatcher, DispatcherSender},
        ArtifactId, ArtifactProtobufSpec, CallInfo, ExecutionContext, ExecutionError,
        InstanceDescriptor, InstanceSpec, Runtime, StateHashAggregator,
    },
};
use exonum_merkledb::{BinaryValue, Fork, Snapshot};

use super::{
    errors::PythonRuntimeError,
    pending_deployment::PendingDeployment,
    python_interface::PYTHON_INTERFACE,
    types::{into_ptr_and_len, RawArtifactId, RawInstanceSpec},
};

/// Sample runtime.
#[derive(Debug)]
pub struct PythonRuntime;

impl PythonRuntime {
    /// Runtime identifier for the python runtime.
    const ID: u32 = 2;
}

impl Runtime for PythonRuntime {
    /// TODO
    fn deploy_artifact(
        &mut self,
        artifact: ArtifactId,
        spec: Any,
    ) -> Box<dyn Future<Item = (), Error = ExecutionError>> {
        let mut python_interface = PYTHON_INTERFACE.write().expect("Interface read");

        let spec_bytes = spec.to_bytes();

        // Call the python side of `deploy_artifact`.
        let result = unsafe {
            let python_artifact_id = RawArtifactId::from_artifact_id(&artifact);
            let (spec_bytes_ptr, spec_bytes_len) = into_ptr_and_len(&spec_bytes);
            (python_interface.methods.deploy_artifact)(
                python_artifact_id,
                spec_bytes_ptr,
                spec_bytes_len as u64,
            )
        };

        // Look at the result.
        if result.success {
            // Everything is ok, deployment started, create a future and return it.
            let deployment_future = PendingDeployment::new();

            python_interface.notify_deployment_started(artifact, deployment_future.clone());

            Box::new(deployment_future)
        } else {
            // Something went wrong on the initial stage, did not even stert.
            let error = PythonRuntimeError::from_value(result.error_code);

            Box::new(Err(error.into()).into_future())
        }
    }

    /// TODO
    fn is_artifact_deployed(&self, id: &ArtifactId) -> bool {
        let python_interface = PYTHON_INTERFACE.read().expect("Interface read");

        unsafe {
            let python_artifact_id = RawArtifactId::from_artifact_id(id);
            (python_interface.methods.is_artifact_deployed)(python_artifact_id)
        }
    }

    /// TODO
    fn start_service(&mut self, spec: &InstanceSpec) -> Result<(), ExecutionError> {
        let python_interface = PYTHON_INTERFACE.read().expect("Interface read");

        let result = unsafe {
            let python_instance_spec = RawInstanceSpec::from_instance_spec(spec);

            (python_interface.methods.start_service)(python_instance_spec)
        };

        if result.success {
            Ok(())
        } else {
            Err(PythonRuntimeError::from_value(result.error_code).into())
        }
    }

    /// TODO
    fn configure_service(
        &self,
        _context: &Fork,
        _descriptor: InstanceDescriptor,
        _parameters: Any,
    ) -> Result<(), ExecutionError> {
        Ok(())
    }

    /// TODO
    fn stop_service(&mut self, _descriptor: InstanceDescriptor) -> Result<(), ExecutionError> {
        Ok(())
    }

    /// TODO
    fn execute(
        &self,
        _context: &ExecutionContext,
        _call_info: &CallInfo,
        _payload: &[u8],
    ) -> Result<(), ExecutionError> {
        Ok(())
    }

    /// TODO
    fn artifact_protobuf_spec(&self, _id: &ArtifactId) -> Option<ArtifactProtobufSpec> {
        // self.deployed_artifacts
        //     .get(id)
        //     .map(|_| ArtifactProtobufSpec::default())
        None
    }

    /// TODO
    fn state_hashes(&self, _snapshot: &dyn Snapshot) -> StateHashAggregator {
        StateHashAggregator::default()
    }

    /// TODO
    fn before_commit(&self, _dispatcher: &Dispatcher, _fork: &mut Fork) {}

    /// TODO
    fn after_commit(
        &self,
        _dispatcher: &DispatcherSender,
        _snapshot: &dyn Snapshot,
        _service_keypair: &(PublicKey, SecretKey),
        _tx_sender: &ApiSender,
    ) {
    }
}

impl From<PythonRuntime> for (u32, Box<dyn Runtime>) {
    fn from(inner: PythonRuntime) -> Self {
        (PythonRuntime::ID, Box::new(inner))
    }
}
