use colored::Colorize;
use serde::{Deserialize, Serialize};
use std::{
    env::VarError,
    io::{self, Write},
    path::Path,
};

#[cfg(any(target_os = "linux", target_os = "macos"))]
pub fn get_global_config_path() -> Result<String, VarError> {
    let home_dir = std::env::var("HOME")?;
    Ok(format!("{}/.config/list-submit/config.toml", home_dir))
}

#[cfg(target_os = "windows")]
pub fn get_global_config_path() -> Result<String, VarError> {
    let home_dir = std::env::var("USERPROFILE")?;
    Ok(format!("{}/AppData/Roaming/list-cli/config.toml", home_dir))
}

fn create_from_template(path: &Path, template: &str) -> eyre::Result<()> {
    let mut file = std::fs::File::create(path)?;
    file.write_all(template.as_bytes())?;
    Ok(())
}

const GLOBAL_CONFIG_VERSION: &str = "0.0.1";

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct GlobalConfig {
    pub version: String,
    pub auth: Option<AuthConfig>,
}

impl GlobalConfig {
    pub fn load() -> eyre::Result<Option<Self>> {
        let path = get_global_config_path()?;

        match std::fs::read_to_string(path) {
            Ok(content) => match content.parse::<toml_edit::DocumentMut>() {
                Ok(config) => {
                    let file_version = config.get("version").and_then(|v| v.as_str());

                    if file_version != Some(GLOBAL_CONFIG_VERSION) {
                        let message = format!(
                            "Global config version mismatch, replacing with default... Expected: {}, found: {:?}",
                            GLOBAL_CONFIG_VERSION,
                            file_version
                        );
                        eprintln!("{}", message.yellow());
                        return Ok(None);
                    }

                    match toml_edit::de::from_document::<GlobalConfig>(config) {
                        Ok(config) => {
                            if let Some(auth) = &config.auth {
                                if auth.email.is_empty() && auth.password.is_empty() {
                                    return Ok(Some(GlobalConfig {
                                        auth: None,
                                        ..config
                                    }));
                                }
                            }
                            Ok(Some(config))
                        }
                        Err(e) => {
                            eprintln!(
                                "{}",
                                "Global config is corrupted, replacing with default...".yellow()
                            );
                            log::debug!("Failed to parse serde global config: {}", e);
                            Ok(None)
                        }
                    }
                }
                Err(e) => {
                    eprintln!(
                        "{}",
                        "Failed to parse toml global config, replacing with default...".yellow()
                    );
                    log::debug!("Failed to parse toml global config: {}", e);
                    Ok(None)
                }
            },
            Err(err) if err.kind() == io::ErrorKind::NotFound => {
                eprintln!("{}", "Global config not found, creating new...".yellow());
                Ok(None)
            }
            Err(err) => Err(err.into()),
        }
    }

    pub fn save(&self) -> eyre::Result<()> {
        let path = get_global_config_path()?;
        let path = Path::new(&path);
        let exists = path.exists();
        if !exists {
            std::fs::create_dir_all(path.parent().unwrap())?;
            create_from_template(&path, include_str!("templates/global-config.toml"))?;
        }

        let content = std::fs::read_to_string(&path)?;
        let mut document = content.parse::<toml_edit::DocumentMut>()?;

        // TODO: Make sure version matches, file could have changed during runtime

        document["version"] = toml_edit::value(self.version.clone());

        if let Some(auth) = &self.auth {
            let auth_table = document
                .as_table_mut()
                .entry("auth")
                .or_insert(toml_edit::table());

            auth_table["email"] = toml_edit::value(auth.email.clone());
            auth_table["password"] = toml_edit::value(auth.password.clone());
        } else {
            document.remove("auth");
        }

        std::fs::write(&path, document.to_string())?;

        Ok(())
    }
}

impl Default for GlobalConfig {
    fn default() -> Self {
        Self {
            version: GLOBAL_CONFIG_VERSION.to_owned(),
            auth: None,
        }
    }
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct AuthConfig {
    pub email: String,
    pub password: String,
}
