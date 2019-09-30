use std::ffi::CStr;
use std::os::raw::c_char;

use exonum::runtime::{ArtifactId, CallInfo, InstanceDescriptor, InstanceSpec};

pub unsafe fn into_ptr_and_len(data: &[u8]) -> (*const u8, usize) {
    let data_ptr: *const u8 = data.as_ptr();
    let data_len = data.len();

    (data_ptr, data_len)
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

#[repr(C)]
pub struct RawInstanceSpec {
    pub id: u32,
    pub name: *const c_char,
    pub artifact: RawArtifactId,
}

impl RawInstanceSpec {
    pub unsafe fn from_instance_spec(instance_spec: &InstanceSpec) -> RawInstanceSpec {
        let name = instance_spec.name.as_ptr() as *const c_char;

        RawInstanceSpec {
            id: instance_spec.id,
            name,
            artifact: RawArtifactId::from_artifact_id(&instance_spec.artifact),
        }
    }
}

impl From<RawInstanceSpec> for InstanceSpec {
    fn from(instance_spec: RawInstanceSpec) -> InstanceSpec {
        let instance_name = unsafe {
            CStr::from_ptr(instance_spec.name)
                .to_string_lossy()
                .into_owned()
        };

        InstanceSpec {
            id: instance_spec.id,
            name: instance_name,
            artifact: ArtifactId::from(instance_spec.artifact),
        }
    }
}

#[repr(C)]
pub struct RawInstanceDescriptor {
    pub id: u32,
    pub name: *const c_char,
}

impl RawInstanceDescriptor {
    pub unsafe fn from_instance_descriptor(
        descriptor: &InstanceDescriptor,
    ) -> RawInstanceDescriptor {
        let name = descriptor.name.as_ptr() as *const c_char;

        RawInstanceDescriptor {
            name,
            id: descriptor.id,
        }
    }
}

#[repr(C)]
pub struct RawCallInfo {
    pub instance_id: u32,
    pub method_id: u32,
}

impl RawCallInfo {
    pub unsafe fn from_call_info(call_info: &CallInfo) -> RawCallInfo {
        RawCallInfo {
            instance_id: call_info.instance_id,
            method_id: call_info.method_id,
        }
    }
}

impl From<RawCallInfo> for CallInfo {
    fn from(call_info: RawCallInfo) -> CallInfo {
        CallInfo {
            instance_id: call_info.instance_id,
            method_id: call_info.method_id,
        }
    }
}
