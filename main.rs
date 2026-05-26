// 写作工作流示例 — cargo run --example write

use pr4xis::engine::{Action, Engine, EngineError, Precondition, PreconditionResult, Situation};
use std::collections::HashMap;

#[derive(Clone, Debug, PartialEq)]
struct WritingSituation { stage: String, cycle: u32, consecutive_review: u32 }

impl Situation for WritingSituation {
    fn describe(&self) -> String {
        format!("stage={}, cycle={}, consecutive_review={}", self.stage, self.cycle, self.consecutive_review)
    }
    fn is_terminal(&self) -> bool { self.stage == "finalDraft" }
}

#[derive(Clone, Debug)]
struct WritingAction { via: String, to: String }

impl Action for WritingAction {
    type Sit = WritingSituation;
    fn describe(&self) -> String { format!("--{}--> {}", self.via, self.to) }
}

#[derive(Debug)]
struct MaxGuard { via: String, var: String, max: u32, rule: String }

impl Precondition<WritingAction> for MaxGuard {
    fn check(&self, sit: &WritingSituation, act: &WritingAction) -> PreconditionResult {
        if act.via != self.via { return PreconditionResult::satisfied(&self.rule, "n/a"); }
        let val = match self.var.as_str() {
            "cycle" => sit.cycle,
            "consecutive_review" => sit.consecutive_review,
            _ => return PreconditionResult::satisfied(&self.rule, "unknown"),
        };
        if val < self.max {
            PreconditionResult::satisfied(&self.rule, &format!("{}={} < {}", self.var, val, self.max))
        } else {
            PreconditionResult::violated(&self.rule, &format!("{}={} >= {}", self.var, val, self.max), &sit.describe(), &act.describe())
        }
    }
    fn describe(&self) -> &str { &self.rule }
}

#[derive(Debug)]
struct MinCycleGuard { via: String, min: u32, rule: String }

impl Precondition<WritingAction> for MinCycleGuard {
    fn check(&self, sit: &WritingSituation, act: &WritingAction) -> PreconditionResult {
        if act.via != self.via { return PreconditionResult::satisfied(&self.rule, "n/a"); }
        if sit.cycle >= self.min {
            PreconditionResult::satisfied(&self.rule, &format!("cycle={} >= {}", sit.cycle, self.min))
        } else {
            PreconditionResult::violated(&self.rule, &format!("cycle={} < {}", sit.cycle, self.min), &sit.describe(), &act.describe())
        }
    }
    fn describe(&self) -> &str { &self.rule }
}

#[derive(Debug, serde::Deserialize)]
struct Contract { stages: HashMap<String, Stage>, expand: Option<HashMap<String, PerStageExpand>> }

#[derive(Debug, serde::Deserialize)]
struct Stage { to: Option<Vec<ToEntry>>, done: Option<DoneTransition> }

#[derive(Debug, serde::Deserialize)]
struct DoneTransition { to: String }

#[derive(Debug, serde::Deserialize)]
#[serde(untagged)]
enum ToEntry { Plain(String), SelfLoop { #[serde(rename = "self")] name: String } }

#[derive(Debug, serde::Deserialize, Default)]
struct PerStageExpand {
    #[serde(rename = "self")]
    self_loops: Option<HashMap<String, SelfExpand>>,
    done: Option<HashMap<String, DoneExpand>>,
}

#[derive(Debug, serde::Deserialize, Default)]
struct SelfExpand { max: Option<u32>, max_consecutive: Option<u32> }

#[derive(Debug, serde::Deserialize, Default)]
struct DoneExpand { min_cycle: Option<u32> }

fn build_engine(contract: &Contract) -> Engine<WritingAction> {
    let mut pre: Vec<Box<dyn Precondition<WritingAction>>> = vec![];
    for (id, stage) in &contract.stages {
        let expand = contract.expand.as_ref().and_then(|e| e.get(id));
        if let Some(to) = &stage.to {
            for entry in to {
                if let ToEntry::SelfLoop { name } = entry {
                    if let Some(cfg) = expand.and_then(|e| e.self_loops.as_ref()).and_then(|s| s.get(name)) {
                        if let Some(max) = cfg.max {
                            let var = match name.as_str() { "rewrite" => "cycle", "review" => "consecutive_review", _ => name, };
                            pre.push(Box::new(MaxGuard { via: name.clone(), var: var.into(), max, rule: format!("{}.{}.max", id, name) }));
                        }
                        if let Some(mc) = cfg.max_consecutive {
                            pre.push(Box::new(MaxGuard { via: name.clone(), var: "consecutive_review".into(), max: mc, rule: format!("{}.{}.max_consecutive", id, name) }));
                        }
                    }
                }
            }
        }
        if let Some(_done) = &stage.done {
            if let Some(min) = expand.and_then(|e| e.done.as_ref()).and_then(|d| d.values().next()).and_then(|c| c.min_cycle) {
                pre.push(Box::new(MinCycleGuard { via: "finalize".into(), min, rule: format!("{}.done.min_cycle", id) }));
            }
        }
    }
    let apply = |sit: &WritingSituation, act: &WritingAction| -> Result<WritingSituation, String> {
        let mut next = sit.clone(); next.stage = act.to.clone();
        match act.via.as_str() {
            "review" => next.consecutive_review += 1,
            "reflect" => next.consecutive_review = 0,
            "rewrite" => { next.cycle += 1; next.consecutive_review = 0; }
            _ => { next.cycle = 0; next.consecutive_review = 0; }
        }
        Ok(next)
    };
    Engine::new(WritingSituation { stage: "material".into(), cycle: 0, consecutive_review: 0 }, pre, apply)
}

fn main() {
    let path = std::env::args().nth(1).unwrap_or_else(|| "examples/write/contract.yaml".into());
    let contract: Contract = match serde_yaml::from_str(&std::fs::read_to_string(&path).unwrap_or_default()) {
        Ok(c) => c,
        Err(_) => { eprintln!("Usage: cargo run --example write [contract.yaml]"); return; }
    };

    let mut eng = build_engine(&contract);
    println!("Initial: {}", eng.situation().describe());

    let demo: [(&str, &str); 11] = [
        ("to_outline","outline"), ("to_firstDraft","firstDraft"),
        ("review","firstDraft"), ("reflect","firstDraft"), ("rewrite","firstDraft"),
        ("review","firstDraft"), ("reflect","firstDraft"), ("rewrite","firstDraft"),
        ("review","firstDraft"), ("reflect","firstDraft"), ("finalize","finalDraft"),
    ];
    for &(via, to) in &demo {
        match eng.next(WritingAction { via: via.into(), to: to.into() }) {
            Ok(e) => { eng = e; }
            Err(EngineError::Violated { violations, .. }) => { for v in violations { println!("  ✗ {:?}", v); } return; }
            Err(e) => { println!("  ✗ {:?}", e); return; }
        }
        println!("  {}", eng.situation().describe());
    }
    println!("\nDone. Steps: {}, Terminal: {}", eng.step(), eng.situation().is_terminal());
}
