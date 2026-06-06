pub mod extract;
pub mod gap;
pub mod review;

use crate::contract::{MotifProfile, StyleProfile};

pub fn build_motif_extract_prompt(scene: &str, article_name: &str) -> String {
    let sample = scene.chars().take(3000).collect::<String>();
    format!(
        r#"分析下面名为《{name}》的文章，从中提取叙事母题（motif）。

母题定义：在叙事中反复出现的主题元素，包括具体意象、关系模式、行为习惯、
叙事惯例。母题与主题不同——主题是"说什么"（如"爱情"），母题是"怎么说"
（如"通过手势而非语言表达爱意"）。

要求：
- 提取 3-6 个母题
- 每个母题必须有来自原文的具体线索（2-3 条 evidence）
- weight 表示该母题在本文中的重要性（1-10）

输出格式（JSON）：
{{"motifs": [{{"title": "母题名","description": "一句话描述","weight": 5,"evidence": ["线索1"]}}]}}

文章内容：
{sample}"#,
        name = article_name,
    )
}

pub fn build_style_review_prompt(
    scene: &str,
    article_name: &str,
    style: &StyleProfile,
) -> String {
    let mut dims_text = String::new();
    for d in &style.dimensions {
        dims_text.push_str(&format!(
            "【{}】(confidence={})\n  {}\n",
            d.title,
            d.confidence.unwrap_or(0.5),
            d.description
        ));
        if let Some(clues) = &d.clues {
            dims_text.push_str(&format!("  clues: {}\n", clues.join("; ")));
        }
        if let Some(tensions) = &d.tensions {
            dims_text.push_str(&format!("  tensions: {}\n", tensions.join("; ")));
        }
        dims_text.push('\n');
    }

    let sample = scene.chars().take(2500).collect::<String>();
    format!(
        r#"风格框架「{title}」——{desc}

{dims_text}

请用以上审美框架评审下面名为《{name}》的场景。
严格评分标准：
- 8-10分：该场景在此维度上执行出色，明显超越系列平均水平
- 5-7分：场景符合维度定义，但只是"执行了"而非"执行好了"
- 1-4分：场景在此维度上明显不足

对每个维度评分（1-10），必须附原文引用作为证据。
只输出 JSON：{{"dimension_scores": [{{"dimension":"维度名","score":8,"evidence":["原文"],"note":"理由","tension":null}}]}}

场景文本：
{sample}"#,
        title = style.title.as_deref().unwrap_or(""),
        desc = style.description.as_deref().unwrap_or(""),
        name = article_name,
    )
}

pub fn build_gap_analysis_prompt(
    scene: &str,
    article_name: &str,
    motif_profile: &MotifProfile,
    directions: &[String],
) -> String {
    let target_titles: Vec<&str> = motif_profile.motifs.iter().map(|m| m.title.as_str()).collect();
    let sample = scene.chars().take(2500).collect::<String>();

    let dir_list = if directions.is_empty() {
        "增强, 引入, 借用, 转化, 克制, 反向".to_string()
    } else {
        directions.join(", ")
    };

    format!(
        r#"你是《{name}》的创作顾问。该系列的目标母题集：{targets}。

请完成以下两步：
1. 从场景中提取当前存在的母题
2. 对每个缺失的母题，从以下方向各生成一条具体的改写建议（80-150字）：
   {dirs}

输出格式（JSON）：
{{{{
  "gaps": [{{{{
    "motif": "母题名",
    "status": "missing",
    "target_weight": 9,
    "attribution": {{{{ "gap_types": ["scene_incompatible"], "reasoning": "原因" }}}},
    "suggestions": [{{"direction": "amplify", "text": "建议...", "paragraph_ref": "第X段"}}]
  }}}}
]}}}}

对于"反向"方向，额外包含 "reverse_risk": 1-3。

场景文本：
{sample}"#,
        name = article_name,
        targets = target_titles.join(", "),
        dirs = dir_list,
    )
}

pub fn build_diagnose_prompt(
    scene: &str,
    article_name: &str,
    style_scores: &[crate::contract::DimensionScore],
    motif_profile: &MotifProfile,
) -> String {
    let scores_text: String = style_scores
        .iter()
        .filter(|s| s.score <= 7)
        .map(|s| format!("- {} (score={}): {}", s.dimension, s.score, s.note))
        .collect::<Vec<_>>()
        .join("\n");

    let _weak_dims: Vec<&str> = style_scores
        .iter()
        .filter(|s| s.score <= 7)
        .map(|s| s.dimension.as_str())
        .collect();

    let target_titles: Vec<&str> = motif_profile.motifs.iter().map(|m| m.title.as_str()).collect();
    let sample = scene.chars().take(2000).collect::<String>();

    format!(
        r#"场景《{name}》风格评审中以下维度偏低：
{scores}

请分析每个弱维度的根因可能是什么（自由文本，不要参考预定义母题列表）。
对每个弱维度，描述"该维度偏弱最可能是因为缺少什么叙事元素"。
如果某个弱维度与叙事元素缺失无关（如纯技巧问题），说明原因。

输出JSON：{{"free_analysis":[{{"weak_dimension":"维度名","root_cause_hypothesis":"...","confidence":"high|medium|low"}}]}}

已知该系列的母题库：{targets}

对每个假设，判断它最接近哪个已知母题（如有）。不匹配则 related_missing_motif 留空。
每个母题最多关联 2 个弱维度。

最终输出JSON：{{{{"links":[{{"weak_dimension":"...","related_missing_motif":"...","confidence":"...","hypothesis":"...","combined_fix":"给出具体的改写建议(80-150字)"}}]}}}}

场景文本：
{sample}"#,
        name = article_name,
        scores = scores_text,
        targets = target_titles.join(", "),
    )
}
