use crate::args::Args;
use crate::config::Config;
use crate::repo::Repo;
use crate::request::Request;
use async_trait::async_trait;
use clap::Parser;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Arc;
#[allow(unused_imports)]
use toolshed_runner::{config::Factory as _, runner::Runner as _};
use toolshed_runner::{request, runner, EmptyResult};

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct Runner {
    pub request: Request,
}

impl Runner {
    async fn cmd_default(&self) -> EmptyResult {
        println!("DEFAULT");
        Ok(())
    }

    async fn cmd_stars(&self) -> EmptyResult {
        let name: String = self.request.config.get("repo.name").unwrap();
        let repo = Repo::new(name).await;
        repo.stars().await;
        Ok(())
    }
}

impl runner::Factory<Runner, Request> for Runner {
    fn new(request: Request) -> Self {
        Self { request }
    }
}

#[async_trait]
impl runner::Runner for Runner {
    runner!(
    request,
    {
        "stars" => Self::cmd_stars,
        "default" => Self::cmd_default,
    });

    async fn handle(&self) -> EmptyResult {
        self.get_command(self.get_request().get_name())(
            &(Box::new(self.clone()) as Box<dyn runner::Runner>),
        )
        .await
    }
}

#[allow(dead_code)]
pub async fn main() {
    let args = Args::parse();
    let config = Config::from_yaml(Box::new(args)).await.unwrap();
    let request =
        <Request as request::Factory<Request, Config>>::new(*config, Some("stars".to_string()));
    let runner = <Runner as runner::Factory<Runner, Request>>::new(request);
    runner.run().await.unwrap();
    ()
}

#[cfg(test)]
mod tests {
    extern crate guerrilla;

    use super::*;
    use crate::runner::Runner;
    use crate::test_helpers::MockManager;
    // use env_logger;
    use serial_test::serial;
    use std::env;
    use std::error::Error;
    use std::future::Future;
    use std::pin::Pin;
    use toolshed_runner::config;
    #[allow(unused_imports)]
    use toolshed_runner::request::Request as _;
    #[allow(unused_imports)]
    use toolshed_runner::runner::Runner as _;

    static MANAGER: once_cell::sync::Lazy<MockManager> =
        once_cell::sync::Lazy::new(|| MockManager::new());

    async fn _handle(testid: &str, _self: &Runner) -> Result<(), Box<dyn Error + Send + Sync>> {
        MANAGER.push(testid, "Runner.handle");
        Ok(())
    }

    fn _env_logger(testid: &str) {
        MANAGER.push(testid, &format!("env_logger::init"));
    }

    fn _get_bad(testid: &str, _self: &Config, key: &str) -> Option<config::LogLevel> {
        MANAGER.push(testid, &format!("Config.get {:?}", key));
        None
    }

    fn _get(testid: &str, _self: &Config, key: &str) -> Option<config::LogLevel> {
        MANAGER.push(testid, &format!("Config.get {:?}", key));
        Some(config::LogLevel::Info)
    }

    fn _start_log(
        testid: &str,
        _self: &Runner,
        level: config::LogLevel,
    ) -> Result<(), Box<dyn Error + Send + Sync>> {
        MANAGER.push(testid, &format!("Runner.start_log {:?}", level.to_string()));
        Ok(())
    }

    #[tokio::test(flavor = "multi_thread")]
    #[serial]
    async fn test_runner_run() {
        let testid = "lib0";
        let expected = vec!["Runner.start_log \"trace\"", "Runner.handle"];

        let config = MANAGER
            .get_config()
            .await
            .expect("Failed to get config from MANAGER");
        let request = MANAGER.get_request(config, Some("stars".to_string()));
        let runner = MANAGER.get_runner(request);

        let guards = vec![
            guerrilla::patch1(Runner::handle, |_self| {
                Box::pin(_handle("lib0", _self))
                    as Pin<
                        Box<dyn Future<Output = Result<(), Box<dyn Error + Send + Sync>>> + Send>,
                    >
            }),
            guerrilla::patch2(Config::get, |_self, key| _get("lib0", _self, key)),
            guerrilla::patch2(Runner::start_log, |_self, level| {
                _start_log("lib0", _self, level)
            }),
        ];
        let result = runner.run().await;
        assert!(
            matches!(result, Ok(())),
            "Expected run() to return Ok(()), but it returned {:?}",
            result
        );
        let calls = MANAGER.get("lib0");
        assert_eq!(*calls, expected);

        drop(guards);
        MANAGER.clear(testid);
    }

    // #[tokio::test(flavor = "multi_thread")]
    // #[serial]
    #[allow(dead_code)]
    async fn test_runner_run_nolog() {
        let testid = "lib1";
        let expected = vec!["Config.get \"log.level\""];

        let config = MANAGER
            .get_config()
            .await
            .expect("Failed to get config from MANAGER");
        let request = MANAGER.get_request(config, Some("stars".to_string()));
        let runner = MANAGER.get_runner(request);
        let guards = vec![
            guerrilla::patch1(Runner::handle, |_self| {
                Box::pin(_handle("lib1", _self))
                    as Pin<
                        Box<dyn Future<Output = Result<(), Box<dyn Error + Send + Sync>>> + Send>,
                    >
            }),
            guerrilla::patch2(Config::get, |_self, key| _get_bad("lib1", _self, key)),
            guerrilla::patch2(Runner::start_log, |_self, level| {
                _start_log("lib1", _self, level)
            }),
        ];
        assert!(runner.run().await.is_err());

        drop(guards);
        let calls = MANAGER.get(testid);
        assert_eq!(*calls, expected);
        MANAGER.clear(testid);
    }

    #[tokio::test(flavor = "multi_thread")]
    #[serial]
    async fn test_runner_run_startlog() {
        let testid = "lib2";
        let expected = vec!["env_logger::init"];

        let config = MANAGER
            .get_config()
            .await
            .expect("Failed to get config from MANAGER");
        let request = MANAGER.get_request(config, Some("stars".to_string()));
        let runner = MANAGER.get_runner(request);
        let guards = vec![
            guerrilla::patch1(Runner::handle, |_self| {
                Box::pin(_handle("lib2", _self))
                    as Pin<
                        Box<dyn Future<Output = Result<(), Box<dyn Error + Send + Sync>>> + Send>,
                    >
            }),
            guerrilla::patch2(Config::get, |_self, key| _get_bad("lib2", _self, key)),
            guerrilla::patch0(env_logger::init, || _env_logger("lib2")),
        ];
        assert!(env::var("RUST_LOG").is_err());
        assert!(runner.start_log(config::LogLevel::Debug).is_ok());
        assert!(env::var("RUST_LOG").expect("Log not set") == "debug");

        drop(guards);
        let calls = MANAGER.get(testid);
        assert_eq!(*calls, expected);
        MANAGER.clear(testid);
    }
}
