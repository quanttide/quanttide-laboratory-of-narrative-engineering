use serde::Deserialize;
use std::collections::HashMap;

#[derive(Debug, Deserialize, Clone)]
pub struct MotifProfile {
    pub series: Option<String>,
    pub title: Option<String>,
    pub description: Option<String>,
    pub motifs: Vec<Motif>,
}

#[derive(Debug, Deserialize, Clone)]
pub struct Motif {
    pub title: String,
    pub description: String,
    pub weight: u32,
}

#[derive(Debug, Deserialize, Clone)]
pub struct StyleProfile {
    pub name: Option<String>,
    pub title: Option<String>,
    pub description: Option<String>,
    pub dimensions: Vec<Dimension>,
    pub excerpts: Option<Vec<Excerpt>>,
}

#[derive(Debug, Deserialize, Clone)]
pub struct Dimension {
    pub title: String,
    pub description: String,
    pub confidence: Option<f64>,
    pub clues: Option<Vec<String>>,
    pub tensions: Option<Vec<String>>,
}

#[derive(Debug, Deserialize, Clone)]
pub struct Excerpt {
    pub paragraph: String,
    pub dimension: String,
    pub note: Option<String>,
}

#[derive(Debug, serde::Serialize, Clone)]
pub struct ExtractedMotif {
    pub title: String,
    pub description: String,
    pub weight: u32,
    pub evidence: Vec<String>,
}

#[derive(Debug, serde::Serialize, Clone)]
pub struct ExtractResult {
    pub motifs: Vec<ExtractedMotif>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub coverage: Option<CoverageReport>,
}

#[derive(Debug, serde::Serialize, Clone)]
pub struct CoverageReport {
    pub matched: usize,
    pub total: usize,
    pub rate: f64,
}

#[derive(Debug, serde::Serialize, Clone)]
pub struct DimensionScore {
    pub dimension: String,
    pub score: u32,
    pub evidence: Vec<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tension: Option<String>,
    pub note: String,
}

#[derive(Debug, serde::Serialize, Clone)]
pub struct ReviewResult {
    pub dimension_scores: Vec<DimensionScore>,
    pub average: Option<f64>,
    pub weak_dimensions: Option<Vec<String>>,
}

#[derive(Debug, serde::Serialize, Clone)]
pub struct GapReport {
    pub gaps: Vec<GapEntry>,
}

#[derive(Debug, serde::Serialize, Clone)]
pub struct GapEntry {
    pub motif: String,
    pub status: String,
    pub target_weight: u32,
    pub attribution: Option<Attribution>,
    pub suggestions: Option<Vec<Suggestion>>,
}

#[derive(Debug, serde::Serialize, Clone)]
pub struct Attribution {
    pub gap_types: Vec<String>,
    pub reasoning: String,
}

#[derive(Debug, serde::Serialize, Clone)]
pub struct Suggestion {
    pub direction: String,
    pub text: String,
    pub feasibility: Option<u32>,
    pub reverse_risk: Option<u32>,
}

#[derive(Debug, serde::Serialize, Clone)]
pub struct DiagnosisResult {
    pub links: Vec<DiagnosisLink>,
    pub style_motif_mapping: Option<HashMap<String, Vec<String>>>,
}

#[derive(Debug, serde::Serialize, Clone)]
pub struct DiagnosisLink {
    pub weak_dimension: String,
    pub score: Option<u32>,
    pub related_motif: Option<String>,
    pub confidence: Option<String>,
    pub hypothesis: Option<String>,
    pub combined_fix: Option<String>,
}

pub fn load_motif_profile(path: &str) -> Result<MotifProfile, Box<dyn std::error::Error>> {
    let content = std::fs::read_to_string(path)?;
    Ok(serde_yaml::from_str(&content)?)
}

pub fn load_style_profile(path: &str) -> Result<StyleProfile, Box<dyn std::error::Error>> {
    let content = std::fs::read_to_string(path)?;
    Ok(serde_yaml::from_str(&content)?)
}

pub fn read_scene(path: &str) -> Result<String, Box<dyn std::error::Error>> {
    let text = std::fs::read_to_string(path)?;
    let body: Vec<&str> = text
        .lines()
        .filter(|l| !l.starts_with("# "))
        .map(|l| if l.trim().is_empty() { " " } else { l })
        .collect();
    Ok(body.join("\n"))
}
