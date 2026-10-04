from pathlib import Path

from uuid import uuid4


from herstyle_ai.weather.provider import (
    WeatherProvider,
)

from herstyle_ai.wardrobe.repository import (
    WardrobeRepository,
)

from herstyle_ai.compatibility.scorer import (
    CompatibilityScorer,
)

from herstyle_ai.recommendation.engine import (
    OutfitRecommendationEngine,
)

from herstyle_ai.recommendation.reranker import (
    OutfitReranker,
)

from herstyle_ai.recommendation.scheduler import (
    WeeklyOutfitScheduler,
)

from herstyle_ai.recommendation.context_selector import (
    ContextStructureSelector,
)

from herstyle_ai.styling import (
    ColorStylingConfig,
    ColorHarmonyScorer,
    PatternStylingConfig,
    PatternHarmonyScorer,
    PatternOutfitScorer,
    StylingScorer,
)

from herstyle_ai.personalization import (
    FeedbackRepository,
    PreferenceRepository,
    UserPreferenceProfileBuilder,
    UserPreferenceScorer,
    PersonalizedReranker,
)

from herstyle_ai.recommendation.styling_request_parser import (
    StylingRequestParser,
)

from herstyle_ai.recommendation.constraint_matcher import (
    StylingConstraintMatcher,
)

from herstyle_ai.recommendation.request_reranker import (
    RequestAwareReranker,
)

from herstyle_ai.personalization.recommendation_snapshot_repository import (
    RecommendationSnapshotRepository,
)

from herstyle_ai.personalization.recommendation_snapshot import (
    build_recommendation_snapshot,
)

from herstyle_ai.personalization.learned_runtime_reranker import (
    LearnedPersonalizationRuntime,
)

from herstyle_ai.personalization.bandit_decision_logger import (
    BanditDecisionLogger,
)

from herstyle_ai.personalization.bandit_runtime import (
    SafeBanditRuntime,
)

