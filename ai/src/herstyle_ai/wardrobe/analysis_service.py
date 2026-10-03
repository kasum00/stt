from pathlib import Path
import json


from herstyle_ai.preprocessing.background_remover import (
    BackgroundRemover,
)

from herstyle_ai.inference.hybrid_attribute_predictor import (
    HybridAttributePredictor,
)

from herstyle_ai.wardrobe.builder import (
    WardrobeItemBuilder,
)

from herstyle_ai.wardrobe.office_filter import (
    WardrobeOfficeFilter,
)

from herstyle_ai.wardrobe.sanitizer import (
    sanitize_wardrobe_item,
)

from herstyle_ai.wardrobe.models import (
    WardrobeItem,
)

from herstyle_ai.wardrobe.repository import (
    WardrobeRepository,
)


ATTRIBUTE_FIELDS = [
    "category",
    "subcategory",
    "color",
    "material",
    "pattern",
    "sleeve_length",
    "neckline",
    "fit",
    "design_details",
    "style_tags",
]


class WardrobeAnalysisService:

    def __init__(
        self,
        project_root: Path,
        data_root=None,
    ):

        self.project_root = Path(
            project_root
        )
        self.data_root = Path(data_root) if data_root is not None else self.project_root / "data"

        # =====================================
        # BACKGROUND REMOVAL
        # =====================================

        self.background_remover = (
            BackgroundRemover(
                project_root=self.project_root,
                data_root=self.data_root,
            )
        )

        # =====================================
        # ATTRIBUTE PREDICTOR
        # =====================================

        self.predictor = (
            HybridAttributePredictor(
                project_root=self.project_root
            )
        )

        # =====================================
        # WARDROBE PIPELINE
        # =====================================

        self.builder = (
            WardrobeItemBuilder()
        )

        self.office_filter = (
            WardrobeOfficeFilter(
                project_root=self.project_root
            )
        )

        self.repository = (
            WardrobeRepository(
                project_root=self.project_root,
                data_root=self.data_root,
            )
        )

        # =====================================
        # PENDING ANALYSES
        # =====================================

        self.analysis_dir = (
            self.data_root
            / "interim"
            / "wardrobe_analysis"
        )

        self.analysis_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    # =====================================================
    # CONFIRM / EDIT / SAVE
    # =====================================================

    def confirm(
        self,
        analysis_id,
        attributes=None,
    ):

        attributes = (
            attributes
            or {}
        )

        # =====================================
        # 1. LOAD PENDING ANALYSIS
        # =====================================

        record_path = (
            self.analysis_dir
            / f"{analysis_id}.json"
        )

        if not record_path.is_file():

            raise FileNotFoundError(
                "Analysis not found"
            )

        with open(
            record_path,
            "r",
            encoding="utf-8",
        ) as f:

            record = json.load(
                f
            )

        # Prevent duplicate save
        if record.get(
            "status"
        ) == "confirmed":

            raise ValueError(
                "Analysis has already been confirmed"
            )

        preview_item = dict(
            record[
                "preview_item"
            ]
        )

        # =====================================
        # 2. ONLY ALLOW USER-EDITABLE FIELDS
        # =====================================

        editable_fields = {

            "category",
            "subcategory",
            "color",
            "material",
            "pattern",
            "sleeve_length",
            "neckline",
            "fit",
            "design_details",
            "style_tags",
        }

        invalid_fields = (
            set(
                attributes.keys()
            )
            -
            editable_fields
        )

        if invalid_fields:

            raise ValueError(
                "Fields are not editable: "
                + ", ".join(
                    sorted(
                        invalid_fields
                    )
                )
            )

        # =====================================
        # 3. APPLY USER EDITS
        # =====================================

        recognition_sources = dict(
            preview_item.get(
                "recognition_sources",
                {}
            )
        )

        for field, value in (
            attributes.items()
        ):

            preview_item[
                field
            ] = value

            recognition_sources[
                field
            ] = "user_confirmed"

        preview_item[
            "recognition_sources"
        ] = recognition_sources

        # =====================================
        # 4. CONFIRMATION FLAGS
        # =====================================

        needs_confirmation = list(
            preview_item.get(
                "needs_confirmation",
                []
            )
        )

        needs_confirmation = [

            field

            for field in needs_confirmation

            if (
                field
                not in
                attributes
            )
        ]

        preview_item[
            "needs_confirmation"
        ] = needs_confirmation

        # =====================================
        # 5. REBUILD WARDROBE ITEM
        # =====================================

        item = WardrobeItem(
            **preview_item
        )

        # =====================================
        # 6. SANITIZE AGAIN
        #
        # Important because user may change
        # category/subcategory.
        # =====================================

        item = (
            sanitize_wardrobe_item(
                item
            )
        )

        # =====================================
        # 7. OFFICE FILTER AGAIN
        # =====================================

        item = (
            self.office_filter.apply(
                item
            )
        )

        item_dict = (
            item.to_dict()
        )
        # =====================================
        # SOURCE IMAGE HASH
        # =====================================

        item_dict[
            "source_sha256"
        ] = record.get(
            "source_sha256"
        )
        # =====================================
        # 8. KEEP IMAGE PROVENANCE
        #
        # image_path stays model_input_path
        # because compatibility uses cleaned image.
        # Original / transparent are kept as
        # additional metadata.
        # =====================================

        images = record.get(
            "images",
            {},
        )

        item_dict[
            "original_image_path"
        ] = images.get(
            "original_image_path"
        )

        item_dict[
            "transparent_image_path"
        ] = images.get(
            "transparent_image_path"
        )

        item_dict[
            "model_input_path"
        ] = images.get(
            "model_input_path"
        )

        # Keep the canonical model image
        # for downstream AI.
        item_dict[
            "image_path"
        ] = images.get(
            "model_input_path",
            item_dict.get(
                "image_path"
            ),
        )

        # =====================================
        # 9. SAVE TO WARDROBE
        # =====================================

        self.repository.add(
            item_dict
        )

        # =====================================
        # 10. MARK ANALYSIS CONFIRMED
        # =====================================

        record[
            "status"
        ] = "confirmed"

        record[
            "saved_item_id"
        ] = item_dict[
            "item_id"
        ]

        record[
            "confirmed_item"
        ] = item_dict

        with open(
            record_path,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                record,
                f,
                indent=2,
                ensure_ascii=False,
            )

        return item_dict

    # =====================================================
    # ANALYZE
    # =====================================================

    def analyze(
        self,
        original_image_path,
        analysis_id,
        source_sha256=None,
    ):

        original_image_path = Path(
            original_image_path
        )

        # =====================================
        # 1. REMOVE BACKGROUND
        # =====================================

        processed = (
            self.background_remover.process(
                image_path=original_image_path,
                output_id=analysis_id,
            )
        )

        model_input_path = (
            processed[
                "model_input_path"
            ]
        )

        # =====================================
        # 2. ATTRIBUTE PREDICTION
        #
        # IMPORTANT:
        # model receives background-removed image,
        # NOT original image.
        # =====================================

        prediction = (
            self.predictor.predict(
                str(
                    model_input_path
                )
            )
        )

        # =====================================
        # 3. BUILD WARDROBE ITEM
        #
        # image_path points to MODEL INPUT so that
        # downstream DINOv2 / compatibility also
        # works on cleaned garment image.
        # =====================================

        item = (
            self.builder.build(
                image_path=str(
                    model_input_path
                ),
                prediction=prediction,
            )
        )

        # =====================================
        # 4. CATEGORY SANITIZER
        # =====================================

        item = (
            sanitize_wardrobe_item(
                item
            )
        )

        # =====================================
        # 5. OFFICE FILTER
        # =====================================

        item = (
            self.office_filter.apply(
                item
            )
        )

        item_dict = (
            item.to_dict()
        )

        # =====================================
        # 6. PUBLIC ATTRIBUTES
        # =====================================

        attributes = {

            field:
                item_dict.get(
                    field
                )

            for field in ATTRIBUTE_FIELDS
        }

        # =====================================
        # 7. INTERNAL PENDING RECORD
        #
        # Used by CONFIRM/SAVE API later.
        # =====================================

        record = {

            "analysis_id":
                analysis_id,

            "status":
                "pending",

            "source_sha256":
                source_sha256,

            "images": {

                "original_image_path":
                    processed[
                        "original_image_path"
                    ],

                "transparent_image_path":
                    processed[
                        "transparent_image_path"
                    ],

                "model_input_path":
                    processed[
                        "model_input_path"
                    ],
            },

            "background_model":
                processed[
                    "background_model"
                ],

            "preview_item":
                item_dict,
        }

        record_path = (
            self.analysis_dir
            / f"{analysis_id}.json"
        )

        with open(
            record_path,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                record,
                f,
                indent=2,
                ensure_ascii=False,
            )

        # =====================================
        # 8. API RESPONSE
        # =====================================

        return {

            "analysis_id":
                analysis_id,

            "status":
                "analyzed",

            "background_removed":
                True,

            "background_model":
                processed[
                    "background_model"
                ],

            "attributes":
                attributes,

            # Keep the complete preview item in the public response as
            # well as the flattened attributes map.  The confirmation
            # screen needs the same normalized values that are persisted
            # in the pending analysis record.
            "preview_item":
                item_dict,

            "material_candidates":
                item_dict.get(
                    "material_candidates",
                    [],
                ),

            "needs_confirmation":
                item_dict.get(
                    "needs_confirmation",
                    [],
                ),

            "recognition_sources":
                item_dict.get(
                    "recognition_sources",
                    {},
                ),

            "office_relevance":
                item_dict.get(
                    "office_relevance"
                ),

            "office_relevance_reasons":
                item_dict.get(
                    "office_relevance_reasons",
                    [],
                ),
        }
