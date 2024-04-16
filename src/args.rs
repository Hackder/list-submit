use clap::{Args, Parser, Subcommand};

#[derive(Debug, Parser)]
#[command(name = "list-submit")]
pub struct ListSubmitArgs {
    #[command(subcommand)]
    pub subcommand: ListSubmitCommand,
}


#[derive(Debug, Subcommand, Clone)]
pub enum ListSubmitCommand {
    Add(AddCommand),
    Remove(RemoveCommand),
    Submit(SubmitCommand),
    Auth,
    Clean,
}

#[derive(Debug, Args, Clone)]
pub struct AddCommand {
    /// Add a file to the current project
    /// If nothing or a path to a direcotry is specified,
    /// a multiselect window with all the files will show up
    /// If a file path or a glob pattern is specified, the matching files
    /// will be added
    #[clap(verbatim_doc_comment)]
    pub path: Option<String>,
}

#[derive(Debug, Args, Clone)]
pub struct RemoveCommand {
    /// Remove a file from the current project
    /// If nothing is specified, a multiselect window with all the files
    /// currently present will show up
    /// If a file path or a glob pattern is specified, the matching files
    /// will be removed
    #[clap(verbatim_doc_comment)]
    pub path: Option<String>,
}

#[derive(Debug, Args, Clone)]
pub struct SubmitCommand {
    /// Submit the project
    /// If a name is specified, a child directory with that name containing
    /// the config file will be treated as the active project
    #[clap(verbatim_doc_comment)]
    pub name: Option<String>,
}
