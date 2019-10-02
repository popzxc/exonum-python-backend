use std::ffi::CStr;
use std::os::raw::c_char;

pub unsafe fn parse_string(data: *const c_char) -> String {
    CStr::from_ptr(data).to_string_lossy().into_owned()
}
