fn main() {
    if let Err(e) = ensure_backend() {
        eprintln!("Warning: {e}");
    }
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("error while running Tauri application");
}

fn ensure_backend() -> Result<(), String> {
    let addr = std::env::var("KARI_BACKEND").unwrap_or_else(|_| "127.0.0.1:8000".into());
    std::net::TcpStream::connect(&addr)
        .map(|_| ())
        .map_err(|_| format!("Backend at {addr} not reachable"))
}
