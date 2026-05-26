use narrative_engineering::workflow::{apply_transition, WritingSituation};
use pr4xis::engine::Situation;

#[test]
fn situation_starts_at_material() {
    let sit = WritingSituation { stage: "material".into(), cycle: 0, consecutive_review: 0 };
    assert_eq!(sit.stage, "material");
    assert!(!sit.is_terminal());
}

#[test]
fn final_draft_is_terminal() {
    let sit = WritingSituation { stage: "finalDraft".into(), cycle: 0, consecutive_review: 0 };
    assert!(sit.is_terminal());
}

#[test]
fn plain_transition_resets_counters() {
    let sit = WritingSituation { stage: "material".into(), cycle: 3, consecutive_review: 2 };
    let next = apply_transition(&sit, "to_outline", "outline");
    assert_eq!(next.stage, "outline");
    assert_eq!(next.cycle, 0);
    assert_eq!(next.consecutive_review, 0);
}

#[test]
fn review_increments_consecutive() {
    let sit = WritingSituation { stage: "firstDraft".into(), cycle: 0, consecutive_review: 0 };
    let next = apply_transition(&sit, "review", "firstDraft");
    assert_eq!(next.consecutive_review, 1);
}

#[test]
fn reflect_resets_consecutive() {
    let sit = WritingSituation { stage: "firstDraft".into(), cycle: 2, consecutive_review: 3 };
    let next = apply_transition(&sit, "reflect", "firstDraft");
    assert_eq!(next.consecutive_review, 0);
    assert_eq!(next.cycle, 2);
}

#[test]
fn rewrite_increments_cycle() {
    let sit = WritingSituation { stage: "firstDraft".into(), cycle: 1, consecutive_review: 3 };
    let next = apply_transition(&sit, "rewrite", "firstDraft");
    assert_eq!(next.cycle, 2);
    assert_eq!(next.consecutive_review, 0);
}

#[test]
fn load_contract_from_file() {
    let contract = narrative_engineering::Contract::from_file("contract.yaml").unwrap();
    assert!(contract.stages.contains_key("material"));
    assert!(contract.stages.contains_key("finalDraft"));
    assert!(contract.expand.is_some());
}

#[test]
fn build_engine_from_contract() {
    let contract = narrative_engineering::Contract::from_file("contract.yaml").unwrap();
    let eng = narrative_engineering::workflow::build_engine(&contract);
    assert_eq!(eng.situation().stage, "material");
    assert_eq!(eng.step(), 0);
}

#[test]
fn full_pipeline() {
    use pr4xis::engine::EngineError;
    use narrative_engineering::workflow::{WritingAction, build_engine};

    let contract = narrative_engineering::Contract::from_file("contract.yaml").unwrap();
    let mut eng = build_engine(&contract);

    let steps = [
        ("to_outline", "outline"),
        ("to_firstDraft", "firstDraft"),
        ("rewrite", "firstDraft"),
        ("finalize", "finalDraft"),
    ];
    for (via, to) in &steps {
        eng = match eng.next(WritingAction { via: via.to_string(), to: to.to_string() }) {
            Ok(e) => e,
            Err(EngineError::Violated { violations, .. }) => {
                panic!("Unexpected violation at {}: {:?}", via, violations);
            }
            Err(e) => panic!("Unexpected error: {:?}", e),
        };
    }
    assert!(eng.situation().is_terminal());
    assert_eq!(eng.step(), 4);
}
