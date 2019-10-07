#[macro_use]
extern crate lazy_static;

#[macro_use]
extern crate log;

mod errors;
pub mod merkledb_interface;
mod pending_deployment;
mod python_interface;
mod runtime;
mod types;

// use exonum_cli::NodeBuilder;
use exonum_merkledb::TemporaryDB;

use exonum::{
    blockchain::{ConsensusConfig, InstanceCollection, ValidatorKeys},
    keys::Keys,
    node::{Node, NodeApiConfig, NodeConfig},
};
use exonum_supervisor::Supervisor;

pub use runtime::PythonRuntime;

// Functions for python side.
pub use merkledb_interface::{
    list_index::merkledb_list_index, map_index::merkledb_map_index,
    proof_list_index::merkledb_proof_list_index, proof_map_index::merkledb_proof_map_index,
};
pub use python_interface::{get_snapshot_token, init_python_side};

// TODO: Use exonum_cli to create node

// #[no_mangle]
// pub unsafe extern "C" fn main() -> Result<(), failure::Error> {
//     exonum::helpers::init_logger().unwrap();

//     let python_runtime = PythonRuntime::new();

//     NodeBuilder::new()
//         .with_external_runtime(python_runtime)
//         .run()
// }

fn node_config() -> NodeConfig {
    let (consensus_public_key, consensus_secret_key) = exonum::crypto::gen_keypair();
    let (service_public_key, service_secret_key) = exonum::crypto::gen_keypair();

    let consensus = ConsensusConfig {
        validator_keys: vec![ValidatorKeys {
            consensus_key: consensus_public_key,
            service_key: service_public_key,
        }],
        ..ConsensusConfig::default()
    };

    let public_api_address = "127.0.0.1:8080".parse().unwrap();
    let private_api_address = "127.0.0.1:8081".parse().unwrap();
    let api_cfg = NodeApiConfig {
        public_api_address: Some(public_api_address),
        private_api_address: Some(private_api_address),
        ..Default::default()
    };

    let peer_address = "0.0.0.0:2000";

    NodeConfig {
        listen_address: peer_address.parse().unwrap(),
        consensus,
        external_address: peer_address.to_owned(),
        network: Default::default(),
        connect_list: Default::default(),
        api: api_cfg,
        mempool: Default::default(),
        services_configs: Default::default(),
        database: Default::default(),
        thread_pool_size: Default::default(),
        master_key_path: Default::default(),
        keys: Keys::from_keys(
            consensus_public_key,
            consensus_secret_key,
            service_public_key,
            service_secret_key,
        ),
    }
}

#[no_mangle]
pub unsafe extern "C" fn main() {
    exonum::helpers::init_logger().unwrap();

    let python_runtime = PythonRuntime::new();

    let external_runtimes: Vec<(u32, Box<dyn exonum::runtime::Runtime>)> =
        vec![python_runtime.into()];
    let services = vec![InstanceCollection::from(Supervisor)];

    println!("Creating database in temporary dir...");
    let node = Node::new(
        TemporaryDB::new(),
        external_runtimes,
        services,
        node_config(),
        None,
    );
    println!("Starting a single node...");
    println!("Blockchain is ready for transactions!");
    node.run().unwrap();
}
