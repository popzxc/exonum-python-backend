use std::ffi::{CStr, CString};
use std::os::raw::c_char;

use exonum::crypto::Hash;
use exonum::runtime::{
    ArtifactId, ArtifactProtobufSpec, CallInfo, Caller, ExecutionContext, InstanceId, InstanceSpec,
    ProtoSourceFile, StateHashAggregator,
};

use exonum_merkledb::{Fork, Snapshot};

pub unsafe fn into_ptr_and_len(data: &[u8]) -> (*const u8, usize) {
    let data_ptr: *const u8 = data.as_ptr();
    let data_len = data.len();

    (data_ptr, data_len)
}

pub fn convert_string(data: &str) -> CString {
    CString::new(data).expect("Unable to parse string")
}

#[repr(C)]
pub struct RawArtifactId {
    pub runtime_id: u32,
    pub name: *const c_char,
}

impl RawArtifactId {
    // This function isn't unsafe in the terms of language, but logically it is.
    pub unsafe fn from_artifact_id(
        artifact: &ArtifactId,
        artifact_name: &CString,
    ) -> RawArtifactId {
        RawArtifactId {
            runtime_id: artifact.runtime_id,
            name: artifact_name.as_ptr(),
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
    pub unsafe fn from_instance_spec(
        instance_spec: &InstanceSpec,
        instance_name: &CString,
        artifact_name: &CString,
    ) -> RawInstanceSpec {
        RawInstanceSpec {
            id: instance_spec.id,
            name: instance_name.as_ptr(),
            artifact: RawArtifactId::from_artifact_id(&instance_spec.artifact, artifact_name),
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
pub struct RawCaller {
    pub tx_type: u32,

    // Will be set if type is Transaction. Otherwise will be nullptr.
    pub hash: *const u8,
    pub author: *const u8,

    // Will be set if type is Service. Otherwise will be 0.
    pub instance_id: u32,
}

impl RawCaller {
    pub unsafe fn from_caller(caller: &Caller) -> RawCaller {
        match caller {
            Caller::Transaction {
                ref hash,
                ref author,
            } => RawCaller {
                tx_type: 0,
                hash: hash.as_ref().as_ptr(),
                author: author.as_ref().as_ptr(),
                instance_id: 0,
            },
            Caller::Service { instance_id } => RawCaller {
                tx_type: 1,
                hash: std::ptr::null::<u8>(),
                author: std::ptr::null::<u8>(),
                instance_id: *instance_id,
            },
        }
    }
}

#[repr(C)]
pub struct RawExecutionContext<'a> {
    pub access: *const RawIndexAccess<'a>,
    pub caller: RawCaller,
    pub interface_name: *const c_char,
    // TODO: store dispatcher ref for calling transactions.
}

impl<'a> RawExecutionContext<'a> {
    pub unsafe fn from_execution_context(
        context: &'a ExecutionContext,
        access: *const RawIndexAccess<'a>,
        interface_name: &CString,
    ) -> RawExecutionContext<'a> {
        RawExecutionContext {
            access,
            caller: RawCaller::from_caller(&context.caller),
            interface_name: interface_name.as_ptr(),
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

#[repr(C)]
#[derive(Clone, Copy)]
pub struct RawHash {
    pub data: *const u8,
}

impl From<RawHash> for Hash {
    fn from(raw_hash: RawHash) -> Hash {
        let slice = unsafe { std::slice::from_raw_parts(raw_hash.data, 32) };

        Hash::from_slice(slice).expect("Incorrect hash recieved from Python")
    }
}

#[repr(C)]
#[derive(Clone, Copy)]
pub struct RawStateHashAggregator {
    pub hashes: *const (*const RawHash),
    pub hashes_length: *const u32,
    pub instance_ids: *const u32,
    pub length: u32,
}

impl From<RawStateHashAggregator> for StateHashAggregator {
    fn from(raw_aggregator: RawStateHashAggregator) -> StateHashAggregator {
        let overall_length: usize = raw_aggregator.length as usize;
        let instances_length: usize = overall_length - 1;

        let hashes = unsafe { std::slice::from_raw_parts(raw_aggregator.hashes, overall_length) };
        let hashes_lengths =
            unsafe { std::slice::from_raw_parts(raw_aggregator.hashes_length, overall_length) };
        let instance_ids =
            unsafe { std::slice::from_raw_parts(raw_aggregator.instance_ids, instances_length) };

        let runtime_hashes = unsafe {
            std::slice::from_raw_parts(hashes[0], hashes_lengths[0] as usize)
                .iter()
                .map(|h| Hash::from(*h))
                .collect()
        };

        let instances_hashes: Vec<(InstanceId, Vec<Hash>)> = (0..instances_length)
            .map(|i| {
                let instance_hashes = unsafe {
                    std::slice::from_raw_parts(hashes[i + 1], hashes_lengths[i + 1] as usize)
                        .iter()
                        .map(|h| Hash::from(*h))
                        .collect()
                };
                let instance_id = instance_ids[i] as InstanceId;
                (instance_id, instance_hashes)
            })
            .collect();

        StateHashAggregator {
            runtime: runtime_hashes,
            instances: instances_hashes,
        }
    }
}

#[repr(C)]
#[derive(Clone, Copy)]
pub struct RawProtoSourceFile {
    pub name: *const c_char,
    pub content: *const c_char,
}

#[repr(C)]
#[derive(Clone, Copy)]
pub struct RawArtifactProtobufSpec {
    pub files: *const RawProtoSourceFile,
    pub files_amount: u32,
}

impl From<RawArtifactProtobufSpec> for ArtifactProtobufSpec {
    fn from(spec: RawArtifactProtobufSpec) -> ArtifactProtobufSpec {
        fn to_str(data: *const c_char) -> String {
            unsafe { CStr::from_ptr(data).to_string_lossy().into_owned() }
        }

        let raw_files =
            unsafe { std::slice::from_raw_parts(spec.files, spec.files_amount as usize) };

        let sources = raw_files
            .iter()
            .map(|f| ProtoSourceFile {
                name: to_str(f.name),
                content: to_str(f.content),
            })
            .collect();

        ArtifactProtobufSpec { sources }
    }
}

#[derive(Debug)]
pub enum RawIndexAccess<'a> {
    Fork(&'a Fork),
    Snapshot(&'a dyn Snapshot),
    SnapshotToken,
}
