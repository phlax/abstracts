use crate::DEFAULT_REPO;
use octocrab::models::Repository;
use octocrab::Octocrab;
use serde::{
    Deserialize,
    Serialize};

pub struct Repo {
    organization: String,
    name: String,
    repo: Option<Repository>,
}

impl Repo {
    pub async fn new (name: String) -> Repo {
        let parts: Vec<String> = name.split('/').map(String::from).collect();
        if parts.len() != 2 {
            panic!("Invalid repository format, expected 'owner/repo'");
        }
        let organization = parts[0].clone();
        let name = parts[1].clone();
        let repo = Some(Repo::fetch_repo(&organization, &name).await);
        Repo { organization, repo, name }
    }

    async fn fetch_repo(organization: &str, name: &str) -> Repository {
        let octocrab = Octocrab::builder().build().unwrap();
        octocrab.repos(organization, name).get().await.unwrap()
    }

    pub async fn stars (&self) {
        println!(
            "Repo({}/{}): {}",
            self.organization,
            self.name,
            self.repo.as_ref().unwrap().stargazers_count.unwrap_or(0));
    }
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct RepoConfig {
    #[serde(default = "RepoConfig::default_repo_name")]
    pub name: String,
    pub token: Option<String>,
}

impl RepoConfig {
    pub fn default_repo() -> RepoConfig {
        RepoConfig {
            name: RepoConfig::default_repo_name(),
            token: None,
        }
    }

    fn default_repo_name() -> String {
        DEFAULT_REPO.to_string()
    }
}
