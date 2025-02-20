#[macro_export]
macro_rules! patched {
    ($manager:expr, $key:expr, $fun:expr, $expected:expr) => {
        fn get_patches() -> Vec<guerrilla::PatchGuard> {
            vec![
                guerrilla::patch0(crate::args::Args::parse, || MANAGER.mock_args($key)),
                guerrilla::patch1(crate::config::Config::from_yaml, |args| {
                    Box::pin(MANAGER.mock_config($key, args))
                        as Pin<
                            Box<
                                dyn Future<
                                        Output = Result<
                                            crate::config::Config,
                                            Box<dyn Error + Send + Sync>,
                                        >,
                                    > + Send,
                            >,
                        >
                }),
                guerrilla::patch2(crate::request::Request::new, |config, name| {
                    MANAGER.mock_request($key, config, name)
                }),
                guerrilla::patch1(crate::runner::Runner::new, |request| {
                    MANAGER.mock_runner($key, request)
                }),
                guerrilla::patch1(crate::runner::Runner::run, |_self| {
                    Box::pin(MANAGER.mock_run(_self, $key))
                        as Pin<
                            Box<
                                dyn Future<Output = Result<(), Box<dyn Error + Send + Sync>>>
                                    + Send,
                            >,
                        >
                }),
            ]
        }
        let patches = get_patches();
        $fun;
        let calls = $manager.get(&$key);
        assert_eq!(*calls, $expected);
        drop(patches);
    };
}
