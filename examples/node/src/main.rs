use exonum_cli::NodeBuilder;

use rust_interface::initialize_python_backend;

// TODO
const CONFIG_PATH: &str = "../../config.toml";

fn main() -> Result<(), failure::Error> {
    exonum::helpers::init_logger().unwrap();

    let python_runtime = initialize_python_backend(CONFIG_PATH).unwrap();
    NodeBuilder::new()
        .with_external_runtime(python_runtime)
        .run()
}
