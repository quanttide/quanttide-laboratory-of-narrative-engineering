use crate::contract::{GapEntry, GapReport, Suggestion};
use crate::llm;
use crate::prompts;

pub fn run(
    scene_path: &str,
    motif_profile_path: &str,
    output_path: Option<&str>,
    directions: &[String],
) -> Result<(), Box<dyn std::error::Error>> {
    let scene = crate::contract::read_scene(scene_path)?;
    let profile = crate::contract::load_motif_profile(motif_profile_path)?;
    let article_name = std::path::Path::new(scene_path)
        .file_stem()
        .and_then(|s| s.to_str())
        .unwrap_or("untitled");

    let prompt = prompts::build_gap_analysis_prompt(&scene, article_name, &profile, directions);
    println!("  分析母题缝隙...");
    let json = llm::call_llm_json(&prompt, "你是一个创作顾问。只输出 JSON。", 0.7)?;

    let gaps: Vec<GapEntry> = json["gaps"]
        .as_array()
        .map(|arr| {
            arr.iter()
                .map(|g| {
                    let attribution = g.get("attribution").map(|a| crate::contract::Attribution {
                        gap_types: a["gap_types"]
                            .as_array()
                            .map(|t| t.iter().filter_map(|v| v.as_str().map(String::from)).collect())
                            .unwrap_or_default(),
                        reasoning: a["reasoning"].as_str().unwrap_or("").to_string(),
                    });
                    let suggestions = g.get("suggestions").map(|suggs| {
                        suggs
                            .as_array()
                            .map(|arr| {
                                arr.iter()
                                    .map(|s| Suggestion {
                                        direction: s["direction"].as_str().unwrap_or("").to_string(),
                                        text: s["text"].as_str().unwrap_or("").to_string(),
                                        feasibility: None,
                                        reverse_risk: s["reverse_risk"].as_u64().map(|v| v as u32),
                                    })
                                    .collect()
                            })
                            .unwrap_or_default()
                    });

                    GapEntry {
                        motif: g["motif"].as_str().unwrap_or("").to_string(),
                        status: g["status"].as_str().unwrap_or("missing").to_string(),
                        target_weight: g["target_weight"].as_u64().unwrap_or(5) as u32,
                        attribution,
                        suggestions,
                    }
                })
                .collect()
        })
        .unwrap_or_default();

    let report = GapReport { gaps };
    let output = serde_json::to_string_pretty(&report)?;

    if let Some(path) = output_path {
        std::fs::write(path, &output)?;
        println!("  → {}", path);
    } else {
        println!("{}", output);
    }

    Ok(())
}
