use std::ffi::CStr;
use std::os::raw::c_char;

use exonum::runtime::{ArtifactId, InstanceSpec};

#[repr(C)]
pub struct RawResult {
    pub success: bool,
    pub error_code: u32,
}

#[repr(C)]
pub struct RawArtifactId {
    pub runtime_id: u32,
    pub name: *const c_char,
}

impl RawArtifactId {
    pub unsafe fn from_artifact_id(artifact: &ArtifactId) -> RawArtifactId {
        // This function isn't unsafe in the terms of language, but logically it is.
        let artifact_name = artifact.name.as_ptr() as *const c_char;
        RawArtifactId {
            runtime_id: artifact.runtime_id,
            name: artifact_name,
        }
    }
}

impl From<RawArtifactId> for ArtifactId {
    fn from(python_artifact: RawArtifactId) -> ArtifactId {
        let artifact_name = unsafe {
            CStr::from_ptr(python_artifact.name)
                .to_string_lossy()
                .into_owned()
        };

        ArtifactId {
            name: artifact_name,
            runtime_id: python_artifact.runtime_id,
        }
    }
}

pub unsafe fn into_ptr_and_len(data: &[u8]) -> (*const u8, usize) {
    let data_ptr: *const u8 = data.as_ptr();
    let data_len = data.len();

    (data_ptr, data_len)
}

#[repr(C)]
pub struct RawInstanceSpec {
    pub name: *const c_char,
    pub artifact: RawArtifactId,
}

impl RawInstanceSpec {
    pub unsafe fn from_instance_spec(instance_spec: &InstanceSpec) -> RawInstanceSpec {
        let name = instance_spec.name.as_ptr() as *const c_char;

        RawInstanceSpec {
            name,
            artifact: RawArtifactId::from_artifact_id(&instance_spec.artifact),
        }
    }
}
