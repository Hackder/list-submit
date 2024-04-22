use colored::Colorize;
use inquire::MultiSelect;
use itertools::Itertools;
use serde::{Deserialize, Serialize};
use std::{
    collections::VecDeque,
    env::VarError,
    fmt::Display,
    io::{self, Write},
    ops::Deref,
    path::{Path, PathBuf},
};

#[cfg(any(target_os = "linux", target_os = "macos"))]
pub fn get_global_config_path() -> Result<String, VarError> {
    let home_dir = std::env::var("HOME")?;
    Ok(format!("{}/.config/list-submit/config.toml", home_dir))
}

#[cfg(target_os = "windows")]
pub fn get_global_config_path() -> Result<String, VarError> {
    let home_dir = std::env::var("USERPROFILE")?;
    Ok(format!("{}/AppData/Roaming/list-submit/config.toml", home_dir))
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
                                if auth.is_empty() {
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

        let config = toml_edit::ser::to_string_pretty(self)?;

        std::fs::write(&path, config)?;

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

impl AuthConfig {
    pub fn is_empty(&self) -> bool {
        self.email.is_empty() && self.password.is_empty()
    }
}

const PROJECT_CONFIG_VERSION: &str = "0.0.1";
const PROJECT_CONFIG_NAME: &str = "list-submit.toml";

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct ProblemConfig {
    pub course_id: u32,
    pub problem_id: u32,
    pub problem_name: String,
    pub files: Vec<String>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct ProjectConfig {
    pub version: String,
    pub problem: ProblemConfig,
}

#[derive(Debug, Clone)]
struct LsbmPathBuf(PathBuf);

impl Deref for LsbmPathBuf {
    type Target = PathBuf;

    fn deref(&self) -> &Self::Target {
        &self.0
    }
}

impl Display for LsbmPathBuf {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.0.display())
    }
}

impl From<PathBuf> for LsbmPathBuf {
    fn from(path: PathBuf) -> Self {
        Self(path)
    }
}

impl ProjectConfig {
    pub fn load(path: &Path) -> eyre::Result<Self> {
        let content = std::fs::read_to_string(path)?;
        let document = content.parse::<toml_edit::DocumentMut>()?;

        if document["version"].as_str() != Some(PROJECT_CONFIG_VERSION) {
            return Err(eyre::eyre!(
                "Project config version mismatch, expected: {}, found: {:?}",
                PROJECT_CONFIG_VERSION,
                document["version"].as_str()
            ));
        }

        let config = toml_edit::de::from_str(&content)?;

        Ok(config)
    }

    pub fn find_project_config_up(start: &Path) -> eyre::Result<Option<PathBuf>> {
        let mut current = start.to_path_buf();

        loop {
            let config_path = current.join(PROJECT_CONFIG_NAME);

            if config_path.exists() {
                return Ok(Some(config_path));
            }

            if !current.pop() {
                break;
            }
        }

        Ok(None)
    }

    pub fn find_project_config_down(
        start: &Path,
        project_name: &str,
    ) -> eyre::Result<Option<PathBuf>> {
        let current = start.to_path_buf();

        let mut queue = VecDeque::new();
        queue.push_back(current);

        while !queue.is_empty() {
            let curr = queue.pop_front().unwrap();

            if curr.file_name().and_then(|a| a.to_str()) == Some(project_name) {
                let config_path = curr.join(PROJECT_CONFIG_NAME);

                if config_path.exists() {
                    return Ok(Some(config_path));
                }
            }

            for entry in curr.read_dir()? {
                let entry = entry?;

                if entry.file_type()?.is_dir() {
                    queue.push_back(entry.path());
                }
            }
        }

        Ok(None)
    }

    pub fn create(
        path: &Path,
        course_id: u32,
        problem_id: u32,
        problem_name: &str,
        files: &Vec<String>,
    ) -> eyre::Result<(ProjectConfig, PathBuf)> {
        let path = path.join(PROJECT_CONFIG_NAME);
        if !path.exists() {
            std::fs::create_dir_all(path.parent().unwrap())?;
            create_from_template(&path, include_str!("templates/project-config.toml"))?;
        }

        let config = ProjectConfig {
            version: PROJECT_CONFIG_VERSION.to_owned(),
            problem: ProblemConfig {
                course_id,
                problem_id,
                problem_name: problem_name.to_owned(),
                files: files.clone(),
            },
        };

        config.save(path.as_path())?;

        Ok((config, path))
    }

    pub fn save(&self, path: &Path) -> eyre::Result<()> {
        let content = std::fs::read_to_string(path)?;
        let mut document = content.parse::<toml_edit::DocumentMut>()?;

        document["version"] = toml_edit::value(PROJECT_CONFIG_VERSION);

        let problem = document["problem"]
            .or_insert(toml_edit::table())
            .as_table_mut()
            .unwrap();

        problem["course_id"] = toml_edit::value(self.problem.course_id as i64);
        problem["problem_id"] = toml_edit::value(self.problem.problem_id as i64);
        problem["problem_name"] = toml_edit::value(&self.problem.problem_name);
        let files_arr = problem["files"]
            .or_insert(toml_edit::array())
            .as_array_mut()
            .unwrap();

        files_arr.clear();

        self.problem.files.iter().unique().for_each(|file| {
            files_arr.push(file);
        });

        std::fs::write(path, document.to_string()).map_err(Into::into)
    }

    pub fn add_files(&mut self, files: impl IntoIterator<Item = PathBuf>) {
        for file in files {
            println!("{} {}", "Adding file:".green(), file.display());
            self.problem.files.push(file.display().to_string());
        }
    }

    pub fn add_files_from(&mut self, dir: &Path, relative_to: &Path) -> eyre::Result<()> {
        let files = walkdir::WalkDir::new(dir)
            .into_iter()
            .filter_map(|e| e.ok())
            .filter(|e| e.file_type().is_file())
            .filter(|e| {
                e.path()
                    .file_name()
                    .is_some_and(|f| f != PROJECT_CONFIG_NAME)
            })
            .map(|e| pathdiff::diff_paths(e.path(), relative_to))
            .filter_map(|e| e)
            .map(LsbmPathBuf::from)
            .collect::<Vec<_>>();

        if files.is_empty() {
            eprintln!("{}", "No files found in the directory".red());
            return Ok(());
        }

        let default = files
            .iter()
            .enumerate()
            .filter(|(_, value)| self.problem.files.contains(&value.display().to_string()))
            .map(|(i, _)| i)
            .collect::<Vec<_>>();

        let picked = MultiSelect::new("Select files to add", files)
            .with_default(&default)
            .prompt()?;

        let picked = picked.into_iter().map(|f| f.0);

        self.add_files(picked);

        Ok(())
    }

    pub fn files_menu_interactive(&mut self) -> eyre::Result<()> {
        let picked = MultiSelect::new("Deselect files to remove", self.problem.files.clone())
            .with_all_selected_by_default()
            .prompt()?;

        self.problem.files.retain(|f| picked.contains(f));

        Ok(())
    }

    pub fn clean_files(&mut self, relative_to: &Path) -> eyre::Result<usize> {
        let len_before = self.problem.files.len();
        self.problem.files.retain(|f| {
            if relative_to.join(f).exists() {
                true
            } else {
                eprintln!("{} {}", "Removing file:".red(), f);
                false
            }
        });
        let len_after = self.problem.files.len();

        Ok(len_before - len_after)
    }
}
