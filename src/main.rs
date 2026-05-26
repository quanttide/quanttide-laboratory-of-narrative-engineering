// 叙事工程实验室 — 写作工作流 CLI
//
// cargo run -- [contract-path]

use narrative_engineering::workflow::{build_engine, WritingAction};
use narrative_engineering::Contract;
use pr4xis::engine::{EngineError, Situation};

fn run_demo(path: &str) -> Result<(), Box<dyn std::error::Error>> {
    let contract = Contract::from_file(path)?;
    let mut eng = build_engine(&contract);

    println!("写作工作流引擎 (narrative-engineering)\n");
    println!("Initial: {}\n", eng.situation().describe());

    // 标准写作流程 demo
    let steps = [
        ("to_outline", "outline"),
        ("to_firstDraft", "firstDraft"),
        ("review", "firstDraft"),
        ("reflect", "firstDraft"),
        ("rewrite", "firstDraft"),
        ("review", "firstDraft"),
        ("reflect", "firstDraft"),
        ("rewrite", "firstDraft"),
        ("review", "firstDraft"),
        ("reflect", "firstDraft"),
        ("finalize", "finalDraft"),
    ];

    for (via, to) in &steps {
        match eng.next(WritingAction { via: via.to_string(), to: to.to_string() }) {
            Ok(e) => { eng = e; }
            Err(EngineError::Violated { violations, .. }) => {
                for v in violations { println!("  ✗ {:?}", v); }
                return Ok(());
            }
            Err(e) => { println!("  ✗ {:?}", e); return Ok(()); }
        }
        println!("  {}", eng.situation().describe());
    }

    println!("\nDone. Steps: {}, Terminal: {}", eng.step(), eng.situation().is_terminal());
    Ok(())
}

fn main() {
    let path = std::env::args().nth(1).unwrap_or_else(|| "contract.yaml".into());
    if let Err(e) = run_demo(&path) {
        eprintln!("Error: {}", e);
    }
}
