extern crate toolshed_runner;

mod args;
mod config;
mod repo;
mod request;
mod runner;

#[cfg(test)]
mod test_helpers;
#[cfg(test)]
mod test_macros;

pub const DEFAULT_REPO: &str = "envoyproxy/envoy";

#[tokio::main]
#[allow(dead_code)]
async fn main() {
    runner::main().await;
}
