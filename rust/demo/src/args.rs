use clap::Parser;
use toolshed_runner::args;

// ARGS

#[derive(Clone, Debug, Parser, PartialEq)]
#[command(version = "1.0", about = "FS API")]
pub struct Args {
    #[command(flatten)]
    pub base: args::BaseArgs,
    #[arg(short, long)]
    pub repo: Option<String>,
}

impl args::Provider for Args {
    fn config(&self) -> String {
        self.base.config.clone()
    }

    fn log_level(&self) -> Option<String> {
        Some(self.base.log_level.clone()?)
    }
}
