use std::os::raw::c_char;

use exonum_merkledb::{Fork, MapIndex};

use super::binary_data::BinaryData;
use super::common::parse_string;

#[repr(C)]
pub struct RawMapIndexMethods {
    pub get: MapIndexGet,
    pub put: MapIndexPut,
    pub remove: MapIndexRemove,
    pub clear: MapIndexClear,
}

impl Default for RawMapIndexMethods {
    fn default() -> Self {
        Self {
            get,
            put,
            remove,
            clear,
        }
    }
}

#[repr(C)]
pub struct RawMapIndex {
    pub fork: *const Fork,
    pub index_name: *const c_char,

    pub methods: RawMapIndexMethods,
}

#[no_mangle]
pub unsafe fn merkledb_map_index(fork: *const Fork, index_name: *const c_char) -> RawMapIndex {
    RawMapIndex {
        fork,
        index_name,
        methods: RawMapIndexMethods::default(),
    }
}

type Allocate = unsafe extern "C" fn(len: u64) -> *mut u8;

type MapIndexGet = unsafe extern "C" fn(
    index: *const RawMapIndex,
    key: BinaryData,
    allocate: Allocate,
) -> BinaryData;
type MapIndexPut =
    unsafe extern "C" fn(index: *const RawMapIndex, key: BinaryData, value: BinaryData);
type MapIndexRemove = unsafe extern "C" fn(index: *const RawMapIndex, key: BinaryData);
type MapIndexClear = unsafe extern "C" fn(index: *const RawMapIndex);

unsafe extern "C" fn get(
    index: *const RawMapIndex,
    key: BinaryData,
    allocate: Allocate,
) -> BinaryData {
    let index = &*index;
    let index_name = parse_string(index.index_name);

    let key = key.to_vec();

    let fork = &*index.fork;
    let index: MapIndex<&Fork, Vec<u8>, Vec<u8>> = MapIndex::new(index_name, fork);

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

unsafe extern "C" fn put(index: *const RawMapIndex, key: BinaryData, value: BinaryData) {
    let index = &*index;
    let index_name = parse_string(index.index_name);
    let key: Vec<u8> = key.to_vec();
    let value: Vec<u8> = value.to_vec();

    let fork = &*index.fork;
    let mut index: MapIndex<&Fork, Vec<u8>, Vec<u8>> = MapIndex::new(index_name, fork);

    index.put(&key, value);
}

unsafe extern "C" fn remove(index: *const RawMapIndex, key: BinaryData) {
    let index = &*index;
    let index_name = parse_string(index.index_name);
    let key: Vec<u8> = key.to_vec();

    let fork = &*index.fork;
    let mut index: MapIndex<&Fork, Vec<u8>, Vec<u8>> = MapIndex::new(index_name, fork);

    index.remove(&key);
}

unsafe extern "C" fn clear(index: *const RawMapIndex) {
    let index = &*index;
    let index_name = parse_string(index.index_name);

    let fork = &*index.fork;
    let mut index: MapIndex<&Fork, Vec<u8>, Vec<u8>> = MapIndex::new(index_name, fork);

    index.clear();
}
