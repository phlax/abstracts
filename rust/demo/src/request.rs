use crate::config::Config;
use serde::{Deserialize, Serialize};
use toolshed_runner::{config, request};

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct Request {
    pub config: Config,
    #[serde(default = "Request::default_name")]
    pub name: String,
}

impl Request {
    fn default_name() -> String {
        "default".to_string()
    }
}

impl request::Factory<Request, Config> for Request {
    fn new(config: Config, name: Option<String>) -> Self {
        if let Some(name) = name {
            Self { config, name }
        } else {
            Self {
                config,
                name: Self::default_name(),
            }
        }
    }
}

impl request::Request for Request {
    fn get_name(&self) -> &str {
        &self.name
    }

    fn get_config(&self) -> Box<&dyn config::Provider> {
        Box::new(&self.config)
    }
}
