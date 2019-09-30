use futures::{Async, Future, Poll};
use std::sync::{Arc, RwLock};

use exonum::runtime::ExecutionError;

type DeploymentStatus = Option<Result<(), ExecutionError>>;
type RwLockArc<T> = Arc<RwLock<T>>;

#[derive(Clone, Default, Debug)]
pub struct PendingDeployment {
    result: RwLockArc<DeploymentStatus>,
}

impl PendingDeployment {
    pub fn new() -> Self {
        Self {
            result: Arc::new(RwLock::new(None)),
        }
    }

    pub fn complete(&mut self) {
        *self.result.write().expect("Expected write lock") = Some(Ok(()));
    }

    pub fn error(&mut self, err: ExecutionError) {
        *self.result.write().expect("Expected write lock") = Some(Err(err));
    }
}

impl Future for PendingDeployment {
    type Item = ();
    type Error = ExecutionError;

    fn poll(&mut self) -> Poll<Self::Item, Self::Error> {
        match *self.result.read().expect("Expected read lock") {
            Some(Ok(_)) => Ok(Async::Ready(())),
            Some(Err(ref err)) => Err(err.clone()),
            None => Ok(Async::NotReady),
        }
    }
}
