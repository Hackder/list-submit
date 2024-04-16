use args::ListSubmitArgs;
use clap::Parser;

mod args;

fn main() {
    let args = ListSubmitArgs::parse();

    println!("{:#?}", args);
}
