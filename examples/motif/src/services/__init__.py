"""services — 应用服务层，按领域组织

每个模块一个独立职责：
- converter:   dict↔dataclass 互转
- gallery:     YAML 知识库加载
- extraction:  母题提取（LLM + 实体转换）
- gap:         缝隙分析、归因、建议
- alignment:   母题吻合度计算
- style_review: 风格评审、诊断、改法
- cross_work:  跨作品相似度、聚类、盲测
"""

from src.infra.acl import (
    to_motifs, to_dims, to_gap_report,
    DataclassJSONEncoder,
)
from src.services.gallery import load_motif_profile, load_gallery, build_style_prompt
from src.services.extraction import (
    extract_motifs, extract_motifs_joint,
    extract_motifs_from_text, extract_motifs_cross_validate,
)
from src.services.gap import (
    compute_gap_report, gap_attribution,
    generate_suggestions, evaluate_suggestions,
)
from src.services.alignment import compute_alignment
from src.services.style_review import (
    style_review, diagnose_style_motif_links,
    generate_combined_fix, generate_style_only_fix, evaluate_pairwise,
)
from src.services.cross_work import (
    cross_work_similarity_matrix,
    motif_chain_reconstruction,
    blind_pairing,
)
