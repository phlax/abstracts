use crate::repo::RepoConfig;
use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use serde_yaml::{self, Value};
use toolshed_runner::config;
#[allow(unused_imports)]
use toolshed_runner::config::Provider as _;

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct Config {
    #[serde(flatten)]
    pub base: config::BaseConfig,
    #[serde(default = "RepoConfig::default_repo")]
    pub repo: RepoConfig,
}

impl Config {
    pub fn get<T: for<'de> Deserialize<'de>>(&self, key: &str) -> Option<T> {
        let field: Option<Value> = self.get_value(key);
        field.and_then(|v| serde_yaml::from_value(v).ok())
    }

    fn get_value(&self, key: &str) -> Option<Value> {
        let keys: Vec<&str> = key.split('.').collect();
        let serialized = if keys[0] == "log" {
            self.base.serialized()?
        } else {
            self.serialized()?
        };
        self.resolve(&serialized, &keys)
    }

    fn resolve(&self, current: &Value, keys: &[&str]) -> Option<Value> {
        if keys.is_empty() {
            return Some(current.clone());
        }
        match current {
            Value::Mapping(map) => {
                if let Some(key) = map.get(keys[0]) {
                    return self.resolve(key, &keys[1..]);
                }
            }
            _ => {}
        }
        None
    }
}

#[async_trait]
impl config::Factory<Config> for Config {}

impl config::Provider for Config {
    fn get_mut_log(&mut self) -> &mut config::LogConfig {
        self.base.log.as_mut().unwrap()
    }

    fn serialized(&self) -> Option<Value> {
        serde_yaml::to_value(self).ok()
    }
}
