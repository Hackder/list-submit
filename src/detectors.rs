use std::path::{Path, PathBuf};

use itertools::Itertools;

pub struct DetectionResult {
    pub probability: f32,
    pub files: Vec<PathBuf>,
    pub recommendations: Vec<String>,
}

pub trait Detector {
    fn name(&self) -> &'static str;
    fn detect(&self, path: &Path) -> eyre::Result<DetectionResult>;
}

pub fn get_detectors() -> Vec<Box<dyn Detector>> {
    vec![Box::new(PythonDetector), Box::new(JavaDetector)]
}

pub struct PythonDetector;

static CODE_EXTENSIONS: [&'static str; 9] = [
    "py", "java", "cpp", "c", "h", "hpp", "cc", "kt", "hs",
];

pub fn is_program_file(path: &Path) -> bool {
    path.extension().map_or(false, |ext| {
        CODE_EXTENSIONS.contains(&ext.to_str().unwrap())
    })
}

impl Detector for PythonDetector {
    fn name(&self) -> &'static str {
        "Python"
    }

    fn detect(&self, path: &Path) -> eyre::Result<DetectionResult> {
        let original_path = path;
        let first_files = std::fs::read_dir(path)?
            .filter_map(|e| e.ok())
            .filter_map(|e| e.file_name().into_string().ok())
            .collect::<Vec<_>>();

        let mut path = path.to_path_buf();
        if first_files.contains(&"src".to_string()) {
            path = path.join("src");
        }

        let files = walkdir::WalkDir::new(&path)
            .into_iter()
            .filter_map(|e| e.ok())
            .map(|e| e.path().to_path_buf())
            .filter(|f| is_program_file(f))
            .map(|f| pathdiff::diff_paths(f, original_path).unwrap())
            .collect::<Vec<_>>();

        if files.contains(&PathBuf::from("riesenie.py")) {
            if has_list_header_comment(&path.join("riesenie.py")) {
                return Ok(DetectionResult {
                    probability: 0.9,
                    files: vec![PathBuf::from("riesenie.py")],
                    recommendations: vec![],
                });
            }
            return Ok(DetectionResult {
                probability: 0.8,
                files: vec![PathBuf::from("riesenie.py")],
                recommendations: vec!["File `riesenie.py` is missing a header comment.".to_string()],
            });
        }

        if files.contains(&PathBuf::from("src/riesenie.py")) {
            if has_list_header_comment(&path.join("src/riesenie.py")) {
                return Ok(DetectionResult {
                    probability: 0.9,
                    files: vec![PathBuf::from("src/riesenie.py")],
                    recommendations: vec![],
                });
            }
            return Ok(DetectionResult {
                probability: 0.8,
                files: vec![PathBuf::from("src/riesenie.py")],
                recommendations: vec![
                    "File `src/riesenie.py` is missing a header comment.".to_string()
                ],
            });
        }

        let files_len = files.len();
        let python_files = files
            .into_iter()
            .filter(|f| f.extension().unwrap() == "py")
            .collect_vec();
        if python_files.len() == files_len {
            return Ok(DetectionResult {
                probability: 0.8,
                files: python_files,
                recommendations: vec![],
            });
        }

        if python_files.len() as f32 / files_len as f32 > 0.5 {
            return Ok(DetectionResult {
                probability: 0.5,
                files: python_files,
                recommendations: vec![],
            });
        }

        if !python_files.is_empty() {
            return Ok(DetectionResult {
                probability: 0.3,
                files: python_files,
                recommendations: vec![],
            });
        }

        Ok(DetectionResult {
            probability: 0.0,
            files: vec![],
            recommendations: vec![],
        })
    }
}

fn has_list_header_comment(file_path: &Path) -> bool {
    let lines = std::fs::read_to_string(file_path).unwrap();
    let lines = lines.lines().take(3).collect::<Vec<_>>();

    lines.len() == 3
        && lines[0].starts_with("#")
        && lines[1].starts_with("# autor")
        && lines[2].starts_with("# datum")
}

pub struct JavaDetector;

impl Detector for JavaDetector {
    fn name(&self) -> &'static str {
        "Java"
    }

    fn detect(&self, path: &Path) -> eyre::Result<DetectionResult> {
        let original_path = path;
        let first_files = std::fs::read_dir(path)?
            .filter_map(|e| e.ok())
            .filter_map(|e| e.file_name().into_string().ok())
            .collect::<Vec<_>>();

        let mut path = path.to_path_buf();
        if first_files.contains(&"src".to_string()) {
            path = path.join("src");
        }

        let files = walkdir::WalkDir::new(&path)
            .into_iter()
            .filter_map(|e| e.ok())
            .map(|e| e.path().to_path_buf())
            .filter(|f| is_program_file(f))
            .map(|f| pathdiff::diff_paths(f, original_path).unwrap())
            .collect::<Vec<_>>();

        let java_files = files
            .iter()
            .filter(|f| f.extension().unwrap() == "java")
            .collect_vec();

        let non_test_files = java_files
            .iter()
            .filter(|f| {
                !f.file_name()
                    .unwrap()
                    .to_string_lossy()
                    .ends_with("Test.java")
                    && !f.file_name().unwrap().to_string_lossy().starts_with("Test")
            })
            .map(|f| f.to_path_buf())
            .collect_vec();

        if java_files.is_empty() {
            return Ok(DetectionResult {
                probability: 0.0,
                files: vec![],
                recommendations: vec![],
            });
        }

        if java_files.len() == files.len() {
            return Ok(DetectionResult {
                probability: 0.8,
                files: non_test_files,
                recommendations: vec![],
            });
        }

        if java_files.len() as f32 / files.len() as f32 > 0.5 {
            return Ok(DetectionResult {
                probability: 0.5,
                files: non_test_files,
                recommendations: vec![],
            });
        }

        Ok(DetectionResult {
            probability: 0.0,
            files: vec![],
            recommendations: vec![],
        })
    }
}
