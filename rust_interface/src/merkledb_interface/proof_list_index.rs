use std::os::raw::c_char;

use exonum_merkledb::{Fork, ObjectHash, ProofListIndex, Snapshot};

use super::binary_data::BinaryData;
use super::common::parse_string;
use crate::types::RawIndexAccess;

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
pub struct RawProofListIndex<'a> {
    pub access: *const RawIndexAccess<'a>,
    pub index_name: *const c_char,

    pub methods: RawProofListIndexMethods,
}

#[no_mangle]
pub unsafe fn merkledb_proof_list_index(
    access: *const RawIndexAccess,
    index_name: *const c_char,
) -> RawProofListIndex {
    RawProofListIndex {
        access,
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
//     unsafe extern "C" fn(index: *const RawProofListIndex, allocate: Allocate) -> BinaryData;
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

    let value = match *index.access {
        RawIndexAccess::Fork(fork) => {
            let index: ProofListIndex<&Fork, Vec<u8>> = ProofListIndex::new(index_name, fork);
            index.get(idx)
        }
        RawIndexAccess::Snapshot(snapshot) => {
            let index: ProofListIndex<&dyn Snapshot, Vec<u8>> =
                ProofListIndex::new(index_name, snapshot);
            index.get(idx)
        }
    };

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

    match *index.access {
        RawIndexAccess::Fork(fork) => {
            let mut index: ProofListIndex<&Fork, Vec<u8>> = ProofListIndex::new(index_name, fork);

            index.push(value);
        }
        RawIndexAccess::Snapshot(_) => {
            panic!("Attempt to call mutable method with a snapshot");
        }
    }
}

// unsafe extern "C" fn pop(index: *const RawProofListIndex, allocate: Allocate) -> BinaryData {
//     let index = &*index;
//     let index_name = parse_string(index.index_name);

//     match *index.access {
//         RawIndexAccess::Fork(fork) => {
//             let mut index: ProofListIndex<&Fork, Vec<u8>> = ProofListIndex::new(index_name, fork);

//             let value = index.pop();

//             match value {
//                 Some(data) => {
//                     let buffer: *mut u8 = allocate(data.len() as u64);

//                     std::ptr::copy(data.as_ptr(), buffer, data.len());

//                     BinaryData {
//                         data: buffer,
//                         data_len: data.len() as u64,
//                     }
//                 }
//                 None => BinaryData {
//                     data: std::ptr::null::<u8>(),
//                     data_len: 0,
//                 },
//             }
//         }
//         RawIndexAccess::Snapshot(_) => {
//             panic!("Attempt to call mutable method with a snapshot");
//         }
//     }
// }

unsafe extern "C" fn len(index: *const RawProofListIndex) -> u64 {
    let index = &*index;
    let index_name = parse_string(index.index_name);

    match *index.access {
        RawIndexAccess::Fork(fork) => {
            let index: ProofListIndex<&Fork, Vec<u8>> = ProofListIndex::new(index_name, fork);
            index.len() as u64
        }
        RawIndexAccess::Snapshot(snapshot) => {
            let index: ProofListIndex<&dyn Snapshot, Vec<u8>> =
                ProofListIndex::new(index_name, snapshot);
            index.len() as u64
        }
    }
}

unsafe extern "C" fn set(index: *const RawProofListIndex, idx: u64, value: BinaryData) {
    let index = &*index;
    let index_name = parse_string(index.index_name);
    let value: Vec<u8> = value.to_vec();

    match *index.access {
        RawIndexAccess::Fork(fork) => {
            let mut index: ProofListIndex<&Fork, Vec<u8>> = ProofListIndex::new(index_name, fork);

            index.set(idx, value);
        }
        RawIndexAccess::Snapshot(_) => {
            panic!("Attempt to call mutable method with a snapshot");
        }
    }
}

unsafe extern "C" fn clear(index: *const RawProofListIndex) {
    let index = &*index;
    let index_name = parse_string(index.index_name);

    match *index.access {
        RawIndexAccess::Fork(fork) => {
            let mut index: ProofListIndex<&Fork, Vec<u8>> = ProofListIndex::new(index_name, fork);

            index.clear();
        }
        RawIndexAccess::Snapshot(_) => {
            panic!("Attempt to call mutable method with a snapshot");
        }
    }
}

unsafe extern "C" fn object_hash(
    index: *const RawProofListIndex,
    allocate: Allocate,
) -> BinaryData {
    let index = &*index;
    let index_name = parse_string(index.index_name);

    let value = match *index.access {
        RawIndexAccess::Fork(fork) => {
            let index: ProofListIndex<&Fork, Vec<u8>> = ProofListIndex::new(index_name, fork);
            index.object_hash()
        }
        RawIndexAccess::Snapshot(snapshot) => {
            let index: ProofListIndex<&dyn Snapshot, Vec<u8>> =
                ProofListIndex::new(index_name, snapshot);
            index.object_hash()
        }
    };
    let data: &[u8] = value.as_ref();

    let buffer: *mut u8 = allocate(data.len() as u64);

    std::ptr::copy(data.as_ptr(), buffer, data.len());

    BinaryData {
        data: buffer,
        data_len: data.len() as u64,
    }
}
