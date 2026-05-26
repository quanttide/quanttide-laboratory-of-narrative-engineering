use pr4xis::engine::{Action, Engine, Precondition, PreconditionResult, Situation};

use crate::contract::{Contract, ToEntry};

// ── 状态 ──

#[derive(Clone, Debug, PartialEq)]
pub struct WritingSituation {
    pub stage: String,
    pub cycle: u32,
    pub consecutive_review: u32,
}

impl Situation for WritingSituation {
    fn describe(&self) -> String {
        format!("stage={}, cycle={}, consecutive_review={}", self.stage, self.cycle, self.consecutive_review)
    }
    fn is_terminal(&self) -> bool { self.stage == "finalDraft" }
}

// ── 动作 ──

#[derive(Clone, Debug)]
pub struct WritingAction {
    pub via: String,
    pub to: String,
}

impl Action for WritingAction {
    type Sit = WritingSituation;
    fn describe(&self) -> String { format!("--{}--> {}", self.via, self.to) }
}

// ── 守卫 ──

#[derive(Debug)]
struct MaxGuard { via: String, var: String, max: u32, rule: String }

impl Precondition<WritingAction> for MaxGuard {
    fn check(&self, sit: &WritingSituation, act: &WritingAction) -> PreconditionResult {
        if act.via != self.via {
            return PreconditionResult::satisfied(&self.rule, "n/a");
        }
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

// ── 转换函数 ──

pub fn apply_transition(sit: &WritingSituation, via: &str, to: &str) -> WritingSituation {
    let mut next = sit.clone();
    next.stage = to.into();
    match via {
        "review" => next.consecutive_review += 1,
        "reflect" => next.consecutive_review = 0,
        "rewrite" => { next.cycle += 1; next.consecutive_review = 0; }
        _ => { next.cycle = 0; next.consecutive_review = 0; }
    }
    next
}

// ── 引擎工厂 ──

pub fn build_engine(contract: &Contract) -> Engine<WritingAction> {
    let mut pre: Vec<Box<dyn Precondition<WritingAction>>> = vec![];

    for (id, stage) in &contract.stages {
        let expand = contract.expand.as_ref().and_then(|e| e.get(id));
        if let Some(to) = &stage.to {
            for entry in to {
                if let ToEntry::SelfLoop { name } = entry {
                    build_self_guards(name, expand, &mut pre, id);
                }
            }
        }
        if let Some(cfg) = expand.and_then(|e| e.done.as_ref()).and_then(|d| d.values().next()) {
            if let Some(min) = cfg.min_cycle {
                pre.push(Box::new(MinCycleGuard { via: "finalize".into(), min, rule: format!("{}.done.min_cycle", id) }));
            }
        }
    }

    let apply = |sit: &WritingSituation, act: &WritingAction| -> Result<WritingSituation, String> {
        Ok(apply_transition(sit, &act.via, &act.to))
    };

    Engine::new(WritingSituation { stage: "material".into(), cycle: 0, consecutive_review: 0 }, pre, apply)
}

fn build_self_guards(name: &str, expand: Option<&crate::contract::PerStageExpand>, pre: &mut Vec<Box<dyn Precondition<WritingAction>>>, id: &str) {
    let cfg = match expand.and_then(|e| e.self_loops.as_ref()).and_then(|s| s.get(name)) {
        Some(c) => c,
        None => return,
    };
    if let Some(max) = cfg.max {
        let var = match name { "rewrite" => "cycle", "review" => "consecutive_review", _ => name, };
        pre.push(Box::new(MaxGuard { via: name.into(), var: var.into(), max, rule: format!("{}.{}.max", id, name) }));
    }
    if let Some(mc) = cfg.max_consecutive {
        pre.push(Box::new(MaxGuard { via: name.into(), var: "consecutive_review".into(), max: mc, rule: format!("{}.{}.max_consecutive", id, name) }));
    }
}

#[cfg(kani)]
mod kani_proofs {
    use super::*;

    #[kani::proof]
    fn rewrite_increments_cycle() {
        let sit = WritingSituation {
            stage: "firstDraft".into(),
            cycle: kani::any(),
            consecutive_review: kani::any(),
        };
        let next = apply_transition(&sit, "rewrite", "firstDraft");
        assert!(next.cycle == sit.cycle.wrapping_add(1));
        assert_eq!(next.consecutive_review, 0);
    }

    #[kani::proof]
    fn review_increments_consecutive() {
        let sit = WritingSituation {
            stage: "firstDraft".into(),
            cycle: kani::any(),
            consecutive_review: kani::any(),
        };
        let next = apply_transition(&sit, "review", "firstDraft");
        assert_eq!(next.cycle, sit.cycle);
        assert_eq!(next.consecutive_review, sit.consecutive_review.wrapping_add(1));
    }

    #[kani::proof]
    fn reflect_resets_consecutive() {
        let sit = WritingSituation {
            stage: "firstDraft".into(),
            cycle: kani::any(),
            consecutive_review: kani::any(),
        };
        let next = apply_transition(&sit, "reflect", "firstDraft");
        assert_eq!(next.cycle, sit.cycle);
        assert_eq!(next.consecutive_review, 0);
    }
}
