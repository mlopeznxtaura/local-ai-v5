#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::Command;
use std::fs;
use std::path::Path;

fn pipeline_dir() -> String {
    let exe = std::env::current_exe().unwrap_or_default();
    let base = exe.parent().unwrap_or(Path::new("."));
    let candidate = base
        .parent().unwrap_or(base)
        .parent().unwrap_or(base)
        .join("pipeline");
    if candidate.exists() {
        candidate.to_string_lossy().to_string()
    } else {
        "../pipeline".to_string()
    }
}

#[tauri::command]
fn preflight_check() -> Result<String, String> {
    let dir = pipeline_dir();
    let out = Command::new("python3")
        .arg("check.py")
        .current_dir(&dir)
        .output()
        .map_err(|e| format!("Cannot run check.py: {}", e))?;
    let stdout = String::from_utf8_lossy(&out.stdout).to_string();
    let stderr = String::from_utf8_lossy(&out.stderr).to_string();
    if out.status.success() { Ok(stdout) } else { Err(format!("{}\n{}", stdout, stderr)) }
}

#[tauri::command]
fn run_step(step: u32, prompt: String) -> Result<String, String> {
    let dir = pipeline_dir();

    if step == 0 {
        fs::write(format!("{}/user_prompt.txt", dir), &prompt)
            .map_err(|e| format!("Cannot write prompt: {}", e))?;
    }

    let script = match step {
        0 => "step0_ground.py",
        1 => "step1_compress.py",
        2 => "step2_mockui.py",
        3 => "step3_parse.py",
        4 => "step4_dag.py",
        5 => "step5_tasks.py",
        6 => "step6_build.py",
        _ => return Err(format!("Invalid step: {}", step)),
    };

    let out = Command::new("python3")
        .arg(script)
        .current_dir(&dir)
        .output()
        .map_err(|e| format!("python3 error: {}", e))?;

    let stdout = String::from_utf8_lossy(&out.stdout).to_string();
    let stderr = String::from_utf8_lossy(&out.stderr).to_string();

    if out.status.success() {
        Ok(stdout)
    } else {
        Err(format!("Step {} failed:\n{}\n{}", step, stdout, stderr))
    }
}

#[tauri::command]
fn get_output_path() -> String {
    let dir = pipeline_dir();
    let zip = format!("{}/output.zip", dir);
    let out = format!("{}/output", dir);
    if Path::new(&zip).exists() {
        Path::new(&zip).canonicalize()
            .map(|p| p.to_string_lossy().to_string())
            .unwrap_or(zip)
    } else {
        Path::new(&out).canonicalize()
            .map(|p| p.to_string_lossy().to_string())
            .unwrap_or(out)
    }
}

#[tauri::command]
fn open_output_folder(path: String) {
    #[cfg(target_os = "windows")]
    { Command::new("explorer").arg(&path).spawn().ok(); }
    #[cfg(target_os = "linux")]
    { Command::new("xdg-open").arg(&path).spawn().ok(); }
    #[cfg(target_os = "macos")]
    { Command::new("open").arg(&path).spawn().ok(); }
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            preflight_check,
            run_step,
            get_output_path,
            open_output_folder,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
