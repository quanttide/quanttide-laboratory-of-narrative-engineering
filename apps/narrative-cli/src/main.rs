use clap::{Parser, Subcommand};

#[derive(Parser)]
#[command(name = "narrative-cli")]
#[command(about = "QuantTide Narrative Engineering CLI", long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// 从场景中提取叙事母题 (p05)
    Extract {
        /// 场景文件路径
        #[arg(short, long)]
        scene: String,

        /// 目标母题配置文件（motif.yaml），用于对照计算覆盖率
        #[arg(short, long)]
        motif_profile: Option<String>,

        /// 输出文件路径
        #[arg(short, long)]
        output: Option<String>,
    },

    /// 用 style.yaml 框架评审场景 (p09)，可选交叉诊断 (p10)
    Review {
        /// 场景文件路径
        #[arg(short, long)]
        scene: String,

        /// style.yaml 配置文件路径
        #[arg(short = 'S', long)]
        style: String,

        /// motif.yaml 配置文件路径（可选，提供则触发 p10 交叉诊断）
        #[arg(short = 'M', long)]
        motif_profile: Option<String>,

        /// 输出文件路径
        #[arg(short, long)]
        output: Option<String>,
    },

    /// 分析母题缝隙并生成多向改进建议 (p08)，可选 pairwise 排序 (p10)
    Inspire {
        /// 场景文件路径
        #[arg(short, long)]
        scene: String,

        /// motif.yaml 配置文件路径
        #[arg(short = 'M', long)]
        motif_profile: String,

        /// 建议方向（逗号分隔，默认全部6个方向）
        #[arg(short, long, value_delimiter = ',')]
        directions: Option<Vec<String>>,

        /// 启用 pairwise blind 对比排序
        #[arg(long)]
        compare: bool,

        /// 输出文件路径
        #[arg(short, long)]
        output: Option<String>,
    },
}

fn main() {
    let cli = Cli::parse();

    let result = match cli.command {
        Commands::Extract {
            scene,
            motif_profile,
            output,
        } => narrative_cli::commands::extract::run(
            &scene,
            motif_profile.as_deref(),
            output.as_deref(),
        ),
        Commands::Review {
            scene,
            style,
            motif_profile,
            output,
        } => narrative_cli::commands::review::run(
            &scene,
            &style,
            motif_profile.as_deref(),
            output.as_deref(),
        ),
        Commands::Inspire {
            scene,
            motif_profile,
            directions,
            compare,
            output,
        } => narrative_cli::commands::inspire::run(
            &scene,
            &motif_profile,
            output.as_deref(),
            &directions.unwrap_or_default(),
            compare,
        ),
    };

    if let Err(e) = result {
        eprintln!("错误: {}", e);
        std::process::exit(1);
    }
}
