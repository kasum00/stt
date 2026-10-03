from collections import defaultdict

from herstyle_ai.recommendation.candidate_generator import (
    OutfitCandidateGenerator,
)


class OutfitRecommendationEngine:

    def __init__(
        self,
        scorer,
        max_candidates=5000,
        styling_scorer=None,
        reranker=None,
    ):

        # =================================================
        # COMPATIBILITY SCORER
        #
        # Current RePolyvore / compatibility model.
        # =================================================

        self.scorer = scorer

        # =================================================
        # STYLING SCORER
        #
        # Optional for backward compatibility.
        #
        # When a reranker is configured, style_score is
        # used as one of the structure-local ranking signals.
        # =================================================

        self.styling_scorer = (
            styling_scorer
        )

        # =================================================
        # RERANKER
        #
        # Optional for backward compatibility.
        #
        # When enabled:
        # compatibility_score
        # +
        # style_score
        # ↓
        # rank-percentile fusion
        # ↓
        # score
        #
        # Small candidate groups automatically fall back
        # to compatibility-only ranking.
        # =================================================

        self.reranker = (
            reranker
        )

        # =================================================
        # CANDIDATE GENERATOR
        # =================================================

        self.generator = (
            OutfitCandidateGenerator(
                max_candidates=max_candidates
            )
        )

        # =================================================
        # FEATURE CACHE
        #
        # One wardrobe image should only be encoded once.
        # =================================================

        self.feature_cache = {}

    # =====================================================
    # FEATURE CACHE
    # =====================================================

    def _get_feature(
        self,
        item,
    ):

        item_id = str(
            item[
                "item_id"
            ]
        )

        if item_id in self.feature_cache:

            return self.feature_cache[
                item_id
            ]

        image_path = item[
            "image_path"
        ]

        feature = (
            self.scorer.extract_feature(
                image_path
            )
        )

        self.feature_cache[
            item_id
        ] = feature

        return feature

    # =====================================================
    # SCORE ONE CANDIDATE
    # =====================================================

    def score_candidate(
        self,
        candidate,
    ):

        # =================================================
        # BUILD COMPATIBILITY FEATURES
        # =================================================

        slot_features = {}

        for slot, item in (
            candidate[
                "items"
            ].items()
        ):

            slot_features[
                slot
            ] = self._get_feature(
                item
            )

        # =================================================
        # REPOLYVORE / COMPATIBILITY SCORE
        # =================================================

        score_result = (
            self.scorer.score_features(
                slot_features
            )
        )

        # =================================================
        # STYLING SCORE
        #
        # StylingScorer receives the RAW candidate because
        # it needs:
        #
        # - color_profile
        # - pattern_profile
        # - slot information
        # - subcategory
        # =================================================

        styling_result = None

        if self.styling_scorer is not None:

            styling_result = (
                self.styling_scorer
                .score_candidate(
                    candidate
                )
            )

        # =================================================
        # PUBLIC RESULT
        # =================================================

        result = {

            "structure":
                candidate[
                    "structure"
                ],

            "structure_analysis":
                candidate.get(
                    "structure_analysis",
                    {},
                ),

            # =============================================
            # RAW RANKING SCORE
            #
            # score starts as compatibility_score here.
            # _score_and_sort() replaces it with fusion_score
            # when a reranker is enabled.
            # =============================================

            "score":
                score_result[
                    "score"
                ],

            "compatibility_score":
                score_result[
                    "score"
                ],

            # =============================================
            # DIAGNOSTIC FLAG
            #
            # Not a probability.
            # =============================================

            "threshold_flag":
                score_result[
                    "compatible"
                ],

            # =============================================
            # ITEMS
            #
            # Keep styling metadata because later phases
            # need it for:
            #
            # - explanation
            # - personalization
            # - feedback learning
            # - debugging
            # =============================================

            "items": {

                slot: {

                    "item_id":
                        item[
                            "item_id"
                        ],

                    "image_path":
                        item[
                            "image_path"
                        ],

                    "category":
                        item.get(
                            "category"
                        ),

                    "subcategory":
                        item.get(
                            "subcategory"
                        ),

                    "color":
                        item.get(
                            "color"
                        ),

                    "pattern":
                        item.get(
                            "pattern"
                        ),

                    "color_profile":
                        item.get(
                            "color_profile"
                        ),

                    "pattern_profile":
                        item.get(
                            "pattern_profile"
                        ),
                }

                for slot, item
                in candidate[
                    "items"
                ].items()
            },
        }

        # =================================================
        # STYLING DIAGNOSTICS
        # =================================================

        if styling_result is not None:

            result[
                "style_score"
            ] = (
                styling_result.score
            )

            result[
                "styling"
            ] = {

                "color_score":
                    styling_result.color_score,

                "pattern_score":
                    styling_result.pattern_score,

                "reasons":
                    styling_result.reasons,

                "components":
                    styling_result.components,
            }

        else:

            result[
                "style_score"
            ] = None

            result[
                "styling"
            ] = None

        return result

    # =====================================================
    # SCORE AND SORT
    # =====================================================

    def _score_and_sort(
        self,
        candidates,
    ):

        scored = [

            self.score_candidate(
                candidate
            )

            for candidate in candidates
        ]

        # =================================================
        # RERANK
        #
        # Reranking happens inside one structure only.
        # The caller passes candidates from one structure,
        # so rank-percentile normalization never mixes
        # different structure types.
        # =================================================

        if self.reranker is not None:

            return self.reranker.rerank(
                scored
            )

        # =================================================
        # BACKWARD-COMPATIBLE RANKING
        # =================================================

        scored.sort(
            key=lambda x:
                x[
                    "score"
                ],
            reverse=True,
        )

        return scored

    # =====================================================
    # RECOMMEND ONE STRUCTURE
    # =====================================================

    def recommend(
        self,
        wardrobe_items,
        structure,
        top_k=10,
        personalized_reranker=None,
        preference_scorer=None,
    ):

        """
        Recommend outfits inside ONE structure.

        Example:

            structure="top+bottom+shoes"

        Raw compatibility scores are not assumed to be
        directly comparable across different structures.

        In P1.8H:
            score = fusion_score when reranking is enabled
            and the structure has enough candidates.

        Small structures keep compatibility_score as
        their ranking score.
        """

        # =================================================
        # GENERATE ALL CANDIDATES
        # =================================================

        candidates = (
            self.generator.generate(
                wardrobe_items
            )
        )

        # =================================================
        # FILTER STRUCTURE
        # =================================================

        candidates = [

            candidate

            for candidate in candidates

            if candidate[
                "structure"
            ]
            == structure
        ]

        # =================================================
        # NO CANDIDATES
        # =================================================

        if not candidates:

            return {

                "structure":
                    structure,

                "candidate_count":
                    0,

                "recommendations":
                    [],
            }

        # =================================================
        # SCORE
        # =================================================

        scored = (
            self._score_and_sort(
                candidates
            )
        )

        # =================================================
        # PERSONALIZED RERANK
        #
        # Applied after Compatibility + Styling fusion and
        # before top_k truncation, within this structure only.
        # =================================================

        if (
            personalized_reranker is not None
            and preference_scorer is not None
        ):

            scored = (
                personalized_reranker
                .rerank(
                    scored,
                    preference_scorer,
                )
            )

        # =================================================
        # RESULT
        # =================================================

        return {

            "structure":
                structure,

            "candidate_count":
                len(
                    candidates
                ),

            "recommendations":
                scored[
                    :top_k
                ],
        }

    # =====================================================
    # RECOMMEND GROUPED BY STRUCTURE
    # =====================================================

    def recommend_by_structure(
        self,
        wardrobe_items,
        top_k_per_structure=5,
        personalized_reranker=None,
        preference_scorer=None,
    ):

        # =================================================
        # GENERATE
        # =================================================

        candidates = (
            self.generator.generate(
                wardrobe_items
            )
        )

        # =================================================
        # GROUP BY STRUCTURE
        # =================================================

        grouped_candidates = (
            defaultdict(
                list
            )
        )

        for candidate in candidates:

            grouped_candidates[
                candidate[
                    "structure"
                ]
            ].append(
                candidate
            )

        groups = {}

        # =================================================
        # SCORE EACH STRUCTURE SEPARATELY
        #
        # Important because raw compatibility scores from
        # different structures are not assumed comparable.
        # =================================================

        for structure, group in (
            grouped_candidates.items()
        ):

            scored = (
                self._score_and_sort(
                    group
                )
            )

            # =================================================
            # PERSONALIZED RERANK
            #
            # Keep personalization structure-local.  Scores
            # from different structures are never mixed.
            # =================================================

            if (
                personalized_reranker is not None
                and preference_scorer is not None
            ):

                scored = (
                    personalized_reranker
                    .rerank(
                        scored,
                        preference_scorer,
                    )
                )

            groups[
                structure
            ] = {

                "candidate_count":
                    len(
                        group
                    ),

                "recommendations":
                    scored[
                        :top_k_per_structure
                    ],
            }

        # =================================================
        # RESULT
        # =================================================

        return {

            "total_candidate_count":
                len(
                    candidates
                ),

            "structure_count":
                len(
                    groups
                ),

            "groups":
                groups,
        }

    # =====================================================
    # CLEAR FEATURE CACHE
    # =====================================================

    def clear_cache(
        self,
    ):

        self.feature_cache.clear()
