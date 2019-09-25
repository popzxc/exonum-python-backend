use std::os::raw::c_char;

use exonum::runtime::{ArtifactId, InstanceSpec};

#[repr(C)]
pub struct PythonArtifactId {
    pub runtime_id: u32,
    pub name: *const c_char,
}

impl PythonArtifactId {
    pub unsafe fn from_artifact_id(artifact: &ArtifactId) -> PythonArtifactId {
        // This function isn't unsafe in the terms of language, but logically it is.
        let artifact_name = artifact.name.as_ptr() as *const c_char;
        PythonArtifactId {
            runtime_id: artifact.runtime_id,
            name: artifact_name,
        }
    }
}

pub unsafe fn into_ptr_and_len(data: &[u8]) -> (*const u8, usize) {
    let data_ptr: *const u8 = data.as_ptr();
    let data_len = data.len();

    (data_ptr, data_len)
}

#[repr(C)]
pub struct PythonInstanceSpec {
    pub name: *const c_char,
    pub artifact: PythonArtifactId,
}

impl PythonInstanceSpec {
    pub unsafe fn from_instance_spec(instance_spec: &InstanceSpec) -> PythonInstanceSpec {
        let name = instance_spec.name.as_ptr() as *const c_char;

        PythonInstanceSpec {
            name,
            artifact: PythonArtifactId::from_artifact_id(&instance_spec.artifact),
        }
    }
}