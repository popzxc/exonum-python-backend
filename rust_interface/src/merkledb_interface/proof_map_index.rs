use std::os::raw::c_char;

use exonum_merkledb::{Fork, ObjectHash, ProofMapIndex};

use super::binary_data::BinaryData;
use super::common::parse_string;

#[repr(C)]
pub struct RawProofMapIndexMethods {
    pub get: ProofMapIndexGet,
    pub put: ProofMapIndexPut,
    pub remove: ProofMapIndexRemove,
    pub clear: ProofMapIndexClear,
    pub object_hash: ProofMapIndexObjectHash,
}

impl Default for RawProofMapIndexMethods {
    fn default() -> Self {
        Self {
            get,
            put,
            remove,
            clear,
            object_hash,
        }
    }
}

#[repr(C)]
pub struct RawProofMapIndex {
    pub fork: *const Fork,
    pub index_name: *const c_char,

    pub methods: RawProofMapIndexMethods,
}

#[no_mangle]
pub unsafe fn merkledb_proof_map_index(
    fork: *const Fork,
    index_name: *const c_char,
) -> RawProofMapIndex {
    RawProofMapIndex {
        fork,
        index_name,
        methods: RawProofMapIndexMethods::default(),
    }
}

type Allocate = unsafe extern "C" fn(len: u64) -> *mut u8;

type ProofMapIndexGet = unsafe extern "C" fn(
    index: *const RawProofMapIndex,
    key: BinaryData,
    allocate: Allocate,
) -> BinaryData;
type ProofMapIndexPut =
    unsafe extern "C" fn(index: *const RawProofMapIndex, key: BinaryData, value: BinaryData);
type ProofMapIndexRemove = unsafe extern "C" fn(index: *const RawProofMapIndex, key: BinaryData);
type ProofMapIndexClear = unsafe extern "C" fn(index: *const RawProofMapIndex);
type ProofMapIndexObjectHash =
    unsafe extern "C" fn(index: *const RawProofMapIndex, allocate: Allocate) -> BinaryData;

unsafe extern "C" fn get(
    index: *const RawProofMapIndex,
    key: BinaryData,
    allocate: Allocate,
) -> BinaryData {
    let index = &*index;
    let index_name = parse_string(index.index_name);

    let key = key.to_vec();

    let fork = &*index.fork;
    let index: ProofMapIndex<&Fork, Vec<u8>, Vec<u8>> = ProofMapIndex::new(index_name, fork);

    let value = index.get(&key);

    match value {
        Some(data) => {
            let buffer: *mut u8 = allocate(data.len() as u64);

            std::ptr::copy(data.as_ptr(), buffer, data.len());

            BinaryData {
                data: buffer,
                data_len: data.len() as u64,
            }
        }
        None => BinaryData {
            data: std::ptr::null::<u8>(),
            data_len: 0,
        },
    }
}

unsafe extern "C" fn put(index: *const RawProofMapIndex, key: BinaryData, value: BinaryData) {
    let index = &*index;
    let index_name = parse_string(index.index_name);
    let key: Vec<u8> = key.to_vec();
    let value: Vec<u8> = value.to_vec();

    let fork = &*index.fork;
    let mut index: ProofMapIndex<&Fork, Vec<u8>, Vec<u8>> = ProofMapIndex::new(index_name, fork);

    index.put(&key, value);
}

unsafe extern "C" fn remove(index: *const RawProofMapIndex, key: BinaryData) {
    let index = &*index;
    let index_name = parse_string(index.index_name);
    let key: Vec<u8> = key.to_vec();

    let fork = &*index.fork;
    let mut index: ProofMapIndex<&Fork, Vec<u8>, Vec<u8>> = ProofMapIndex::new(index_name, fork);

    index.remove(&key);
}

unsafe extern "C" fn clear(index: *const RawProofMapIndex) {
    let index = &*index;
    let index_name = parse_string(index.index_name);

    let fork = &*index.fork;
    let mut index: ProofMapIndex<&Fork, Vec<u8>, Vec<u8>> = ProofMapIndex::new(index_name, fork);

    index.clear();
}

unsafe extern "C" fn object_hash(index: *const RawProofMapIndex, allocate: Allocate) -> BinaryData {
    let index = &*index;
    let index_name = parse_string(index.index_name);

    let fork = &*index.fork;
    let index: ProofMapIndex<&Fork, Vec<u8>, Vec<u8>> = ProofMapIndex::new(index_name, fork);

    let value = index.object_hash();
    let data: &[u8] = value.as_ref();

    let buffer: *mut u8 = allocate(data.len() as u64);

    std::ptr::copy(data.as_ptr(), buffer, data.len());

    BinaryData {
        data: buffer,
        data_len: data.len() as u64,
    }
}
