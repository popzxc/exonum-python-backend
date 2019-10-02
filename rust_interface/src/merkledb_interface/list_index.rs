use std::ffi::CStr;
use std::os::raw::c_char;

use exonum_merkledb::{Fork, ListIndex};

use super::binary_data::BinaryData;

#[repr(C)]
pub struct RawListIndex {
    pub fork: *const Fork,
    pub index_name: *const c_char,

    pub push: ListIndexPushMethod,
    pub len: ListIndexLenMethod,
}

#[no_mangle]
pub unsafe fn merkledb_list_index(fork: *const Fork, index_name: *const c_char) -> RawListIndex {
    RawListIndex {
        fork,
        index_name,
        push: merkledb_list_index_push,
        len: merkledb_list_index_len,
    }
}

unsafe fn parse_string(data: *const c_char) -> String {
    CStr::from_ptr(data).to_string_lossy().into_owned()
}

type ListIndexPushMethod = unsafe extern "C" fn(index: *const RawListIndex, value: BinaryData);
type ListIndexLenMethod = unsafe extern "C" fn(index: *const RawListIndex) -> u64;

pub unsafe extern "C" fn merkledb_list_index_push(index: *const RawListIndex, value: BinaryData) {
    let index = &*index;
    let index_name = parse_string(index.index_name);
    let value: Vec<u8> = value.to_vec();

    let fork = &*index.fork;
    let mut index: ListIndex<&Fork, Vec<u8>> = ListIndex::new(index_name, fork);

    index.push(value);
}

pub unsafe extern "C" fn merkledb_list_index_len(index: *const RawListIndex) -> u64 {
    println!("LEN!!!");
    let index = &*index;
    let index_name = parse_string(index.index_name);

    let fork = &*index.fork;
    let index: ListIndex<&Fork, Vec<u8>> = ListIndex::new(index_name, fork);

    index.len() as u64
}
