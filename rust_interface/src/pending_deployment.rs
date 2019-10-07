use futures::{
    task::{current, Task},
    Async, Future, Poll,
};
use std::sync::{Arc, RwLock};

use exonum::runtime::ExecutionError;

type DeploymentStatus = Option<Result<(), ExecutionError>>;
type RwLockArc<T> = Arc<RwLock<T>>;

#[derive(Clone, Default, Debug)]
pub struct PendingDeployment {
    result: RwLockArc<DeploymentStatus>,
    task: RwLockArc<Option<Task>>,
}

impl PendingDeployment {
    pub fn new() -> Self {
        Self {
            result: Arc::new(RwLock::new(None)),
            task: Arc::new(RwLock::new(None)),
        }
    }

    pub fn complete(&mut self) {
        *self.result.write().expect("Expected write lock") = Some(Ok(()));

        if let Some(ref task) = self.task.read().expect("Expected read lock").as_ref() {
            task.notify();
        }
    }

    pub fn error(&mut self, err: ExecutionError) {
        *self.result.write().expect("Expected write lock") = Some(Err(err));

        if let Some(ref task) = self.task.read().expect("Expected read lock").as_ref() {
            task.notify();
        }
    }
}

impl Future for PendingDeployment {
    type Item = ();
    type Error = ExecutionError;

    fn poll(&mut self) -> Poll<Self::Item, Self::Error> {
        match *self.result.read().expect("Expected read lock") {
            Some(Ok(_)) => Ok(Async::Ready(())),
            Some(Err(ref err)) => Err(err.clone()),
            None => {
                *self.task.write().expect("Expected write lock") = Some(current());
                Ok(Async::NotReady)
            }
        }
    }
}
