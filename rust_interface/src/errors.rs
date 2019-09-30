use exonum_derive::IntoExecutionError;

/// Enum representing common python runtime errors.
#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd, IntoExecutionError)]
#[exonum(kind = "runtime")]
pub enum PythonRuntimeError {
    /// PythonRuntime is not ready yet for work.
    RuntimeNotReady = 1,

    /// PythonRuntime process is dead.
    RuntimeDead = 2,

    /// Undefined kind of error.
    /// Receiving that kind of error probably means that something wrong with runtime implementation.
    Other = 255,
}

impl PythonRuntimeError {
    pub fn from_value(value: u32) -> PythonRuntimeError {
        match value {
            0 => PythonRuntimeError::RuntimeNotReady,
            _ => PythonRuntimeError::Other,
        }
    }
}
