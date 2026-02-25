fn main() {
    tonic_build::configure()
        .build_client(false)
        .build_server(true)
        .compile_protos(&["proto/sim_engine.proto"], &["proto"])
        .expect("failed to compile sim_engine.proto");
}