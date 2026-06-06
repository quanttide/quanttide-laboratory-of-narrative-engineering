use crate::contract::{DimensionScore, ReviewResult};
use crate::llm;
use crate::prompts;

pub fn run(
    scene_path: &str,
    style_path: &str,
    output_path: Option<&str>,
) -> Result<(), Box<dyn std::error::Error>> {
    let scene = crate::contract::read_scene(scene_path)?;
    let style = crate::contract::load_style_profile(style_path)?;
    let article_name = std::path::Path::new(scene_path)
        .file_stem()
        .and_then(|s| s.to_str())
        .unwrap_or("untitled");

    let prompt = prompts::build_style_review_prompt(&scene, article_name, &style);
    println!("  评审中...");
    let json = llm::call_llm_json(&prompt, "你是一个专业的文学评审。只输出 JSON。", 0.0)?;

    let scores: Vec<DimensionScore> = json["dimension_scores"]
        .as_array()
        .map(|arr| {
            arr.iter()
                .map(|s| DimensionScore {
                    dimension: s["dimension"].as_str().unwrap_or("").to_string(),
                    score: s["score"].as_u64().unwrap_or(5) as u32,
                    evidence: s["evidence"]
                        .as_array()
                        .map(|e| e.iter().filter_map(|v| v.as_str().map(String::from)).collect())
                        .unwrap_or_default(),
                    tension: s["tension"].as_str().map(String::from),
                    note: s["note"].as_str().unwrap_or("").to_string(),
                })
                .collect()
        })
        .unwrap_or_default();

    let total: u32 = scores.iter().map(|s| s.score).sum();
    let avg = if !scores.is_empty() {
        Some(total as f64 / scores.len() as f64)
    } else {
        None
    };

    let weak: Vec<String> = scores
        .iter()
        .filter(|s| s.score <= 7)
        .map(|s| s.dimension.clone())
        .collect();

    let result = ReviewResult {
        dimension_scores: scores,
        average: avg,
        weak_dimensions: if weak.is_empty() { None } else { Some(weak) },
    };

    let output = serde_json::to_string_pretty(&result)?;
    if let Some(path) = output_path {
        std::fs::write(path, &output)?;
        println!("  → {}", path);
    } else {
        println!("{}", output);
    }

    Ok(())
}
