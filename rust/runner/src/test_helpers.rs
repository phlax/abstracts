use crate::args::Args;
use crate::config::Config;
use crate::repo::RepoConfig;
use crate::request::Request;
use crate::runner::Runner;
use std::collections::HashMap;
use std::error::Error;
use std::sync::{Arc, Mutex};
use toolshed_runner::{args, config};

pub struct MockManager {
    pub calls: Arc<Mutex<HashMap<String, Vec<String>>>>,
}

impl MockManager {
    pub fn new() -> Self {
        Self {
            calls: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    pub fn get(&self, key: &str) -> Vec<String> {
        let mut calls = self.calls.lock().unwrap();
        calls
            .entry(key.to_string())
            .or_insert_with(Vec::new)
            .to_vec()
    }

    pub fn clear(&self, key: &str) {
        let mut calls = self.calls.lock().unwrap();
        calls.insert(key.to_string(), Vec::new());
    }

    pub fn push(&self, key: &str, value: &str) {
        let mut calls = self.calls.lock().unwrap();
        calls
            .entry(key.to_string())
            .or_insert_with(Vec::new)
            .to_vec();
        let vec = calls.get_mut(key).unwrap();
        vec.push(value.to_string());
    }

    pub fn get_args(&self) -> Args {
        let config = "TESTCONFIG".to_string();
        let base = args::BaseArgs {
            config,
            log_level: Some(config::LogLevel::Trace.to_string()),
        };
        let repo = Some("TESTOWNER/TESTREPO".to_string());
        Args { base, repo }
    }

    pub async fn get_config(
        &self,
        args: Box<dyn args::Provider + Send + Sync>,
    ) -> Result<Config, Box<dyn Error + Send + Sync>> {
        let level = config::LogLevel::Trace;
        let log = Some(config::LogConfig { level });
        let base = config::BaseConfig { log };
        let name = "TESTOWNER/TESTREPO".to_string();
        let token = Some("TESTTOKEN".to_string());
        let repo = RepoConfig { name, token };
        Ok(Config { base, repo })
    }

    pub fn get_request(&self, config: Config, name: Option<String>) -> Request {
        let _name = if let Some(_name) = name {
            _name
        } else {
            "".to_string()
        };
        Request {
            config,
            name: _name,
        }
    }

    pub fn get_runner(&self, request: Request) -> Runner {
        Runner { request }
    }

    pub fn mock_args(&self, key: &str) -> Args {
        self.push(&key, "Args::parse");
        self.get_args()
    }

    pub async fn mock_config(
        &self,
        key: &str,
        args: Box<dyn args::Provider + Send + Sync>,
    ) -> Result<Config, Box<dyn Error + Send + Sync>> {
        self.push(&key, &format!("Config::from_yaml {:?}", args));
        self.get_config(args).await
    }

    pub fn mock_request(&self, key: &str, config: Config, name: Option<String>) -> Request {
        self.push(&key, &format!("Request::new {:?} {:?}", config, name));
        self.get_request(config, name)
    }

    pub fn mock_runner(&self, key: &str, request: Request) -> Runner {
        self.push(&key, &format!("Runner::new {:?}", request));
        self.get_runner(request)
    }

    pub async fn mock_run(
        &self,
        _self: &Runner,
        key: &str,
    ) -> Result<(), Box<dyn Error + Send + Sync>> {
        self.push(&key, &format!("runner.run {:?}", _self));
        Ok(())
    }

    pub fn reset_calls(&self, key: String) {
        let mut calls = self.get(&key);
        calls.clear();
    }
}
