from dataclasses import (
    asdict,
    dataclass,
    field,
)

from typing import (
    Any,
    Dict,
    List,
    Mapping,
)


# =========================================================
# RESULT
# =========================================================

@dataclass
class OutfitExplanation:

    summary: str

    reasons: List[str] = field(
        default_factory=list
    )

    signals: Dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(
        self,
    ):

        return asdict(
            self
        )


# =========================================================
# EXPLANATION GENERATOR
# =========================================================

class OutfitExplanationGenerator:

    def __init__(
        self,
        min_personalization_confidence=0.25,
    ):

        self.min_personalization_confidence = float(
            min_personalization_confidence
        )

        if not (
            0.0
            <= self.min_personalization_confidence
            <= 1.0
        ):

            raise ValueError(
                "min_personalization_confidence "
                "must be in [0, 1]"
            )

    # =====================================================
    # HELPERS
    # =====================================================

    @staticmethod
    def _number(
        value,
    ):

        if isinstance(
            value,
            (int, float),
        ):

            return float(
                value
            )

        return None

    @staticmethod
    def _format_temperature(
        value,
    ):

        number = (
            OutfitExplanationGenerator
            ._number(
                value
            )
        )

        if number is None:

            return None

        return (
            f"{number:.1f}°C"
        )

    @staticmethod
    def _append_unique(
        reasons,
        reason,
    ):

        if (
            reason
            and reason not in reasons
        ):

            reasons.append(
                reason
            )

    # =====================================================
    # ITEM DESCRIPTION
    # =====================================================

    @staticmethod
    def _describe_item(
        item,
    ):

        if not isinstance(
            item,
            Mapping,
        ):

            return None

        subcategory = (
            item.get(
                "subcategory"
            )
            or item.get(
                "category"
            )
        )

        color = (
            item.get(
                "color"
            )
        )

        if (
            color
            and subcategory
        ):

            return (
                f"{subcategory} màu {color}"
            )

        if subcategory:

            return str(
                subcategory
            )

        return None

    # =====================================================
    # SUMMARY
    # =====================================================

    def _build_summary(
        self,
        outfit,
    ):

        items = (
            outfit.get(
                "items"
            )
            or {}
        )

        descriptions = []

        for slot in (
            "top",
            "bottom",
            "dress",
            "outerwear",
            "shoes",
        ):

            item = (
                items.get(
                    slot
                )
            )

            description = (
                self._describe_item(
                    item
                )
            )

            if description:

                descriptions.append(
                    description
                )

        if not descriptions:

            return (
                "Bộ này được chọn từ các món "
                "hiện có trong tủ đồ của bạn."
            )

        return (
            "Phối "
            + ", ".join(
                descriptions
            )
            + "."
        )

    # =====================================================
    # WEATHER
    # =====================================================

    @staticmethod
    def _weather_signals(
        weather,
    ):

        keys = (
            "date",
            "temperature",
            "apparent_temperature",
            "decision_temperature",
            "precipitation_probability",
            "precipitation_sum",
            "rain_risk",
            "weather_code",
        )

        return {

            key:
                weather.get(
                    key
                )

            for key in keys

            if key in weather
        }

    def _add_weather_reason(
        self,
        weather,
        reasons,
    ):

        temperature = (
            weather.get(
                "decision_temperature"
            )
        )

        if temperature is None:

            temperature = (
                weather.get(
                    "apparent_temperature"
                )
            )

        if temperature is None:

            temperature = (
                weather.get(
                    "temperature"
                )
            )

        formatted = (
            self._format_temperature(
                temperature
            )
        )

        if formatted is not None:

            self._append_unique(
                reasons,
                (
                    "Cấu trúc outfit được chọn "
                    "có xét đến nhiệt độ khoảng "
                    f"{formatted}."
                ),
            )

        if weather.get(
            "rain_risk"
        ):

            self._append_unique(
                reasons,
                (
                    "Lịch phối đồ có xét đến "
                    "nguy cơ mưa trong ngày."
                ),
            )

    # =====================================================
    # STYLING REASON TRANSLATION
    # =====================================================

    def _translate_styling_reason(
        self,
        reason,
    ):

        reason = str(
            reason
        )

        # -------------------------------------------------
        # COLOR — OFFICE PALETTE
        # -------------------------------------------------

        prefix = (
            "color:office_palette:"
        )

        if reason.startswith(
            prefix
        ):

            palette = (
                reason[
                    len(
                        prefix
                    ):
                ]
                .replace(
                    "+",
                    ", ",
                )
            )

            return (
                f"Bảng màu {palette} "
                "phù hợp với phối đồ công sở."
            )

        # -------------------------------------------------
        # COLOR — HARMONY GROUP
        # -------------------------------------------------

        prefix = (
            "color:harmony_group:"
        )

        if reason.startswith(
            prefix
        ):

            group = (
                reason[
                    len(
                        prefix
                    ):
                ]
                .replace(
                    "_",
                    " ",
                )
            )

            return (
                "Các màu nằm trong cùng "
                f"nhóm hòa sắc {group}."
            )

        # -------------------------------------------------
        # COLOR — REPEATED
        # -------------------------------------------------

        prefix = (
            "color:repeated_color:"
        )

        if reason.startswith(
            prefix
        ):

            color = (
                reason[
                    len(
                        prefix
                    ):
                ]
            )

            return (
                f"Màu {color} được lặp lại "
                "giữa các món, giúp outfit "
                "liên kết hơn."
            )

        # -------------------------------------------------
        # COLOR — NEUTRAL
        # -------------------------------------------------

        prefix = (
            "color:neutral_color:"
        )

        if reason.startswith(
            prefix
        ):

            color = (
                reason[
                    len(
                        prefix
                    ):
                ]
            )

            return (
                f"Màu {color} đóng vai trò "
                "màu trung tính, giúp tổng thể "
                "dễ cân bằng."
            )

        # -------------------------------------------------
        # PATTERN
        # -------------------------------------------------

        if reason == (
            "pattern:layering:"
            "pattern_inner_solid_outer"
        ):

            return (
                "Lớp trong có họa tiết được cân bằng "
                "bằng lớp ngoài trơn."
            )

        if reason == (
            "pattern:layering:"
            "solid_inner_pattern_outer"
        ):

            return (
                "Lớp trong trơn kết hợp với lớp ngoài "
                "có họa tiết."
            )

        if reason.endswith(
            ":both_items_solid"
        ):

            parts = reason.split(
                ":"
            )

            if len(
                parts
            ) >= 3:

                slot_pair = parts[
                    -2
                ]

                slot_names = {
                    "top": "áo",
                    "bottom": "phần dưới",
                    "dress": "váy liền",
                    "outerwear": "lớp ngoài",
                }

                slots = slot_pair.split(
                    "+"
                )

                if len(
                    slots
                ) == 2:

                    left = slot_names.get(
                        slots[0],
                        slots[0],
                    )

                    right = slot_names.get(
                        slots[1],
                        slots[1],
                    )

                    return (
                        f"{left.capitalize()} và "
                        f"{right} đều trơn, "
                        "giúp tổng thể gọn và dễ phối."
                    )

        if (
            "all_garments_solid"
            in reason
        ):

            return (
                "Toàn bộ trang phục dùng "
                "họa tiết trơn nên tổng thể "
                "giữ được sự tối giản."
            )

        if (
            "single_patterned_garment"
            in reason
        ):

            return (
                "Outfit chỉ có một món "
                "mang họa tiết, giúp hạn chế "
                "xung đột thị giác."
            )

        if (
            "solid_top_pattern_bottom"
            in reason
        ):

            return (
                "Phần dưới có họa tiết được "
                "cân bằng bằng áo trơn."
            )

        if (
            "pattern_top_solid_bottom"
            in reason
        ):

            return (
                "Áo họa tiết được cân bằng "
                "bằng phần dưới trơn."
            )

        if (
            "neutral_solid_companion"
            in reason
        ):

            return (
                "Món trơn màu trung tính giúp "
                "cân bằng món có họa tiết."
            )

        if (
            "pattern_with_solid"
            in reason
        ):

            return (
                "Món có họa tiết được phối "
                "cùng món trơn để giữ tổng thể "
                "dễ nhìn."
            )

        if (
            "multiple_patterns"
            in reason
        ):

            return (
                "Outfit có nhiều họa tiết nên "
                "điểm phối đồ được đánh giá "
                "thận trọng hơn."
            )

        if (
            "pattern_conflict"
            in reason
        ):

            return (
                "Các họa tiết có dấu hiệu "
                "xung đột với nhau."
            )

        # Unknown internal reason:
        # do NOT expose raw backend code to user.
        return None

    def _add_styling_reasons(
        self,
        outfit,
        reasons,
    ):

        styling = (
            outfit.get(
                "styling"
            )
        )

        if not isinstance(
            styling,
            Mapping,
        ):

            return

        styling_reasons = (
            styling.get(
                "reasons",
                [],
            )
        )

        if isinstance(
            styling_reasons,
            str,
        ):

            styling_reasons = [
                styling_reasons
            ]

        if not isinstance(
            styling_reasons,
            (list, tuple),
        ):

            return

        for raw_reason in (
            styling_reasons
        ):

            if raw_reason is None:

                continue

            translated = (
                self._translate_styling_reason(
                    raw_reason
                )
            )

            if translated:

                self._append_unique(
                    reasons,
                    translated,
                )

    # =====================================================
    # STRUCTURE AND LAYERING
    # =====================================================

    def _add_structure_reason(
        self,
        outfit,
        reasons,
    ):

        structure_analysis = outfit.get(
            "structure_analysis",
            {},
        )

        if not isinstance(
            structure_analysis,
            Mapping,
        ):

            structure_analysis = {}

        base_structure = structure_analysis.get(
            "base_structure"
        )

        structure_text = {
            "top+trousers":
                "Cấu trúc cơ bản gồm áo và quần.",
            "top+skirt":
                "Cấu trúc cơ bản gồm áo và chân váy.",
            "top+trousers+blazer":
                "Cấu trúc gồm áo, quần và blazer.",
            "top+skirt+cardigan":
                "Cấu trúc gồm áo, chân váy và cardigan.",
            "dress+blazer/cardigan":
                "Cấu trúc gồm váy và một lớp ngoài blazer hoặc cardigan.",
        }

        if base_structure in structure_text:

            self._append_unique(
                reasons,
                structure_text[
                    base_structure
                ],
            )

        relation_tags = structure_analysis.get(
            "relation_tags",
            [],
        )

        if not isinstance(
            relation_tags,
            (list, tuple, set),
        ):

            relation_tags = []

        if "pattern_inner_solid_outer" in relation_tags:

            self._append_unique(
                reasons,
                (
                    "Lớp trong có họa tiết được cân bằng "
                    "bằng lớp ngoài trơn."
                ),
            )

        if "solid_inner_pattern_outer" in relation_tags:

            self._append_unique(
                reasons,
                (
                    "Lớp trong trơn kết hợp với lớp ngoài "
                    "có họa tiết."
                ),
            )

    @staticmethod
    def _structure_signals(
        outfit,
    ):

        structure_analysis = outfit.get(
            "structure_analysis",
            {},
        )

        if not isinstance(
            structure_analysis,
            Mapping,
        ):

            structure_analysis = {}

        return {
            "base_card_id": structure_analysis.get(
                "base_card_id"
            ),
            "base_structure": structure_analysis.get(
                "base_structure"
            ),
            "layer_count": structure_analysis.get(
                "layer_count"
            ),
            "is_layered": structure_analysis.get(
                "is_layered"
            ),
            "relation_card_ids": structure_analysis.get(
                "relation_card_ids",
                [],
            ),
            "relation_tags": structure_analysis.get(
                "relation_tags",
                [],
            ),
        }

    # =====================================================
    # COMPATIBILITY
    # =====================================================

    def _add_compatibility_reason(
        self,
        outfit,
        reasons,
    ):

        threshold_flag = (
            outfit.get(
                "threshold_flag"
            )
        )

        if threshold_flag is True:

            self._append_unique(
                reasons,
                (
                    "Mức tương thích của các món "
                    "đạt ngưỡng lựa chọn của "
                    "mô hình."
                ),
            )

        elif threshold_flag is False:

            self._append_unique(
                reasons,
                (
                    "Mức tương thích của các món "
                    "chưa đạt ngưỡng lựa chọn "
                    "thông thường của mô hình."
                ),
            )

    # =====================================================
    # PERSONALIZATION
    # =====================================================

    def _add_preference_reason(
        self,
        outfit,
        scheduler,
        reasons,
    ):

        confidence = (
            outfit.get(
                "personalization_confidence"
            )
        )

        if confidence is None:

            confidence = (
                scheduler.get(
                    "personalization_confidence"
                )
            )

        confidence = (
            self._number(
                confidence
            )
        )

        preference_score = (
            outfit.get(
                "preference_score"
            )
        )

        if preference_score is None:

            preference_score = (
                scheduler.get(
                    "preference_score"
                )
            )

        preference_score = (
            self._number(
                preference_score
            )
        )

        if (
            confidence is None
            or preference_score is None
        ):

            return

        if (
            confidence
            <
            self.min_personalization_confidence
        ):

            if preference_score >= 0.50:

                self._append_unique(
                    reasons,
                    (
                        "Bộ này có một số đặc điểm "
                        "gần với các lựa chọn gần đây "
                        "của bạn; dữ liệu cá nhân hiện "
                        "còn ít nên tín hiệu này chỉ "
                        "được dùng với trọng số nhỏ."
                    ),
                )

            return

        if preference_score >= 0.75:

            self._append_unique(
                reasons,
                (
                    "Bộ này khá gần với các "
                    "đặc điểm bạn thường lựa chọn."
                ),
            )

        elif preference_score >= 0.50:

            self._append_unique(
                reasons,
                (
                    "Bộ này có một số đặc điểm "
                    "phù hợp với sở thích đã "
                    "ghi nhận."
                ),
            )

    # =====================================================
    # SCHEDULER
    # =====================================================

    def _add_scheduler_reason(
        self,
        scheduler,
        reasons,
    ):

        repeat_count = (
            scheduler.get(
                "recent_repeat_count",
                0,
            )
        )

        try:

            repeat_count = int(
                repeat_count
            )

        except (
            TypeError,
            ValueError,
        ):

            repeat_count = 0

        if repeat_count > 0:

            self._append_unique(
                reasons,
                (
                    "Lịch tuần đã giảm nhẹ điểm "
                    "để hạn chế lặp lại các món "
                    "đã dùng gần đây."
                ),
            )

    # =====================================================
    # GENERATE
    # =====================================================

    def generate(
        self,
        outfit,
        weather=None,
    ) -> OutfitExplanation:

        if outfit is None:

            return OutfitExplanation(
                summary=(
                    "Không có outfit để giải thích."
                ),
                reasons=[],
                signals={
                    "weather":
                        dict(
                            weather
                            or {}
                        ),
                },
            )

        if not isinstance(
            outfit,
            Mapping,
        ):

            raise TypeError(
                "outfit must be a mapping"
            )

        if weather is None:

            weather = {}

        if not isinstance(
            weather,
            Mapping,
        ):

            raise TypeError(
                "weather must be a mapping"
            )

        scheduler = (
            outfit.get(
                "scheduler",
                {},
            )
        )

        if not isinstance(
            scheduler,
            Mapping,
        ):

            scheduler = {}

        styling = (
            outfit.get(
                "styling",
                {},
            )
        )

        if not isinstance(
            styling,
            Mapping,
        ):

            styling = {}

        reasons = []

        self._add_weather_reason(
            weather,
            reasons,
        )

        self._add_structure_reason(
            outfit,
            reasons,
        )

        self._add_styling_reasons(
            outfit,
            reasons,
        )

        self._add_compatibility_reason(
            outfit,
            reasons,
        )

        self._add_preference_reason(
            outfit,
            scheduler,
            reasons,
        )

        self._add_scheduler_reason(
            scheduler,
            reasons,
        )

        # =================================================
        # RAW DIAGNOSTIC SIGNALS
        #
        # Raw backend reason codes remain here intentionally.
        # They are NOT exposed in user-facing reasons.
        # =================================================

        confidence = (
            outfit.get(
                "personalization_confidence"
            )
        )

        if confidence is None:

            confidence = (
                scheduler.get(
                    "personalization_confidence"
                )
            )

        signals = {

            "weather":
                self._weather_signals(
                    weather
                ),

            "structure":
                self._structure_signals(
                    outfit
                ),

            "styling": {

                "style_score":
                    outfit.get(
                        "style_score"
                    ),

                "reasons":
                    styling.get(
                        "reasons",
                        [],
                    ),

                "components":
                    styling.get(
                        "components",
                        {},
                    ),
            },

            "compatibility": {

                "score":
                    outfit.get(
                        "compatibility_score"
                    ),

                "threshold_flag":
                    outfit.get(
                        "threshold_flag"
                    ),
            },

            "preference": {

                "score":
                    outfit.get(
                        "preference_score",
                        scheduler.get(
                            "preference_score"
                        ),
                    ),

                "rank_score":
                    outfit.get(
                        "preference_rank_score",
                        scheduler.get(
                            "preference_rank_score"
                        ),
                    ),

                "confidence":
                    confidence,

                "weight":
                    outfit.get(
                        "personalization_weight",
                        scheduler.get(
                            "personalization_weight"
                        ),
                    ),
            },

            "scheduler":
                dict(
                    scheduler
                ),
        }

        if not reasons:

            reasons.append(
                (
                    "Gợi ý được tạo từ các "
                    "tín hiệu hiện có của hệ thống."
                )
            )

        return OutfitExplanation(
            summary=(
                self._build_summary(
                    outfit
                )
            ),
            reasons=reasons,
            signals=signals,
        )
