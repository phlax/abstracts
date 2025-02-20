use crate::args;
use async_trait::async_trait;
use serde::de::DeserializeOwned;
use serde::{Deserialize, Serialize};
use serde_yaml::{self, Value};
use std::any::Any;
use std::error::Error;
use std::fmt;
use std::fmt::Debug;
use std::sync::Arc;

pub trait ConfigValue: Debug + Send + Sync + Any {
    fn as_any(&self) -> &dyn Any;
    fn to_str(&self) -> Option<String> {
        None
    }
}

impl ConfigValue for Value {
    fn as_any(&self) -> &dyn Any {
        self
    }

    fn to_str(&self) -> Option<String> {
        match self {
            Value::String(s) => Some(s.clone()),
            _ => None,
        }
    }
}

pub trait Provider: Any + Send + Sync {
    fn get(&self, key: &str) -> Option<Box<dyn ConfigValue>> {
        self.get_value(key)
            .map(|v| Box::new(v) as Box<dyn ConfigValue>)
    }

    fn get_value(&self, key: &str) -> Option<Value> {
        let keys: Vec<&str> = key.split('.').collect();
        let serialized = self.serialized()?;
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

    fn get_mut_log(&mut self) -> &mut LogConfig;
    fn serialized(&self) -> Option<Value>;
}

#[async_trait]
pub trait Factory<T>
where
    T: Provider + DeserializeOwned + 'static + Send + Sync,
{
    async fn from_yaml(
        args: Box<dyn args::Provider + Send + Sync>,
    ) -> Result<Box<T>, Box<dyn Error + Send + Sync>> {
        let args = Arc::new(args);
        let yaml_result = Self::read_yaml(Arc::clone(&args)).await?;
        let config = Self::override_config(Arc::clone(&args), yaml_result).await?;
        Ok(config)
    }

    async fn override_config(
        args: Arc<Box<dyn args::Provider + Send + Sync>>,
        mut config: Box<T>,
    ) -> Result<Box<T>, Box<dyn Error + Send + Sync>> {
        if let Ok(env_log_level) = std::env::var("LOG_LEVEL") {
            if let Ok(parsed_level) = serde_yaml::from_str::<LogLevel>(&env_log_level) {
                config.get_mut_log().level = parsed_level;
            }
        }
        if let Some(log_level_override) = args.log_level() {
            if let Ok(parsed_level) = serde_yaml::from_str::<LogLevel>(&log_level_override) {
                config.get_mut_log().level = parsed_level;
            }
        }
        Ok(config)
    }

    async fn read_yaml(
        args: Arc<Box<dyn args::Provider + Send + Sync>>,
    ) -> Result<Box<T>, Box<dyn Error + Send + Sync>> {
        let config_str = args.config();
        let path = std::path::Path::new(&config_str);
        if !path.exists() {
            log::error!("Path does not exist: {}", path.display());
        }
        let file = std::fs::File::open(path)
            .map_err(|e| format!("Failed to open {}: {}", path.display(), e))?;
        let config = serde_yaml::from_reader(file)
            .map_err(|e| format!("Failed to parse YAML({}): {}", path.display(), e))?;
        Ok(config)
    }
}

impl LogConfig {
    fn default_log_level() -> LogLevel {
        LogLevel::Info
    }

    fn default_log() -> Option<LogConfig> {
        Some(LogConfig {
            level: Self::default_log_level(),
        })
    }
}

impl ToString for LogLevel {
    fn to_string(&self) -> String {
        match self {
            LogLevel::Error => "error".to_string(),
            LogLevel::Warning => "warning".to_string(),
            LogLevel::Info => "info".to_string(),
            LogLevel::Debug => "debug".to_string(),
            LogLevel::Trace => "trace".to_string(),
        }
    }
}

#[derive(Debug, Eq, Deserialize, Clone, Copy, PartialEq, Serialize)]
#[serde(rename_all = "lowercase")]
pub enum LogLevel {
    Error,
    Warning,
    Info,
    Debug,
    Trace,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct LogConfig {
    #[serde(default = "LogConfig::default_log_level")]
    pub level: LogLevel,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct BaseConfig {
    #[serde(default = "LogConfig::default_log")]
    pub log: Option<LogConfig>,
}

impl BaseConfig {
    pub fn log_level(&self) -> LogLevel {
        self.log
            .as_ref()
            .map(|log| log.level)
            .unwrap_or(LogLevel::Info)
    }
}

impl Provider for BaseConfig {
    fn get_mut_log(&mut self) -> &mut LogConfig {
        self.log.as_mut().unwrap()
    }

    fn serialized(&self) -> Option<Value> {
        serde_yaml::to_value(self).ok()
    }
}

impl fmt::Display for BaseConfig {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", serde_yaml::to_string(&self).ok().unwrap())
    }
}

impl fmt::Display for LogConfig {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", serde_yaml::to_string(&self).ok().unwrap())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashMap;

    impl Provider for LogConfig {
        fn get_mut_log(&mut self) -> &mut LogConfig {
            self
        }

        fn serialized(&self) -> Option<Value> {
            serde_yaml::to_value(self).ok()
        }
    }

    #[async_trait]
    impl Factory<LogConfig> for LogConfig {}

    #[async_trait]
    impl Factory<BaseConfig> for BaseConfig {}

    #[test]
    fn test_logconfig_yaml() {
        let yaml = "
level: warning
        ";
        let config = serde_yaml::from_str::<LogConfig>(yaml).expect("Unable to parse yaml");
        let display = format!("{}", config);
        assert_eq!(display.trim(), yaml.trim());
        assert_eq!(config.level, LogLevel::Warning);
    }

    #[test]
    fn test_logconfig_yaml_default() {
        let yaml = "
        ";
        let expected = "
level: info
        ";
        let config = serde_yaml::from_str::<LogConfig>(yaml).expect("Unable to parse yaml");
        let display = format!("{}", config);
        assert_eq!(display.trim(), expected.trim());
        assert_eq!(config.level, LogLevel::Info);
    }

    #[test]
    fn test_baseconfig_yaml() {
        let yaml = "
log:
  level: error
        ";
        let config = serde_yaml::from_str::<BaseConfig>(yaml).expect("Unable to parse yaml");
        let display = format!("{}", config);
        assert_eq!(display.trim(), yaml.trim());
        assert_eq!(config.log.unwrap().level, LogLevel::Error);
    }

    #[test]
    fn test_baseconfig_yaml_default() {
        let config = serde_yaml::from_str::<BaseConfig>("").expect("Unable to parse yaml");
        assert_eq!(config.log.unwrap().level, LogLevel::Info);
    }

    #[test]
    fn test_log_levels() {
        let map = HashMap::from([
            ("debug", LogLevel::Debug),
            ("error", LogLevel::Error),
            ("info", LogLevel::Info),
            ("trace", LogLevel::Trace),
            ("warning", LogLevel::Warning),
        ]);

        for (expected_str, log_level) in &map {
            assert_eq!(*expected_str, log_level.to_string());
        }
    }
}
