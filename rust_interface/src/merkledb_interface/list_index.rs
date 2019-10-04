use std::os::raw::c_char;

use exonum_merkledb::{Fork, ListIndex, Snapshot};

use super::binary_data::BinaryData;
use super::common::parse_string;
use crate::types::RawIndexAccess;

#[repr(C)]
pub struct RawListIndexMethods {
    pub get: ListIndexGet,
    pub push: ListIndexPush,
    pub pop: ListIndexPop,
    pub len: ListIndexLen,
    pub set: ListIndexSet,
    pub clear: ListIndexClear,
}

impl Default for RawListIndexMethods {
    fn default() -> Self {
        Self {
            get,
            push,
            pop,
            len,
            set,
            clear,
        }
    }
}

#[repr(C)]
pub struct RawListIndex<'a> {
    pub access: *const RawIndexAccess<'a>,
    pub index_name: *const c_char,

    pub methods: RawListIndexMethods,
}

#[no_mangle]
pub unsafe fn merkledb_list_index(
    access: *const RawIndexAccess,
    index_name: *const c_char,
) -> RawListIndex {
    RawListIndex {
        access,
        index_name,
        methods: RawListIndexMethods::default(),
    }
}

type Allocate = unsafe extern "C" fn(len: u64) -> *mut u8;

type ListIndexGet =
    unsafe extern "C" fn(index: *const RawListIndex, idx: u64, allocate: Allocate) -> BinaryData;
type ListIndexPop =
    unsafe extern "C" fn(index: *const RawListIndex, allocate: Allocate) -> BinaryData;
type ListIndexPush = unsafe extern "C" fn(index: *const RawListIndex, value: BinaryData);
type ListIndexLen = unsafe extern "C" fn(index: *const RawListIndex) -> u64;
type ListIndexSet = unsafe extern "C" fn(index: *const RawListIndex, idx: u64, value: BinaryData);
type ListIndexClear = unsafe extern "C" fn(index: *const RawListIndex);

unsafe extern "C" fn get(index: *const RawListIndex, idx: u64, allocate: Allocate) -> BinaryData {
    let index = &*index;
    let index_name = parse_string(index.index_name);

    let value = match *index.access {
        RawIndexAccess::Fork(fork) => {
            let index: ListIndex<&Fork, Vec<u8>> = ListIndex::new(index_name, fork);
            index.get(idx)
        }
        RawIndexAccess::Snapshot(snapshot) => {
            let index: ListIndex<&dyn Snapshot, Vec<u8>> = ListIndex::new(index_name, snapshot);
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

unsafe extern "C" fn push(index: *const RawListIndex, value: BinaryData) {
    let index = &*index;
    let index_name = parse_string(index.index_name);
    let value: Vec<u8> = value.to_vec();

    match *index.access {
        RawIndexAccess::Fork(fork) => {
            let mut index: ListIndex<&Fork, Vec<u8>> = ListIndex::new(index_name, fork);

            index.push(value);
        }
        RawIndexAccess::Snapshot(_) => {
            panic!("Attempt to call mutable method with a snapshot");
        }
    }
}

unsafe extern "C" fn pop(index: *const RawListIndex, allocate: Allocate) -> BinaryData {
    let index = &*index;
    let index_name = parse_string(index.index_name);

    match *index.access {
        RawIndexAccess::Fork(fork) => {
            let mut index: ListIndex<&Fork, Vec<u8>> = ListIndex::new(index_name, fork);

            let value = index.pop();

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
        RawIndexAccess::Snapshot(_) => {
            panic!("Attempt to call mutable method with a snapshot");
        }
    }
}

unsafe extern "C" fn len(index: *const RawListIndex) -> u64 {
    let index = &*index;
    let index_name = parse_string(index.index_name);

    match *index.access {
        RawIndexAccess::Fork(fork) => {
            let index: ListIndex<&Fork, Vec<u8>> = ListIndex::new(index_name, fork);
            index.len() as u64
        }
        RawIndexAccess::Snapshot(snapshot) => {
            let index: ListIndex<&dyn Snapshot, Vec<u8>> = ListIndex::new(index_name, snapshot);
            index.len() as u64
        }
    }
}

unsafe extern "C" fn set(index: *const RawListIndex, idx: u64, value: BinaryData) {
    let index = &*index;
    let index_name = parse_string(index.index_name);
    let value: Vec<u8> = value.to_vec();

    match *index.access {
        RawIndexAccess::Fork(fork) => {
            let mut index: ListIndex<&Fork, Vec<u8>> = ListIndex::new(index_name, fork);

            index.set(idx, value);
        }
        RawIndexAccess::Snapshot(_) => {
            panic!("Attempt to call mutable method with a snapshot");
        }
    }
}

unsafe extern "C" fn clear(index: *const RawListIndex) {
    let index = &*index;
    let index_name = parse_string(index.index_name);

    match *index.access {
        RawIndexAccess::Fork(fork) => {
            let mut index: ListIndex<&Fork, Vec<u8>> = ListIndex::new(index_name, fork);

            index.clear();
        }
        RawIndexAccess::Snapshot(_) => {
            panic!("Attempt to call mutable method with a snapshot");
        }
    }
}
