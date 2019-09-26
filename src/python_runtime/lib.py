"""TODO"""
import ctypes as c

RUST_LIBRARY_PATH = "../../target/debug/librust_interface.so"


class RustFFIProvider:
    """TODO"""

    def __init__(self, rust_library_path):
        self._rust_library_path = rust_library_path

        c.cdll.LoadLibrary(RUST_LIBRARY_PATH)
        self._rust_interface = c.CDLL(RUST_LIBRARY_PATH)


@c.CFUNCTYPE(c.c_uint32, c.c_uint32, c.c_uint32)
def callback(first, second):
    """TODO"""
    print("Hello from python!")
    return first + second


def main():
    """TODO"""

    # rust_interface = ffi.dlopen(RUST_LIBRARY_PATH)
    c.cdll.LoadLibrary(RUST_LIBRARY_PATH)
    rust_interface = c.CDLL(RUST_LIBRARY_PATH)

    hi_str = c.c_char_p(b"hello from python")
    print(rust_interface.test(1, hi_str))

    rust_interface.test2(callback)


if __name__ == "__main__":
    main()
