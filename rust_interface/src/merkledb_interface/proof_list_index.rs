use std::os::raw::c_char;

use exonum_merkledb::{Fork, ObjectHash, ProofListIndex};

use super::binary_data::BinaryData;
use super::common::parse_string;

#[repr(C)]
pub struct RawProofListIndexMethods {
    pub get: ProofListIndexGet,
    pub push: ProofListIndexPush,
    // pub pop: ProofListIndexPop,
    pub len: ProofListIndexLen,
    pub set: ProofListIndexSet,
    pub clear: ProofListIndexClear,
    pub object_hash: ProofListIndexObjectHash,
}

impl Default for RawProofListIndexMethods {
    fn default() -> Self {
        Self {
            get,
            push,
            // pop,
            len,
            set,
            clear,
            object_hash,
        }
    }
}

#[repr(C)]
pub struct RawProofListIndex {
    pub fork: *const Fork,
    pub index_name: *const c_char,

    pub methods: RawProofListIndexMethods,
}

#[no_mangle]
pub unsafe fn merkledb_proof_list_index(
    fork: *const Fork,
    index_name: *const c_char,
) -> RawProofListIndex {
    RawProofListIndex {
        fork,
        index_name,
        methods: RawProofListIndexMethods::default(),
    }
}

type Allocate = unsafe extern "C" fn(len: u64) -> *mut u8;

type ProofListIndexGet = unsafe extern "C" fn(
    index: *const RawProofListIndex,
    idx: u64,
    allocate: Allocate,
) -> BinaryData;
// type ProofListIndexPop =
// unsafe extern "C" fn(index: *const RawProofListIndex, allocate: Allocate) -> BinaryData;
type ProofListIndexPush = unsafe extern "C" fn(index: *const RawProofListIndex, value: BinaryData);
type ProofListIndexLen = unsafe extern "C" fn(index: *const RawProofListIndex) -> u64;
type ProofListIndexSet =
    unsafe extern "C" fn(index: *const RawProofListIndex, idx: u64, value: BinaryData);
type ProofListIndexClear = unsafe extern "C" fn(index: *const RawProofListIndex);
type ProofListIndexObjectHash =
    unsafe extern "C" fn(index: *const RawProofListIndex, allocate: Allocate) -> BinaryData;

unsafe extern "C" fn get(
    index: *const RawProofListIndex,
    idx: u64,
    allocate: Allocate,
) -> BinaryData {
    let index = &*index;
    let index_name = parse_string(index.index_name);

    let fork = &*index.fork;
    let index: ProofListIndex<&Fork, Vec<u8>> = ProofListIndex::new(index_name, fork);

    let value = index.get(idx);

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

unsafe extern "C" fn push(index: *const RawProofListIndex, value: BinaryData) {
    let index = &*index;
    let index_name = parse_string(index.index_name);
    let value: Vec<u8> = value.to_vec();

    let fork = &*index.fork;
    let mut index: ProofListIndex<&Fork, Vec<u8>> = ProofListIndex::new(index_name, fork);

    index.push(value);
}

// unsafe extern "C" fn pop(index: *const RawProofListIndex, allocate: Allocate) -> BinaryData {
//     let index = &*index;
//     let index_name = parse_string(index.index_name);

//     let fork = &*index.fork;
//     let mut index: ProofListIndex<&Fork, Vec<u8>> = ProofListIndex::new(index_name, fork);

//     let value = index.pop();

//     match value {
//         Some(data) => {
//             let buffer: *mut u8 = allocate(data.len() as u64);

//             std::ptr::copy(data.as_ptr(), buffer, data.len());

//             BinaryData {
//                 data: buffer,
//                 data_len: data.len() as u64,
//             }
//         }
//         None => BinaryData {
//             data: std::ptr::null::<u8>(),
//             data_len: 0,
//         },
//     }
// }

unsafe extern "C" fn len(index: *const RawProofListIndex) -> u64 {
    let index = &*index;
    let index_name = parse_string(index.index_name);

    let fork = &*index.fork;
    let index: ProofListIndex<&Fork, Vec<u8>> = ProofListIndex::new(index_name, fork);

    index.len() as u64
}

unsafe extern "C" fn set(index: *const RawProofListIndex, idx: u64, value: BinaryData) {
    let index = &*index;
    let index_name = parse_string(index.index_name);
    let value: Vec<u8> = value.to_vec();

    let fork = &*index.fork;
    let mut index: ProofListIndex<&Fork, Vec<u8>> = ProofListIndex::new(index_name, fork);

    index.set(idx, value);
}

unsafe extern "C" fn clear(index: *const RawProofListIndex) {
    let index = &*index;
    let index_name = parse_string(index.index_name);

    let fork = &*index.fork;
    let mut index: ProofListIndex<&Fork, Vec<u8>> = ProofListIndex::new(index_name, fork);

    index.clear();
}

unsafe extern "C" fn object_hash(
    index: *const RawProofListIndex,
    allocate: Allocate,
) -> BinaryData {
    let index = &*index;
    let index_name = parse_string(index.index_name);

    let fork = &*index.fork;
    let index: ProofListIndex<&Fork, Vec<u8>> = ProofListIndex::new(index_name, fork);

    let value = index.object_hash();
    let data: &[u8] = value.as_ref();

    let buffer: *mut u8 = allocate(data.len() as u64);

    std::ptr::copy(data.as_ptr(), buffer, data.len());

    BinaryData {
        data: buffer,
        data_len: data.len() as u64,
    }
}
