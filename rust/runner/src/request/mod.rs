use crate::config;

pub trait Factory<T, C>: Send + Sync
where
    T: Request + Sized,
    C: config::Provider + Sized,
{
    fn new(config: C, name: Option<String>) -> Self;
}

pub trait Request: Send + Sync {
    fn get_config(&self) -> Box<&dyn config::Provider>;
    fn get_name(&self) -> &str;
}
