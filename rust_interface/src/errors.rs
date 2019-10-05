use exonum::runtime::{ErrorKind, ExecutionError};

/// Enum representing common python runtime errors.
#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub enum PythonRuntimeResult {
    /// Operation completed successfully.
    Ok = 0,

    /// PythonRuntime is not ready yet for work.
    RuntimeNotReady = 1,

    /// PythonRuntime process is dead.
    RuntimeDead = 2,

    /// Python artifact spec is incorrect.
    WrongSpec = 16,

    /// Error occured during deployment process.
    ServiceInstallFailed = 17,

    /// Undefined kind of runtime error.
    /// Receiving that kind of error probably means that something wrong with runtime implementation.
    Other = 64,

    /// Service errors are beginning from the code 65.
    Service = 65,
}

impl PythonRuntimeResult {
    pub fn from_value(value: u8) -> Result<(), ExecutionError> {
        let runtime_error = |x: u8| ErrorKind::runtime(x);

        // Service error codes are starting from 65, so we have to substract it
        // to get actual error code.
        let service_error = |x: u8| ErrorKind::service((x - Self::Service as u8) as u8);

        let (kind, description): (&dyn Fn(u8) -> ErrorKind, String) = match value {
            // No error.
            code if code == Self::Ok as u8 => return Ok(()),

            // Runtime errors on the Rust side.
            code if code == Self::RuntimeNotReady as u8 => {
                (&runtime_error, "Python runtime is not initialized".into())
            }
            code if code == Self::RuntimeDead as u8 => (
                &runtime_error,
                "Python runtime process is terminated".into(),
            ),

            // Reserved error codes on the Rust side.
            // Receiving that kind of error means that probably some kind of error
            // was not added into this enum.
            code if ((Self::RuntimeDead as u8 + 1)..(Self::WrongSpec as u8)).contains(&code) => (
                &runtime_error,
                format!(
                    "Unknown error code {} on the Rust side of Python Runtime",
                    code
                ),
            ),

            // Runtime errors on the Python side.
            code if code == Self::WrongSpec as u8 => {
                (&runtime_error, "Incorrect Python artifact spec".into())
            }
            code if code == Self::ServiceInstallFailed as u8 => {
                (&runtime_error, "Service installation failed".into())
            }

            // Reserved error codes on the Python side.
            // Receiving that kind of error means that probably some kind of error
            // was not added into this enum.
            code if ((Self::ServiceInstallFailed as u8 + 1)..(Self::Other as u8))
                .contains(&code) =>
            {
                (
                    &runtime_error,
                    format!(
                        "Unkonwn error code {} on the Python side of Python runtime",
                        code
                    ),
                )
            }

            // Unspecified error type rised by the Python runtime.
            code if code == Self::Other as u8 => {
                (&runtime_error, "Unspecified runtime error".into())
            }

            // Service error.
            _ => {
                let msg = "Python Service execution error. Check service docs for description of this error code";
                (&service_error, msg.into())
            }
        };

        Err((kind(value), description).into())
    }
}
