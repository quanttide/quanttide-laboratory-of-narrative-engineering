use reqwest::blocking::Client;
use serde_json::Value;
use std::env;
use std::time::Duration;

const API_URL: &str = "https://api.deepseek.com/chat/completions";

fn api_key() -> String {
    env::var("DEEPSEEK_API_KEY").unwrap_or_default()
}

pub fn call_llm(
    prompt: &str,
    system: &str,
    temperature: f64,
) -> Result<String, Box<dyn std::error::Error>> {
    let client = Client::builder()
        .timeout(Duration::from_secs(180))
        .build()?;

    let body = serde_json::json!({
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
    });

    let resp = client
        .post(API_URL)
        .header("Authorization", format!("Bearer {}", api_key()))
        .header("Content-Type", "application/json")
        .json(&body)
        .send()?;

    let json: Value = resp.json()?;
    let content = json["choices"][0]["message"]["content"]
        .as_str()
        .unwrap_or("")
        .to_string();
    Ok(content)
}

pub fn call_llm_json(
    prompt: &str,
    system: &str,
    temperature: f64,
) -> Result<Value, Box<dyn std::error::Error>> {
    let raw = call_llm(prompt, system, temperature)?;
    let cleaned = clean_json(&raw);
    Ok(serde_json::from_str(&cleaned)?)
}

fn clean_json(raw: &str) -> String {
    let mut s = raw.trim().to_string();
    if s.starts_with("```") {
        if let Some(pos) = s.find('\n') {
            s = s[pos + 1..].to_string();
        }
        if s.ends_with("```") {
            s = s[..s.len() - 3].trim().to_string();
        }
    }
    s
}
