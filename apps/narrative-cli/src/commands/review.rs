use crate::contract::{DiagnosisResult, DimensionScore};
use crate::llm;
use crate::prompts;

pub fn run(
    scene_path: &str,
    style_path: &str,
    motif_profile_path: Option<&str>,
    output_path: Option<&str>,
) -> Result<(), Box<dyn std::error::Error>> {
    let scene = crate::contract::read_scene(scene_path)?;
    let style = crate::contract::load_style_profile(style_path)?;
    let article_name = std::path::Path::new(scene_path)
        .file_stem()
        .and_then(|s| s.to_str())
        .unwrap_or("untitled");

    // Step 1: Style review
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

    // Step 2: Two-step cross-diagnosis (if motif profile provided)
    let diagnosis = if let Some(motif_path) = motif_profile_path {
        let motif_profile = crate::contract::load_motif_profile(motif_path)?;

        // Step 2a: Free inference (no motif list)
        println!("  交叉诊断(1/2) 自由推断...");
        let free_prompt = prompts::build_free_inference_prompt(&scene, article_name, &scores);
        let free_json = llm::call_llm_json(&free_prompt, "你是一个叙事诊断专家。只输出 JSON。", 0.2)?;

        // Step 2b: Match against motif pool
        println!("  交叉诊断(2/2) 母题匹配...");
        let hypotheses = serde_json::to_string(&free_json)?;
        let match_prompt = prompts::build_motif_match_prompt(&hypotheses, &motif_profile);
        match llm::call_llm_json(&match_prompt, "你是一个叙事编辑。只输出 JSON。", 0.2) {
            Ok(diag_json) => {
                let links = diag_json["links"]
                    .as_array()
                    .map(|arr| {
                        arr.iter()
                            .map(|l| crate::contract::DiagnosisLink {
                                weak_dimension: l["weak_dimension"].as_str().unwrap_or("").to_string(),
                                score: None,
                                related_motif: l["related_missing_motif"].as_str().map(String::from),
                                confidence: l["confidence"].as_str().map(String::from),
                                hypothesis: l["hypothesis"].as_str().map(String::from),
                                combined_fix: l["combined_fix"].as_str().map(String::from),
                            })
                            .collect()
                    })
                    .unwrap_or_default();
                Some(DiagnosisResult {
                    links,
                    style_motif_mapping: None,
                })
            }
            Err(_) => None,
        }
    } else {
        None
    };

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

    let mut result = serde_json::json!({
        "dimension_scores": scores,
        "average": avg,
        "weak_dimensions": if weak.is_empty() { None } else { Some(weak) },
    });

    if let Some(d) = diagnosis {
        result["diagnosis"] = serde_json::json!(d);
    }

    let output = serde_json::to_string_pretty(&result)?;
    if let Some(path) = output_path {
        std::fs::write(path, &output)?;
        println!("  → {}", path);
    } else {
        println!("{}", output);
    }

    Ok(())
}
