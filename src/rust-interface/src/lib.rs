#[macro_use]
extern crate lazy_static;

use std::ffi::CStr;
use std::os::raw::c_char;

use exonum::runtime::Runtime;

mod errors;
mod pending_deployment;
mod python_interface;
mod runtime;
mod types;

// TODO return result
pub fn initialize_python_backend() -> Option<Box<dyn Runtime>> {
    None
}

// To be removed
type CCallbackType = unsafe extern "C" fn(a: u32, b: u32) -> u32;

#[no_mangle]
unsafe fn test(a: u32, hi: *const c_char) -> u32 {
    let hi_str = CStr::from_ptr(hi).to_string_lossy().into_owned();
    println!("Hello from rust! {}", hi_str);
    a
}

#[no_mangle]
fn test2(f: CCallbackType) {
    unsafe {
        let aaa = f(1, 2);
        println!("Got {}", aaa);
    }
}
