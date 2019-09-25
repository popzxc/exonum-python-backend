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
use exonum_derive::IntoExecutionError;
use exonum_merkledb::{BinaryValue, Fork, Snapshot};
use futures::{Future, IntoFuture};

use std::sync::RwLock;

use super::{
    python_interface::PythonRuntimeInterface,
    types::{into_ptr_and_len, PythonArtifactId, PythonInstanceSpec},
};

lazy_static! {
    static ref PYTHON_INTERFACE: RwLock<PythonRuntimeInterface> =
        RwLock::new(PythonRuntimeInterface::default());
}

/// Sample runtime.
#[derive(Debug)]
pub struct PythonRuntime;

// Define runtime specific errors.
#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd, IntoExecutionError)]
#[exonum(kind = "runtime")]
enum SampleRuntimeError {
    /// Unable to parse service configuration.
    ConfigParseError = 0,
    /// Incorrect information to call transaction.
    IncorrectCallInfo = 1,
    /// Incorrect transaction payload.
    IncorrectPayload = 2,
}

impl PythonRuntime {
    /// Runtime identifier for the python runtime.
    const ID: u32 = 2;
}

impl PythonRuntime {
    pub fn on_artifact_deployed(&mut self, _artifact: PythonArtifactId) {
        // TODO
    }
}

// const ERROR_PYTHON_INTERFACE_NOT_READY: u8 = 0;

impl Runtime for PythonRuntime {
    /// TODO
    fn deploy_artifact(
        &mut self,
        artifact: ArtifactId,
        spec: Any,
    ) -> Box<dyn Future<Item = (), Error = ExecutionError>> {
        let python_interface = PYTHON_INTERFACE.read().expect("Interface read");

        let spec_bytes = spec.to_bytes();

        let deploy_artifact_fn = python_interface.deploy_artifact;

        unsafe {
            let python_artifact_id = PythonArtifactId::from_artifact_id(&artifact);
            let (spec_bytes_ptr, spec_bytes_len) = into_ptr_and_len(&spec_bytes);
            deploy_artifact_fn(python_artifact_id, spec_bytes_ptr, spec_bytes_len);
        }

        // TODO actually use a future
        let res: Result<(), ExecutionError> = Ok(());
        Box::new(res.into_future())
    }

    /// TODO
    fn is_artifact_deployed(&self, id: &ArtifactId) -> bool {
        let python_interface = PYTHON_INTERFACE.read().expect("Interface read");

        let is_artifact_deployed_fn = python_interface.is_artifact_deployed;
        unsafe {
            let python_artifact_id = PythonArtifactId::from_artifact_id(id);
            is_artifact_deployed_fn(python_artifact_id)
        }
    }

    /// TODO
    fn start_service(&mut self, spec: &InstanceSpec) -> Result<(), ExecutionError> {
        let python_interface = PYTHON_INTERFACE.read().expect("Interface read");

        let start_service_fn = python_interface.start_service;
        // TODO return either Ok or Err depending on python return value.
        unsafe {
            let python_instance_spec = PythonInstanceSpec::from_instance_spec(spec);

            start_service_fn(python_instance_spec);
            Ok(())
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
