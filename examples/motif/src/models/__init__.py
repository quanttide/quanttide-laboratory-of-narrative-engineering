"""models — 领域模型实体，拆分自 domain.py"""

from src.models.types import Series, ArticleType, SceneType, Direction, GapType, Confidence, PairType
from src.models.motif import Motif, SubMotif, Variant
from src.models.article import Article, SceneTemplate, ArticleAnalysis
from src.models.analysis import GapItem, GapAttribution, GapReport, Suggestion, SuggestionDirection, DIRECTIONS, DIRECTION_MAP
from src.models.style import StyleDimension, StyleMotifLink, StyleReview, FixGroup
from src.models.eval import MatchItem, CoverageReport, EvaluationScore, MotifSimilarityPair
from src.models.gallery import MotifProfile, Gallery
