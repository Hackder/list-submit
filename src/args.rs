use clap::Parser;

#[derive(Debug, Parser)]
#[clap(name = "list-submit")]
pub struct ListSubmitArgs {
    /// Add a file to the current project
    ///
    /// If nothing or a path to a direcotry is specified,
    /// a multiselect window with all the files will show up
    ///
    /// If a file path or a glob pattern is specified, the matching files
    /// will be added
    pub add: Option<String>,

    /// Remove a file from the current project
    ///
    /// If nothing is specified, a multiselect window with all the files
    /// currently present will show up
    ///
    /// If a file path or a glob pattern is specified, the matching files
    /// will be removed
    pub remove: Option<String>,

    /// Remove all non existing files from the current project
    pub clean: bool,
}
