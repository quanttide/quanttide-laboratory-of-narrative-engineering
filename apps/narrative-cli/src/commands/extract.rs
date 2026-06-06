use crate::contract::{CoverageReport, ExtractResult};
use crate::llm;
use crate::prompts;

pub fn run(
    scene_path: &str,
    motif_profile_path: Option<&str>,
    output_path: Option<&str>,
) -> Result<(), Box<dyn std::error::Error>> {
    let scene = crate::contract::read_scene(scene_path)?;
    let article_name = std::path::Path::new(scene_path)
        .file_stem()
        .and_then(|s| s.to_str())
        .unwrap_or("untitled");

    let prompt = prompts::build_motif_extract_prompt(&scene, article_name);
    println!("  提取母题...");
    let json = llm::call_llm_json(&prompt, "你是一个专业的叙事学分析助手。只输出 JSON。", 0.3)?;

    let motifs: Vec<crate::contract::ExtractedMotif> = json["motifs"]
        .as_array()
        .map(|arr| {
            arr.iter()
                .map(|m| crate::contract::ExtractedMotif {
                    title: m["title"].as_str().unwrap_or("").to_string(),
                    description: m["description"].as_str().unwrap_or("").to_string(),
                    weight: m["weight"].as_u64().unwrap_or(5) as u32,
                    evidence: m["evidence"]
                        .as_array()
                        .map(|e| e.iter().filter_map(|v| v.as_str().map(String::from)).collect())
                        .unwrap_or_default(),
                })
                .collect()
        })
        .unwrap_or_default();

    let coverage = if let Some(profile_path) = motif_profile_path {
        let profile = crate::contract::load_motif_profile(profile_path)?;
        let total = profile.motifs.len();
        let target_titles: Vec<&str> = profile.motifs.iter().map(|m| m.title.as_str()).collect();
        let mut matched = 0;
        for m in &motifs {
            for t in &target_titles {
                if m.title.contains(t) || t.contains(&m.title) {
                    matched += 1;
                    break;
                }
            }
        }
        Some(CoverageReport {
            matched,
            total,
            rate: if total > 0 { matched as f64 / total as f64 } else { 0.0 },
        })
    } else {
        None
    };

    let result = ExtractResult { motifs, coverage };

    let output = serde_json::to_string_pretty(&result)?;
    if let Some(path) = output_path {
        std::fs::write(path, &output)?;
        println!("  → {}", path);
    } else {
        println!("{}", output);
    }

    Ok(())
}
