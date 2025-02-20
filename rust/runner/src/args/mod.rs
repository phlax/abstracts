use crate::DEFAULT_CONFIG_PATH;
use clap::Parser;
use std::fmt::Debug;

pub trait Provider: Debug + Sync + Send {
    fn config(&self) -> String;
    fn log_level(&self) -> Option<String>;
}

#[derive(Clone, Debug, Parser, PartialEq)]
#[command(version = "1.0", about = "FS API")]
pub struct BaseArgs {
    #[arg(short, long, default_value = DEFAULT_CONFIG_PATH)]
    pub config: String,

    #[arg(long)]
    #[arg(short, long)]
    pub log_level: Option<String>,
}

impl Provider for BaseArgs {
    fn config(&self) -> String {
        self.config.clone()
    }

    fn log_level(&self) -> Option<String> {
        self.log_level.clone()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_baseargs_constructor() {
        let args = vec!["test_program"];
        let base_args = BaseArgs::parse_from(args.clone());
        assert!(base_args.config == *DEFAULT_CONFIG_PATH.to_string());
        assert!(base_args.log_level.is_none())
    }

    #[test]
    fn test_baseargs_constructor_config() {
        let args = vec!["test_program", "--config", "/some/path"];
        let base_args = BaseArgs::parse_from(args.clone());
        assert!(base_args.config == *"/some/path".to_string());
        assert!(base_args.log_level.is_none())
    }

    #[test]
    fn test_baseargs_constructor_log_level() {
        let args = vec!["test_program", "--log-level", "trace"];
        let base_args = BaseArgs::parse_from(args.clone());
        assert!(base_args.config == *DEFAULT_CONFIG_PATH.to_string());
        assert!(base_args.log_level == Some("trace".to_string()));
    }

    #[test]
    fn test_provider() {
        let base_args = BaseArgs {
            config: "/some/path".to_string(),
            log_level: Some("debug".to_string()),
        };
        assert!(base_args.config() == base_args.config);
        assert!(base_args.log_level() == base_args.log_level);
    }
}
