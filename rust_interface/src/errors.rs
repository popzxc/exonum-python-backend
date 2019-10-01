use exonum_derive::IntoExecutionError;

/// Enum representing common python runtime errors.
#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd, IntoExecutionError)]
#[exonum(kind = "runtime")]
pub enum PythonRuntimeError {
    /// PythonRuntime is not ready yet for work.
    RuntimeNotReady = 1,

    /// PythonRuntime process is dead.
    RuntimeDead = 2,

    /// Python artifact spec is incorrect.
    WrongSpec = 16,

    /// Error occured during deployment process.
    ServiceInstallFailed = 17,

    /// Undefined kind of error.
    /// Receiving that kind of error probably means that something wrong with runtime implementation.
    Other = 255,
}

impl PythonRuntimeError {
    pub fn from_value(value: u32) -> PythonRuntimeError {
        match value {
            1 => PythonRuntimeError::RuntimeNotReady,
            2 => PythonRuntimeError::RuntimeDead,

            16 => PythonRuntimeError::WrongSpec,
            17 => PythonRuntimeError::ServiceInstallFailed,

            _ => PythonRuntimeError::Other,
        }
    }
}
