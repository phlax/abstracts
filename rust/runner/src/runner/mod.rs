use crate::request::Request;
use crate::{config, EmptyResult};
use async_trait::async_trait;
use std::any::Any;
use std::collections::HashMap;
use std::env;
use std::future::Future;
use std::pin::Pin;
use std::sync::Arc;

pub type CommandFn = Arc<
    dyn Fn(&Box<dyn Runner>) -> Pin<Box<dyn Future<Output = EmptyResult> + Send>> + Send + Sync,
>;
pub type CommandsFn<'a> = HashMap<&'a str, CommandFn>;

pub trait Factory<T, R>: Send + Sync
where
    T: Runner + Sized,
    R: Request + Sized,
{
    fn new(request: R) -> Self;
}

#[macro_export]
macro_rules! runner {
    ($request:ident, { $( $cmd_name:literal => $cmd_fn:expr ),* $(,)? }) => {

        fn as_any(&self) -> &dyn std::any::Any {
            self
        }

        fn get_request(&self) -> &dyn toolshed_runner::request::Request {
            &self.$request
        }

        fn get_commands(&self) -> toolshed_runner::runner::CommandsFn {
            let mut commands: toolshed_runner::runner::CommandsFn = HashMap::new();
            $(
                commands.insert($cmd_name, Arc::new(|s: &Box<dyn toolshed_runner::runner::Runner>| {
                    if let Some(s) = s.as_any().downcast_ref::<Self>() {
                        let s = s.clone();
                        Box::pin(async move {$cmd_fn(&s).await})
                    } else {
                        panic!("Failed to downcast to Runner");
                    }
                }));
            )*
            commands
        }
    };
}

#[async_trait]
pub trait Runner: Any + Send + Sync {
    fn as_any(&self) -> &dyn Any;
    fn get_commands(&self) -> CommandsFn;
    fn get_request(&self) -> &dyn Request;
    async fn handle(&self) -> EmptyResult;

    fn get_command(&self, name: &str) -> CommandFn {
        self.get_commands()
            .get(name)
            .expect("No such command")
            .clone()
    }

    async fn run(&self) -> EmptyResult {
        if let Some(level) = self.get_request().get_config().get("log.level") {
            if let Some(level_str) = level.to_str() {
                if let Ok(parsed_level) = serde_yaml::from_str::<config::LogLevel>(&level_str) {
                    let _ = self.start_log(parsed_level);
                } else {
                    return Err("Log level is not a valid LogLevel".into());
                }
            }
        }
        self.handle().await
    }

    fn start_log(&self, level: config::LogLevel) -> EmptyResult {
        env::set_var("RUST_LOG", level.to_string());
        env_logger::init();
        Ok(())
    }
}
