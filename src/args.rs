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
    Remove(RemoveCommand),
    Submit(SubmitCommand),
    Auth,
    Clean,
}

#[derive(Debug, Args, Clone)]
pub struct AddCommand {
    /// Add files to the current project
    /// If nothing or a path to a direcotry is specified,
    /// a multiselect window with all the files will show up
    #[clap(verbatim_doc_comment)]
    pub path: Vec<String>,
}

#[derive(Debug, Args, Clone)]
pub struct RemoveCommand {
    /// Remove files from the current project
    /// If nothing is specified, a multiselect window with all the files
    /// currently present will show up
    #[clap(verbatim_doc_comment)]
    pub path: Vec<String>,
}

#[derive(Debug, Args, Clone)]
pub struct SubmitCommand {
    /// Submit the project
    /// If a name is specified, a child directory with that name containing
    /// the config file will be treated as the active project
    #[clap(verbatim_doc_comment)]
    pub name: Option<String>,
}