class WeatherAwareRecommendationService:

    def __init__(
        self,
        project_root: Path,
        data_root=None,
    ):

        self.project_root = Path(
            project_root
        )

        # =====================================
        # PERSONALIZATION
        # =====================================

        self.feedback_repository = (
            FeedbackRepository(
                self.project_root,
                data_root=data_root,
            )
        )

        self.preference_repository = (
            PreferenceRepository(
                self.project_root,
                data_root=data_root,
            )
        )

        self.recommendation_snapshot_repository = (
            RecommendationSnapshotRepository(
                project_root=self.project_root,
                data_root=data_root,
            )
        )

        self.personalized_reranker = (
            PersonalizedReranker(
                max_personalization_weight=0.15,
                full_confidence_signals=20,
                min_candidates=5,
            )
        )

        self.learned_personalization_runtime = (
            LearnedPersonalizationRuntime(
                project_root=self.project_root
            )
        )

        self.bandit_decision_logger = (
            BanditDecisionLogger(
                project_root=self.project_root,
                data_root=data_root,
            )
        )

        self.bandit_runtime = SafeBanditRuntime()

        # =====================================
        # NATURAL LANGUAGE STYLING REQUEST
        # =====================================

        self.styling_request_parser = (
            StylingRequestParser()
        )

        self.constraint_matcher = (
            StylingConstraintMatcher()
        )

        self.request_reranker = (
            RequestAwareReranker(
                max_request_weight=0.15
            )
        )

        # =====================================
        # WEATHER
        # =====================================

        self.weather_provider = (
            WeatherProvider()
        )

        # =====================================
        # CONTEXT
        # =====================================

        self.context_selector = (
            ContextStructureSelector(
                cold_threshold=20,
                hot_threshold=28,
            )
        )

        # =====================================
        # WARDROBE
        # =====================================

        self.repository = (
            WardrobeRepository(
                project_root=(
                    self.project_root
                )
            )
        )

        # =====================================
        # COMPATIBILITY
        # =====================================

        self.scorer = (
            CompatibilityScorer(
                project_root=(
                    self.project_root
                )
            )
        )
        # =====================================
        # STYLING
        # =====================================

        self.color_styling_config = (
            ColorStylingConfig(
                self.project_root
            )
        )

        self.color_styling_scorer = (
            ColorHarmonyScorer(
                self.color_styling_config
            )
        )

        self.pattern_styling_config = (
            PatternStylingConfig(
                self.project_root
            )
        )

        self.pattern_harmony_scorer = (
            PatternHarmonyScorer(
                pattern_config=(
                    self.pattern_styling_config
                ),
                color_config=(
                    self.color_styling_config
                ),
            )
        )

        self.pattern_outfit_scorer = (
            PatternOutfitScorer(
                pair_scorer=(
                    self.pattern_harmony_scorer
                )
            )
        )

        self.styling_scorer = (
            StylingScorer(
                project_root=(
                    self.project_root
                ),
                color_scorer=(
                    self.color_styling_scorer
                ),
                pattern_scorer=(
                    self.pattern_outfit_scorer
                ),
            )
        )

        # =====================================
        # RERANKER
        #
        # V1 engineering defaults.
        # These are NOT learned user weights.
        # =====================================

        self.reranker = (
            OutfitReranker(
                compatibility_weight=0.70,
                styling_weight=0.30,
                min_candidates=5,
            )
        )

        self.engine = (
            OutfitRecommendationEngine(
                scorer=self.scorer,
                max_candidates=5000,
                styling_scorer=(
                    self.styling_scorer
                ),
                reranker=(
                    self.reranker
                ),
            )
        )

        # =====================================
        # SCHEDULER
        # =====================================

        self.scheduler = (
            WeeklyOutfitScheduler(
                recommendation_engine=(
                    self.engine
                ),
                cooldown_days=7,
                repetition_penalty=0.30,
                low_score_threshold=0.30,
            )
        )

    # =====================================================
    # PREFERENCE SCORER
    # =====================================================

    def _get_preference_scorer(
        self,
        user_id,
        wardrobe_items,
    ):

        user_id = str(
            user_id
        )

        events = (
            self.feedback_repository
            .list_all(
                user_id=user_id
            )
        )

        profile = (
            self.preference_repository
            .load(
                user_id
            )
        )

        # feedback_events.jsonl is append-only in V1.
        # event_count is therefore sufficient for a simple
        # stale-profile check before each recommendation.
        if (
            profile is None
            or profile.event_count
            != len(events)
        ):

            builder = (
                UserPreferenceProfileBuilder(
                    user_id=user_id,
                    item_lookup=wardrobe_items,
                )
            )

            profile = (
                builder
                .build(
                    events
                )
            )

            self.preference_repository.save(
                profile
            )

        return UserPreferenceScorer(
            profile
        )

    # =====================================================
    # GENERATE WEEKLY PLAN
    # =====================================================

    def generate(
        self,
        latitude,
        longitude,
        prefer_dress=False,
        days=7,
        user_id="default",
        styling_request=None,
        wardrobe_items=None,
        calendar_event=None,
    ):

        # =====================================
        # NATURAL-LANGUAGE REQUEST
        # =====================================

        request_constraints = None

        if (
            styling_request is not None
            and str(
                styling_request
            ).strip()
        ):
            request_constraints = (
                self.styling_request_parser
                .parse(
                    styling_request
                )
            )

        # =====================================
        # WEATHER
        # =====================================

        forecast = (
            self.weather_provider
            .get_weekly_forecast(
                latitude=latitude,
                longitude=longitude,
                days=days,
            )
        )

        # =====================================
        # BUILD STRUCTURE PLAN
        # =====================================

        contexts = []
        structure_plan = []

        for day_offset, weather_day in enumerate(
            forecast
        ):

            effective_prefer_dress = (
                prefer_dress
            )

            if request_constraints is not None:
                target_offset = (
                    request_constraints
                    .target_day_offset
                )
                request_applies = (
                    target_offset is None
                    or int(
                        target_offset
                    )
                    == int(
                        day_offset
                    )
                )

                if (
                    request_applies
                    and request_constraints
                    .prefer_dress
                    is not None
                ):
                    effective_prefer_dress = (
                        request_constraints
                        .prefer_dress
                    )

            decision_temperature = (
                weather_day.get(
                    "apparent_temperature"
                )
            )

            if decision_temperature is None:

                decision_temperature = (
                    weather_day[
                        "temperature"
                    ]
                )

            selection = (
                self.context_selector.select(
                    temperature=(
                        decision_temperature
                    ),
                    prefer_dress=(
                        effective_prefer_dress
                    ),
                    raining=(
                        weather_day.get(
                            "rain_risk",
                            False,
                        )
                    ),
                )
            )

            context = {
                **weather_day,
                **selection,
            }

            # Calendar context is additional structured input. It does not
            # rewrite parsed request constraints or alter weather selection.
            if calendar_event is not None:
                context["calendar_event"] = dict(calendar_event)

            contexts.append(
                context
            )

            structure_plan.append(
                selection[
                    "structure"
                ]
            )

        # =====================================
        # WARDROBE
        # =====================================

        # Authenticated API callers can provide an already owner-scoped
        # wardrobe snapshot. Existing research/CLI callers keep the legacy
        # repository behavior by leaving this argument as None.
        wardrobe = (
            self.repository.list_all()
            if wardrobe_items is None
            else wardrobe_items
        )

        # =====================================
        # USER PERSONALIZATION
        # =====================================

        preference_scorer = (
            self._get_preference_scorer(
                user_id=user_id,
                wardrobe_items=wardrobe,
            )
        )

        learned_personalization = None

        if (
            self.learned_personalization_runtime
            .can_use(
                user_id
            )
        ):

            learned_personalization = (
                self.learned_personalization_runtime
            )

        # =====================================
        # SCHEDULE
        # =====================================

        result = (
            self.scheduler.create_schedule(
                wardrobe_items=wardrobe,
                structure_plan=structure_plan,
                personalized_reranker=(
                    self.personalized_reranker
                ),
                preference_scorer=(
                    preference_scorer
                ),
                request_constraints=(
                    request_constraints
                ),
                constraint_matcher=(
                    self.constraint_matcher
                ),
                request_reranker=(
                    self.request_reranker
                ),
                contexts=(
                    contexts
                ),
                learned_personalization=(
                    learned_personalization
                ),
                user_id=(
                    user_id
                ),
                bandit_decision_logger=(
                    self.bandit_decision_logger
                ),
                bandit_runtime=(
                    self.bandit_runtime
                ),
            )
        )

        # =====================================
        # ATTACH CONTEXT
        # =====================================

        for schedule_day, context in zip(
            result[
                "schedule"
            ],
            contexts,
        ):

            schedule_day[
                "weather"
            ] = {

                "date":
                    context[
                        "date"
                    ],

                "temperature":
                    context[
                        "temperature"
                    ],

                "apparent_temperature":
                    context[
                        "apparent_temperature"
                    ],

                "decision_temperature":
                    context[
                        "decision_temperature"
                    ],

                "precipitation_probability":
                    context[
                        "precipitation_probability"
                    ],

                "precipitation_sum":
                    context[
                        "precipitation_sum"
                    ],

                "rain_risk":
                    context[
                        "rain_risk"
                    ],

                "weather_code":
                    context[
                        "weather_code"
                    ],
            }

            outfit = schedule_day.get(
                "outfit"
            )

            if isinstance(
                outfit,
                dict,
            ):

                recommendation_id = outfit.get(
                    "recommendation_id"
                )

                if not recommendation_id:

                    recommendation_id = uuid4().hex

                    outfit[
                        "recommendation_id"
                    ] = recommendation_id

                snapshot = build_recommendation_snapshot(
                    recommendation_id=recommendation_id,
                    user_id=user_id,
                    outfit=outfit,
                    weather=schedule_day.get(
                        "weather",
                        {},
                    ),
                    request_applied=schedule_day.get(
                        "request_applied"
                    ),
                )

                self.recommendation_snapshot_repository.add(
                    snapshot
                )

        result[
            "location"
        ] = {

            "latitude":
                float(
                    latitude
                ),

            "longitude":
                float(
                    longitude
                ),
        }

        result[
            "styling_request"
        ] = styling_request

        result[
            "request_constraints"
        ] = (
            request_constraints.to_dict()
            if request_constraints is not None
            else None
        )

        if calendar_event is not None:
            result["calendar_event"] = dict(calendar_event)

        return result
