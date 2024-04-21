use std::fmt::{self, Display, Formatter};

use chrono::NaiveDateTime;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Course {
    pub id: u32,
    pub name: String,
}

impl Display for Course {
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.name)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Problem {
    pub id: u32,
    pub full_id: String,
    pub name: String,
}

impl Display for Problem {
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.name)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Submit {
    pub id: String,
    pub version: u32,
    pub name: String,
    pub problem_id: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Test {
    pub id: u32,
    pub start_time: NaiveDateTime,
    pub end_time: Option<NaiveDateTime>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct SubmitForm {
    pub tests: Vec<String>,
    pub task_set_id: String,
    pub student_id: u32,
    pub select_test_type: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct TestResult {
    pub normal_points: f32,
    pub bonus_points: f32,
    pub problems: Vec<TestResultProblem>,
}

impl TestResult {
    pub fn total_points(&self) -> f32 {
        self.normal_points + self.bonus_points
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct TestResultProblem {
    pub name: String,
    pub percentage: f32,
    pub points: f32,
    pub output: String,
}
