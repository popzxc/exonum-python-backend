use exonum::{
    crypto::{PublicKey, SecretKey},
    node::ApiSender,
    proto::Any,
    runtime::{
        dispatcher::{Dispatcher, DispatcherSender, Error as DispatcherError},
        ArtifactId, ArtifactProtobufSpec, CallInfo, ExecutionContext, ExecutionError,
        InstanceDescriptor, InstanceSpec, Runtime, StateHashAggregator,
    },
};
use exonum_derive::IntoExecutionError;
use exonum_merkledb::{Fork, Snapshot};
use futures::{Future, IntoFuture};

use std::collections::btree_map::{BTreeMap, Entry};

use super::python_interface::PythonRuntimeInterface;

/// Sample runtime.
#[derive(Debug)]
struct PythonRuntime {
    python_backend: Option<PythonRuntimeInterface>,
    deployed_artifacts: BTreeMap<ArtifactId, Any>,
    // started_services: BTreeMap<InstanceId, SampleService>,
}

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

impl Runtime for PythonRuntime {
    /// TODO
    fn deploy_artifact(
        &mut self,
        artifact: ArtifactId,
        spec: Any,
    ) -> Box<dyn Future<Item = (), Error = ExecutionError>> {
        Box::new(
            match self.deployed_artifacts.entry(artifact) {
                Entry::Occupied(_) => Err(DispatcherError::ArtifactAlreadyDeployed),
                Entry::Vacant(entry) => {
                    println!("Deploying artifact: {}", entry.key());
                    entry.insert(spec);
                    Ok(())
                }
            }
            .map_err(ExecutionError::from)
            .into_future(),
        )
    }

    /// TODO
    fn is_artifact_deployed(&self, id: &ArtifactId) -> bool {
        self.deployed_artifacts.contains_key(id)
    }

    /// TODO
    fn start_service(&mut self, spec: &InstanceSpec) -> Result<(), ExecutionError> {
        if !self.deployed_artifacts.contains_key(&spec.artifact) {
            return Err(DispatcherError::ArtifactNotDeployed.into());
        }
        Ok(())
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
    fn artifact_protobuf_spec(&self, id: &ArtifactId) -> Option<ArtifactProtobufSpec> {
        self.deployed_artifacts
            .get(id)
            .map(|_| ArtifactProtobufSpec::default())
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
