#[repr(C)]
pub struct BinaryData {
    pub data: *const u8,
    pub data_len: u64,
}

impl BinaryData {
    pub unsafe fn to_vec(&self) -> Vec<u8> {
        std::slice::from_raw_parts(self.data, self.data_len as usize).to_vec()
    }
}
