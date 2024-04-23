use std::path::PathBuf;

use clap::{Args, Parser, Subcommand};

#[derive(Debug, Parser)]
#[command(name = "list-submit")]
pub struct ListSubmitArgs {
    /// Specify the project to work with
    /// A project is the name of a directory containing a config file
    #[clap(short, long, verbatim_doc_comment)]
    pub project: Option<String>,

    #[command(subcommand)]
    pub subcommand: Option<ListSubmitCommand>,
}


#[derive(Debug, Subcommand, Clone)]
pub enum ListSubmitCommand {
    Add(AddCommand),
    /// Shows interactive multiselect window to remove files
    Files,
    Submit,
    Auth,
    Clean,
    Update,
}

#[derive(Debug, Args, Clone)]
pub struct AddCommand {
    /// Add files to the current project
    /// If nothing or a path to a direcotry is specified,
    /// a multiselect window with all the files will show up
    #[clap(verbatim_doc_comment)]
    pub files: Vec<PathBuf>,
}

