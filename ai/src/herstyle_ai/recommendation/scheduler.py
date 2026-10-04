from copy import deepcopy
from uuid import uuid4


class WeeklyOutfitScheduler:

    def __init__(
        self,
        recommendation_engine,
        cooldown_days=7,
        repetition_penalty=0.30,
        low_score_threshold=0.30,
    ):

        self.engine = (
            recommendation_engine
        )

        self.cooldown_days = int(
            cooldown_days
        )

        self.repetition_penalty = float(
            repetition_penalty
        )

        self.low_score_threshold = float(
            low_score_threshold
        )

    @staticmethod
    def _request_applies_to_day(
        request_constraints,
        day_index,
    ):
        if request_constraints is None:
            return False

        target_day_offset = (
            request_constraints.target_day_offset
        )

        if target_day_offset is None:
            return True

        return (
            int(target_day_offset)
            == int(day_index) - 1
        )

    @staticmethod
    def _group_for_structure(groups, structure):
        """Return the best available group for a requested structure.

        Weather contexts may request shoes or an outer layer even when the
        user's wardrobe does not contain either slot.  Returning an empty
        week in that case is a poor product experience: a valid base outfit
        can still be built from the owned items.  Keep the requested
        structure as the day's context, but gracefully reduce optional
        layers in the candidate lookup.
        """

        fallbacks = {
            "top+bottom+outerwear+shoes": (
                "top+bottom+outerwear",
                "top+bottom",
            ),
            "top+bottom+shoes": (
                "top+bottom",
            ),
            "dress+outerwear+shoes": (
                "dress+outerwear",
            ),
            "dress+shoes": (),
        }

        for candidate_structure in (
            structure,
            *fallbacks.get(structure, ()),
        ):
            group = groups.get(candidate_structure)
            if group and group.get("recommendations"):
                return candidate_structure, group

        return structure, None
    # =====================================================
    # ITEM IDS
    # =====================================================

    @staticmethod
    def _get_item_ids(
        recommendation,
    ):

        return {

            item[
                "item_id"
            ]

            for item in recommendation[
                "items"
            ].values()
        }

    # =====================================================
    # OUTFIT SIGNATURE
    # =====================================================

    @staticmethod
    def _outfit_signature(
        recommendation,
    ):

        pairs = []

        for slot, item in sorted(
            recommendation[
                "items"
            ].items()
        ):

            pairs.append(
                (
                    slot,
                    item[
                        "item_id"
                    ],
                )
            )

        return tuple(
            pairs
        )

    # =====================================================
    # RECENT ITEMS
    # =====================================================

    def _recent_item_ids(
        self,
        scheduled,
    ):

        recent = scheduled[
            -self.cooldown_days:
        ]

        result = set()

        for day in recent:

            recommendation = (
                day.get(
                    "outfit"
                )
            )

            if recommendation is None:
                continue

            result.update(
                self._get_item_ids(
                    recommendation
                )
            )

        return result

    @staticmethod
    def _scheduled_item_ids(scheduled):
        result = set()
        for day in scheduled:
            recommendation = day.get("outfit")
            if recommendation is not None:
                result.update(WeeklyOutfitScheduler._get_item_ids(recommendation))
        return result

    # =====================================================
    # CHOOSE ONE OUTFIT
    # =====================================================

    def _score_scheduler_candidates(
        self,
        candidates,
        scheduled,
        used_outfits,
    ):

        if not candidates:
            return []

        recent_items = (
            self._recent_item_ids(
                scheduled
            )
        )
        scheduled_items = self._scheduled_item_ids(scheduled)

        scored = []

        for candidate in candidates:

            candidate = deepcopy(
                candidate
            )

            item_ids = (
                self._get_item_ids(
                    candidate
                )
            )

            repeated_recent = (
                item_ids
                &
                recent_items
            )

            repeated_week = (
                item_ids
                &
                scheduled_items
            )

            repeat_count = len(
                repeated_recent
            )

            cooldown_item_count = sum(
                1
                for item in candidate["items"].values()
                if item.get("styling_cooldown_active")
            )

            signature = (
                self._outfit_signature(
                    candidate
                )
            )

            exact_outfit_used = (
                signature
                in
                used_outfits
            )

            # =============================================
            # ACTIVE RANKING SCORE
            #
            # May be:
            #
            # - fusion_score
            # - compatibility_score fallback
            #
            # depending on recommendation group size.
            # =============================================

            ranking_score = float(
                candidate[
                    "score"
                ]
            )

            compatibility_score = float(
                candidate.get(
                    "compatibility_score",
                    ranking_score,
                )
            )

            style_score = (
                candidate.get(
                    "style_score"
                )
            )

            if style_score is not None:

                style_score = float(
                    style_score
                )

            adjusted_score = (
                ranking_score
                -
                (
                    self.repetition_penalty
                    *
                    len(repeated_week)
                )
                - (self.repetition_penalty * 0.50 * repeat_count)
            )

            # Strongly discourage repeating
            # the exact same outfit.
            if exact_outfit_used:

                adjusted_score -= 1.0

            candidate[
                "scheduler"
            ] = {

                # Backward-compatible field.
                "raw_score":
                    ranking_score,

                # Explicit score semantics.
                "ranking_score":
                    ranking_score,

                "compatibility_score":
                    compatibility_score,

                "style_score":
                    style_score,

                "base_score":
                    candidate.get(
                        "base_score"
                    ),

                "preference_score":
                    candidate.get(
                        "preference_score"
                    ),

                "preference_rank_score":
                    candidate.get(
                        "preference_rank_score"
                    ),

                "personalization_confidence":
                    candidate.get(
                        "personalization_confidence"
                    ),

                "personalization_weight":
                    candidate.get(
                        "personalization_weight"
                    ),

                "personalized_score":
                    candidate.get(
                        "personalized_score"
                    ),

                "ranking_method":
                    candidate.get(
                        "ranking_method",
                        "compatibility",
                    ),

                "adjusted_score":
                    float(
                        adjusted_score
                    ),

                "recent_repeat_count":
                    int(
                        repeat_count
                    ),

                "weekly_repeat_count":
                    int(
                        len(repeated_week)
                    ),

                "repeated_item_ids":
                    sorted(
                        repeated_recent
                    ),

                "repeated_week_item_ids":
                    sorted(
                        repeated_week
                    ),

                "exact_outfit_used_before":
                    bool(
                        exact_outfit_used
                    ),

                "styling_cooldown_item_count":
                    int(cooldown_item_count),
            }

            scored.append(
                candidate
            )

        scored.sort(
            key=lambda x: (
                x["scheduler"]["styling_cooldown_item_count"] == 0,
                x["scheduler"]["adjusted_score"],
            ),
            reverse=True,
        )

        return scored

    def _choose_outfit(
        self,
        candidates,
        scheduled,
        used_outfits,
    ):

        scored = self._score_scheduler_candidates(
            candidates=candidates,
            scheduled=scheduled,
            used_outfits=used_outfits,
        )

        return scored[0] if scored else None

    @staticmethod
    def _selection_candidates(candidates):
        """Build a diverse selection pool before score/bandit selection."""

        def is_clean(candidate):
            scheduler = candidate.get("scheduler") or {}
            return (
                scheduler.get("styling_cooldown_item_count", 0) == 0
                and scheduler.get("weekly_repeat_count", 0) == 0
                and not scheduler.get("exact_outfit_used_before", False)
            )

        def no_weekly_repeat(candidate):
            scheduler = candidate.get("scheduler") or {}
            return (
                scheduler.get("weekly_repeat_count", 0) == 0
                and not scheduler.get("exact_outfit_used_before", False)
            )

        def no_cooldown(candidate):
            scheduler = candidate.get("scheduler") or {}
            return scheduler.get("styling_cooldown_item_count", 0) == 0

        # Prefer unused items and unique combinations, but fall back when the
        # wardrobe does not contain enough alternatives for all seven days.
        for predicate in (is_clean, no_weekly_repeat, no_cooldown):
            selected = [candidate for candidate in candidates if predicate(candidate)]
            if selected:
                return selected

        return list(candidates)

    @staticmethod
    def _rotate_selection(candidates, variation, day_index):
        """Pick a different high-quality candidate when regenerating."""

        if not candidates or not variation or len(candidates) == 1:
            return candidates[0] if candidates else None

        # Stay within the best five candidates so variation does not trade
        # away recommendation quality for a random low-scoring outfit.
        pool_size = min(len(candidates), 5)
        offset = (int(variation) + int(day_index) - 1) % pool_size
        return candidates[offset]

    # =====================================================
    # CREATE WEEKLY PLAN
    # =====================================================

    def create_schedule(
        self,
        wardrobe_items,
        structure_plan,
        personalized_reranker=None,
        preference_scorer=None,
        request_constraints=None,
        constraint_matcher=None,
        request_reranker=None,
        contexts=None,
        learned_personalization=None,
        user_id="default",
        bandit_decision_logger=None,
        bandit_runtime=None,
        variation=0,
    ):

        use_learned_personalization = (
            learned_personalization
            is not None
        )

        # Get ALL ranked candidates,
        # not just top 5.
        recommendation_result = (
            self.engine.recommend_by_structure(
                wardrobe_items=wardrobe_items,
                top_k_per_structure=10000,
                personalized_reranker=(
                    None
                    if use_learned_personalization
                    else personalized_reranker
                ),
                preference_scorer=(
                    None
                    if use_learned_personalization
                    else preference_scorer
                ),
            )
        )

        groups = (
            recommendation_result[
                "groups"
            ]
        )

        scheduled = []

        used_outfits = set()

        for day_index, structure in enumerate(
            structure_plan,
            start=1,
        ):

            day_context = {}

            if (
                isinstance(
                    contexts,
                    (list, tuple),
                )
                and day_index - 1 < len(
                    contexts
                )
            ):

                day_context = contexts[
                    day_index - 1
                ]

            selected_structure, group = (
                self._group_for_structure(
                    groups,
                    structure,
                )
            )

            if group is None:

                request_applied = (
                    self._request_applies_to_day(
                        request_constraints,
                        day_index,
                    )
                )

                scheduled.append(
                    {
                        "day":
                            day_index,

                        "structure":
                            structure,

                        "available_structure":
                            selected_structure
                            if selected_structure != structure
                            else None,

                        "status":
                            (
                                "no_request_match"
                                if request_applied
                                else "unavailable"
                            ),

                        "outfit":
                            None,

                        "request_applied":
                            request_applied,
                    }
                )

                continue

            candidates = (
                group[
                    "recommendations"
                ]
            )

            # =============================================
            # NATURAL-LANGUAGE REQUEST
            # =============================================

            request_applied = (
                self._request_applies_to_day(
                    request_constraints,
                    day_index,
                )
            )

            if (
                request_applied
                and request_constraints is not None
                and constraint_matcher is not None
                and request_reranker is not None
            ):
                candidates = (
                    request_reranker.rerank(
                        candidates=candidates,
                        constraints=request_constraints,
                        matcher=constraint_matcher,
                    )
                )

            # =============================================
            # P9 LEARNED PERSONALIZATION
            #
            # Runs after request constraints because an
            # explicit user request has higher priority.
            # =============================================
            if learned_personalization is not None:
                learned_candidates = (
                    learned_personalization
                    .rerank(
                        candidates=candidates,
                        context=day_context,
                        request_applied=request_applied,
                        request_constraints=(
                            request_constraints
                            if request_applied
                            else None
                        ),
                        preference_scorer=(
                            preference_scorer
                        ),
                        user_id=user_id,
                    )
                )

                if learned_candidates:

                    candidates = learned_candidates

            # =============================================
            # SCHEDULER DIVERSITY SCORING
            # =============================================
            scheduler_candidates = (
                self._score_scheduler_candidates(
                    candidates=candidates,
                    scheduled=scheduled,
                    used_outfits=used_outfits,
                )
            )

            selection_candidates = self._selection_candidates(
                scheduler_candidates
            )

            # =============================================
            # P10 BANDIT DECISION
            #
            # Exploration happens only after request
            # constraints, personalization, and scheduler
            # diversity penalties have been applied.
            # =============================================
            bandit_decision = None

            if bandit_runtime is not None and not variation:

                try:

                    bandit_decision = (
                        bandit_runtime.choose(
                            selection_candidates
                        )
                    )

                except Exception as exc:

                    bandit_decision = {
                        "selected": None,
                        "behavior_policy": {
                            "name":
                                "herstyle-ranking-scheduler",
                            "version":
                                "p10-deterministic-v1",
                            "deterministic": True,
                            "exploration_enabled": False,
                            "selected_propensity": 1.0,
                            "ips_eligible": False,
                            "reason": "bandit_runtime_error",
                            "error": str(exc),
                        },
                    }

            selected = None

            if isinstance(
                bandit_decision,
                dict,
            ):

                selected = bandit_decision.get(
                    "selected"
                )

            if variation:
                selected = self._rotate_selection(
                    selection_candidates,
                    variation=variation,
                    day_index=day_index,
                )
            elif selected is None and selection_candidates:
                selected = selection_candidates[0]

            if selected is None:

                scheduled.append(
                    {
                        "day":
                            day_index,

                        "structure":
                            structure,

                        "status":
                            (
                                "no_request_match"
                                if request_applied
                                else "unavailable"
                            ),

                        "outfit":
                            None,

                        "request_applied":
                            request_applied,
                    }
                )

                continue

            # =============================================
            # P10 BANDIT EXPOSURE LOGGING
            #
            # V1 is deterministic and observational only.
            # Logging failures must not break recommendations.
            # =============================================
            recommendation_id = selected.get(
                "recommendation_id"
            )

            if not recommendation_id:

                recommendation_id = uuid4().hex

                selected[
                    "recommendation_id"
                ] = recommendation_id

            if bandit_decision_logger is not None:

                try:

                    exposure = (
                        bandit_decision_logger.record(
                            recommendation_id=(
                                recommendation_id
                            ),
                            user_id=user_id,
                            day=day_index,
                            structure=structure,
                            context=day_context,
                            request_applied=request_applied,
                            candidates=selection_candidates,
                            selected=selected,
                            behavior_policy=(
                                (
                                    bandit_decision.get(
                                        "behavior_policy"
                                    )
                                    if isinstance(
                                        bandit_decision,
                                        dict,
                                    )
                                    else None
                                )
                            ),
                        )
                    )

                    selected[
                        "bandit_decision_id"
                    ] = exposure.get(
                        "decision_id"
                    )

                    selected[
                        "bandit_policy"
                    ] = exposure.get(
                        "behavior_policy"
                    )

                except Exception as exc:

                    selected[
                        "bandit_logging_error"
                    ] = str(
                        exc
                    )

            # =============================================
            # QUALITY
            #
            # Prefer the CompatibilityScorer's own
            # threshold decision when available.
            #
            # This avoids maintaining two conflicting
            # compatibility thresholds.
            # =============================================

            threshold_flag = (
                selected.get(
                    "threshold_flag"
                )
            )

            compatibility_quality_score = float(
                selected[
                    "scheduler"
                ][
                    "compatibility_score"
                ]
            )

            if threshold_flag is False:

                quality = (
                    "low_confidence"
                )

            elif (
                threshold_flag is None
                and
                compatibility_quality_score
                <
                self.low_score_threshold
            ):

                quality = "low_confidence"

            elif (
                selected[
                    "scheduler"
                ][
                    "recent_repeat_count"
                ]
                > 0
            ):

                quality = "acceptable"

            else:

                quality = "good"
            signature = (
                self._outfit_signature(
                    selected
                )
            )

            used_outfits.add(
                signature
            )

            scheduled.append(
                {
                    "day":
                        day_index,

                    "structure":
                        structure,

                    "available_structure":
                        selected_structure
                        if selected_structure != structure
                        else None,

                    "status":
                        "scheduled",

                    "quality":
                        quality,

                    "outfit":
                        selected,

                    "request_applied":
                        request_applied,
                }
            )

        return {

            "days":
                len(
                    structure_plan
                ),

            "cooldown_days":
                self.cooldown_days,

            "repetition_penalty":
                self.repetition_penalty,

            "schedule":
                scheduled,
        }
