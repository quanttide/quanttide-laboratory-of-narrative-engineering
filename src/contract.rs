use std::collections::HashMap;

#[derive(Debug, serde::Deserialize)]
pub struct Contract {
    pub stages: HashMap<String, Stage>,
    pub expand: Option<HashMap<String, PerStageExpand>>,
}

#[derive(Debug, serde::Deserialize)]
pub struct Stage {
    pub to: Option<Vec<ToEntry>>,
    pub done: Option<DoneTransition>,
}

#[derive(Debug, serde::Deserialize)]
pub struct DoneTransition {
    #[allow(dead_code)]
    pub to: String,
}

#[derive(Debug, serde::Deserialize)]
#[serde(untagged)]
pub enum ToEntry {
    #[allow(dead_code)]
    Plain(String),
    SelfLoop { #[serde(rename = "self")] name: String },
}

#[derive(Debug, serde::Deserialize, Default)]
pub struct PerStageExpand {
    #[serde(rename = "self")]
    pub self_loops: Option<HashMap<String, SelfExpand>>,
    pub done: Option<HashMap<String, DoneExpand>>,
}

#[derive(Debug, serde::Deserialize, Default)]
pub struct SelfExpand {
    pub max: Option<u32>,
    pub max_consecutive: Option<u32>,
}

#[derive(Debug, serde::Deserialize, Default)]
pub struct DoneExpand {
    pub min_cycle: Option<u32>,
}

impl Contract {
    pub fn from_file(path: &str) -> Result<Self, Box<dyn std::error::Error>> {
        let content = std::fs::read_to_string(path)?;
        Ok(serde_yaml::from_str(&content)?)
    }
}
