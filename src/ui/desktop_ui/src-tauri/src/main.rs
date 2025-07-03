#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri_plugin_http::Http;
use tauri_plugin_log::Builder as LogBuilder;
use tauri_plugin_shell::Shell;

fn main() {
    tauri::Builder::default()
        .plugin(Http::default())
        .plugin(Shell::default())
        .plugin(LogBuilder::default().build())
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
