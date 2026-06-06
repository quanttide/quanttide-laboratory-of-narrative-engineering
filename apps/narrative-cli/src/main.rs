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

        /// 目标母题配置文件（motif.yaml）
        #[arg(short, long)]
        motif_profile: Option<String>,

        /// 输出文件路径
        #[arg(short, long)]
        output: Option<String>,
    },

    /// 用 style.yaml 框架评审场景 (p09)
    Review {
        /// 场景文件路径
        #[arg(short, long)]
        scene: String,

        /// style.yaml 配置文件路径
        #[arg(short = 'S', long)]
        style: String,

        /// 输出文件路径
        #[arg(short, long)]
        output: Option<String>,
    },

    /// 分析母题缝隙并生成改进建议 (p08)
    Gap {
        /// 场景文件路径
        #[arg(short, long)]
        scene: String,

        /// motif.yaml 配置文件路径
        #[arg(short, long)]
        motif_profile: String,

        /// 建议方向（逗号分隔，默认全部6个方向）
        #[arg(short, long, value_delimiter = ',')]
        directions: Option<Vec<String>>,

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
            output,
        } => narrative_cli::commands::review::run(&scene, &style, output.as_deref()),
        Commands::Gap {
            scene,
            motif_profile,
            directions,
            output,
        } => narrative_cli::commands::gap::run(
            &scene,
            &motif_profile,
            output.as_deref(),
            &directions.unwrap_or_default(),
        ),
    };

    if let Err(e) = result {
        eprintln!("错误: {}", e);
        std::process::exit(1);
    }
}
