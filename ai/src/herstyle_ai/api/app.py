from contextlib import asynccontextmanager
from pathlib import Path
from uuid import UUID, uuid4
from io import BytesIO
from typing import Any
from dataclasses import fields
from datetime import datetime, timezone
import json
import logging

import hashlib


from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
    UploadFile,
    File,
)
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from fastapi.concurrency import run_in_threadpool

from fastapi.middleware.cors import (
    CORSMiddleware,
)

from fastapi.responses import (
    FileResponse,
    JSONResponse,
)
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from pydantic import (
    BaseModel,
    Field,
)

from PIL import (
    Image,
    UnidentifiedImageError,
)

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession


from herstyle_ai.recommendation.weather_service import (
    WeatherAwareRecommendationService,
)

from herstyle_ai.recommendation.explainer import (
    OutfitExplanationGenerator,
)

from herstyle_ai.wardrobe.analysis_service import (
    WardrobeAnalysisService,
)

from herstyle_ai.wardrobe.models import (
    WardrobeItem,
)

from herstyle_ai.wardrobe.office_filter import (
    WardrobeOfficeFilter,
)

from herstyle_ai.wardrobe.sanitizer import (
    sanitize_wardrobe_item,
)

from herstyle_ai.wardrobe.taxonomy_validator import (
    WardrobeTaxonomyValidator,
)

from herstyle_ai.personalization import (
    FeedbackEvent,
    FeedbackRepository,
    PreferenceRepository,
    SUPPORTED_FEEDBACK_EVENTS,
    UserPreferenceProfileBuilder,
)

from herstyle_ai.context.date_context import (
    DateContextService,
)

from herstyle_ai.api.routes.auth import (
    router as auth_router,
)

from herstyle_ai.api.routes.profile import (
    router as profile_router,
)

from herstyle_ai.api.routes.preferences import (
    router as explicit_preferences_router,
)

from herstyle_ai.api.routes.saved_outfits import (
    router as saved_outfits_router,
)

from herstyle_ai.api.routes.calendar_events import (
    router as calendar_events_router,
)

from herstyle_ai.api.dependencies import get_current_user
from herstyle_ai.core.config import get_settings
from herstyle_ai.core.observability import configure_logging, log_request
from herstyle_ai.core.rate_limit import rate_limiter
from herstyle_ai.db.models import User
from herstyle_ai.db.session import engine, get_db
from herstyle_ai.db.wardrobe import (
    apply_domain_item_to_record,
    get_owned_wardrobe,
    list_owned_wardrobe,
    new_record_from_domain,
    record_to_domain_item,
)
from herstyle_ai.db.recommendations import (
    RecommendationPersistenceError,
    get_owned_recommendation,
    list_owned_recommendations,
    persist_generated_recommendations,
)
from herstyle_ai.db.calendar_events import get_owned_calendar_event


logger = logging.getLogger(__name__)


optional_bearer_scheme = HTTPBearer(auto_error=False)


async def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        optional_bearer_scheme
    ),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    if credentials is None:
        return None
    return await get_current_user(credentials=credentials, db=db)

# =========================================================
# PROJECT
# =========================================================

settings = get_settings()
configure_logging(settings.log_level)

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[3]
)

RUNTIME_STORAGE_ROOT = (
    Path(settings.storage_root)
    if settings.storage_root
    else PROJECT_ROOT / "data"
)

if settings.storage_backend != "local":
    raise RuntimeError("Unsupported storage backend")

RUNTIME_STORAGE_ROOT.mkdir(parents=True, exist_ok=True)


# =========================================================
# WARDROBE UPLOAD CONFIG
# =========================================================

MAX_UPLOAD_BYTES = settings.max_upload_bytes


UPLOAD_DIR = (
    RUNTIME_STORAGE_ROOT
    / "interim"
    / "wardrobe_uploads"
)


UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


IMAGE_EXTENSION_MAP = {

    "JPEG": ".jpg",

    "PNG": ".png",

    "WEBP": ".webp",
}


# =========================================================
# REQUEST MODELS
# =========================================================

class WeeklyRecommendationRequest(
    BaseModel
):

    latitude: float = Field(
        ge=-90,
        le=90,
    )

    longitude: float = Field(
        ge=-180,
        le=180,
    )

    prefer_dress: bool = False

    days: int = Field(
        default=7,
        ge=1,
        le=7,
    )

    user_id: str = "default"

    styling_request: str | None = None

    event_id: UUID | None = None


class WardrobeConfirmRequest(
    BaseModel
):

    analysis_id: str

    attributes: dict[
        str,
        Any,
    ] = Field(
        default_factory=dict
    )


class WardrobePatchRequest(
    BaseModel
):

    attributes: dict[
        str,
        Any,
    ] = Field(
        default_factory=dict
    )


class FeedbackRequest(
    BaseModel
):

    event_type: str

    user_id: str = "default"

    recommendation_id: str | None = None

    structure: str | None = None

    items: dict[
        str,
        str,
    ] = Field(
        default_factory=dict
    )

    compatibility_score: float | None = None

    style_score: float | None = None

    fusion_score: float | None = None

    ranking_method: str | None = None

    metadata: dict[
        str,
        Any,
    ] = Field(
        default_factory=dict
    )


# =========================================================
# APP
# =========================================================

@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(
    title="HerStyleAI API",
    version="1.0.0",
    docs_url="/docs" if settings.enable_api_docs else None,
    redoc_url="/redoc" if settings.enable_api_docs else None,
    openapi_url="/openapi.json" if settings.enable_api_docs else None,
    lifespan=lifespan,
)


# =========================================================
# CORS
#
# Development only.
# Restrict this for production.
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.frontend_origins),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=list(settings.trusted_hosts),
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    return await log_request(request, call_next)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault(
        "Referrer-Policy",
        "strict-origin-when-cross-origin",
    )
    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(), microphone=(), geolocation=()",
    )
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
    )
    if settings.app_env == "production":
        response.headers.setdefault(
            "Strict-Transport-Security",
            "max-age=31536000; includeSubDomains",
        )
    if request.url.path.startswith("/api/v1/auth"):
        response.headers.setdefault("Cache-Control", "no-store")
    return response


AI_RATE_LIMIT_PATHS = {
    "/api/v1/recommendations/weekly",
    "/api/v1/wardrobe/analyze",
}


@app.middleware("http")
async def expensive_endpoint_rate_limit(request: Request, call_next):
    if request.method == "POST" and request.url.path in AI_RATE_LIMIT_PATHS:
        client_host = request.client.host if request.client else "unknown"
        allowed, retry_after = rate_limiter.check(
            f"ai:{client_host}:{request.url.path}",
            settings.ai_rate_limit,
            settings.rate_limit_window_seconds,
        )
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many AI requests. Please retry later."},
                headers={"Retry-After": str(retry_after)},
            )
    return await call_next(request)

app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(explicit_preferences_router)
app.include_router(saved_outfits_router)
app.include_router(calendar_events_router)


# =========================================================
# LOAD RECOMMENDATION SERVICE ONCE
# =========================================================

service = (
    WeatherAwareRecommendationService(
        project_root=PROJECT_ROOT,
        data_root=RUNTIME_STORAGE_ROOT,
    )
)

outfit_explainer = (
    OutfitExplanationGenerator(
        min_personalization_confidence=0.25
    )
)

feedback_repository = (
    FeedbackRepository(
        project_root=PROJECT_ROOT,
        data_root=RUNTIME_STORAGE_ROOT,
    )
)

preference_repository = (
    PreferenceRepository(
        project_root=PROJECT_ROOT,
        data_root=RUNTIME_STORAGE_ROOT,
    )
)

date_context_service = (
    DateContextService()
)


# =========================================================
# LAZY WARDROBE ANALYSIS SERVICE
# =========================================================

wardrobe_analysis_service = None


def get_wardrobe_analysis_service():

    global wardrobe_analysis_service

    if wardrobe_analysis_service is None:

        print(
            "Loading WardrobeAnalysisService..."
        )

        wardrobe_analysis_service = (
            WardrobeAnalysisService(
                project_root=PROJECT_ROOT,
                data_root=RUNTIME_STORAGE_ROOT,
            )
        )

    return wardrobe_analysis_service


# =========================================================
# OFFICE FILTER FOR CRUD
# =========================================================

wardrobe_office_filter = (
    WardrobeOfficeFilter(
        project_root=PROJECT_ROOT
    )
)

wardrobe_taxonomy_validator = (
    WardrobeTaxonomyValidator(
        project_root=PROJECT_ROOT
    )
)

WARDROBE_DATACLASS_FIELDS = {

    field.name

    for field in fields(
        WardrobeItem
    )
}


EDITABLE_WARDROBE_FIELDS = {

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


# =========================================================
# HELPERS
# =========================================================

def find_wardrobe_item(
    item_id: str,
):

    return (
        service
        .repository
        .get(
            item_id
        )
    )


def prepare_public_item(
    item,
    request: Request,
    *,
    public_image: bool = False,
):

    result = dict(
        item
    )

    item_id = result[
        "item_id"
    ]

    base_url = (
        str(
            request.base_url
        )
        .rstrip("/")
    )

    if public_image:
        result["image_url"] = (
            f"{base_url}"
            f"/api/v1/wardrobe/public/"
            f"{item_id}"
            f"/image"
        )
    else:
        result["image_url"] = (
            f"{base_url}"
            f"/api/v1/wardrobe/"
            f"{item_id}"
            f"/image"
        )

    # Never expose server filesystem
    for field in [

        "image_path",

        "original_image_path",

        "transparent_image_path",

        "model_input_path",

        "source_sha256",

    ]:

        result.pop(
            field,
            None,
        )

    return result


def prepare_public_response(
    result,
    request: Request,
):

    base_url = (
        str(
            request.base_url
        )
        .rstrip("/")
    )

    for day in result.get(
        "schedule",
        [],
    ):

        outfit = day.get(
            "outfit"
        )

        if not outfit:

            continue

        items = outfit.get(
            "items",
            {},
        )

        for item in items.values():

            item_id = item.get(
                "item_id"
            )

            if item_id:

                item[
                    "image_url"
                ] = (
                    f"{base_url}"
                    f"/api/v1/wardrobe/"
                    f"{item_id}"
                    f"/image"
                )

            for field in [

                "image_path",

                "original_image_path",

                "transparent_image_path",

                "model_input_path",

            ]:

                item.pop(
                    field,
                    None,
                )

    return result


def _restore_weekly_response(
    records,
    wardrobe_items,
    request: Request,
):
    """Rebuild a displayable weekly response from persisted snapshots."""

    if not records:
        return {"days": 0, "schedule": []}

    latest_snapshot = dict(records[0].snapshot or {})
    generation_id = latest_snapshot.get("generation_id")
    if generation_id:
        records = [
            record
            for record in records
            if (record.snapshot or {}).get("generation_id") == generation_id
        ]
    else:
        # Older rows predate generation IDs. The newest seven rows are the
        # best available representation of the last generated week.
        records = records[:7]

    wardrobe_by_id = {
        str(item.get("item_id")): item
        for item in wardrobe_items
        if item.get("item_id") is not None
    }
    schedule = []
    for record in records:
        snapshot = dict(record.snapshot or {})
        item_snapshots = snapshot.get("items") or {}
        items = {}
        if isinstance(item_snapshots, dict):
            for slot, item_snapshot in item_snapshots.items():
                if not isinstance(item_snapshot, dict):
                    continue
                item_id = item_snapshot.get("item_id")
                item = wardrobe_by_id.get(str(item_id))
                if item is None:
                    continue
                items[str(slot)] = dict(item)

        outfit = {
            "recommendation_id": snapshot.get("recommendation_id", record.recommendation_id),
            "structure": snapshot.get("structure"),
            "items": items,
            "compatibility_score": snapshot.get("compatibility_score"),
            "style_score": snapshot.get("style_score"),
            "base_score": snapshot.get("base_score"),
            "ranking_method": snapshot.get("ranking_method"),
            "personalization_weight": snapshot.get("personalization_weight"),
            "explanation": snapshot.get("explanation"),
        }
        weather = snapshot.get("weather") or {}
        schedule.append({
            "day": snapshot.get("day"),
            "structure": snapshot.get("structure"),
            "status": "scheduled",
            "quality": "restored",
            "outfit": outfit,
            "weather": weather,
            "request_applied": snapshot.get("request_applied"),
            "explanation": snapshot.get("explanation"),
        })

    schedule.sort(key=lambda day: int(day.get("day") or 0))
    return prepare_public_response(
        {
            "days": len(schedule),
            "schedule": schedule,
            "generation_id": generation_id,
            "restored": True,
        },
        request=request,
    )

# =========================================================
# DUPLICATE DETECTION
# =========================================================

ANALYSIS_DIR = (
    RUNTIME_STORAGE_ROOT
    / "interim"
    / "wardrobe_analysis"
)


def sha256_bytes(
    content: bytes,
):

    return (
        hashlib
        .sha256(
            content
        )
        .hexdigest()
    )


def sha256_file(
    file_path,
):

    file_path = Path(
        file_path
    )

    hasher = (
        hashlib.sha256()
    )

    with open(
        file_path,
        "rb",
    ) as f:

        while True:

            chunk = f.read(
                1024
                * 1024
            )

            if not chunk:

                break

            hasher.update(
                chunk
            )

    return (
        hasher.hexdigest()
    )


def find_duplicate_wardrobe_item(
    source_sha256: str,
    items=None,
):

    if items is None:
        items = service.repository.list_all()

    for item in items:

        # =====================================
        # NEW ITEMS
        # =====================================

        stored_hash = item.get(
            "source_sha256"
        )

        if (
            stored_hash
            and stored_hash
            == source_sha256
        ):

            return item

        # =====================================
        # LEGACY ITEMS
        #
        # Old 19 wardrobe items do not yet
        # contain source_sha256.
        # =====================================

        candidate_path = (

            item.get(
                "original_image_path"
            )

            or

            item.get(
                "image_path"
            )
        )

        if not candidate_path:

            continue

        path = Path(
            candidate_path
        )

        if not path.is_file():

            continue

        try:

            candidate_hash = (
                sha256_file(
                    path
                )
            )

        except OSError:

            continue

        if (
            candidate_hash
            == source_sha256
        ):

            return item

    return None


def find_duplicate_pending_analysis(
    source_sha256: str,
    owner_user_id: str | None = None,
):

    if not ANALYSIS_DIR.is_dir():

        return None

    for record_path in (
        ANALYSIS_DIR.glob(
            "*.json"
        )
    ):

        try:

            with open(
                record_path,
                "r",
                encoding="utf-8",
            ) as f:

                record = (
                    json.load(
                        f
                    )
                )

        except (
            OSError,
            json.JSONDecodeError,
        ):

            continue

        if (
            record.get(
                "source_sha256"
            )
            != source_sha256
        ):

            continue

        if (
            record.get(
                "status"
            )
            == "confirmed"
        ):

            continue

        if owner_user_id is not None and record.get("owner_user_id") != owner_user_id:
            continue

        return record

    return None
# =========================================================
# HEALTH
# =========================================================

@app.get(
    "/health"
)
def health():

    return {

        "status":
            "ok",

        "service":
            "HerStyleAI",
    }


@app.get("/ready")
async def readiness():
    """Readiness probe: the process and PostgreSQL must both be available."""

    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "database": "unavailable"},
        )
    return {"status": "ok", "database": "ok"}


# =========================================================
# DATE / TIME CONTEXT
#
# Python weekday numbering is Monday=0 through Sunday=6.
# =========================================================

@app.get(
    "/api/v1/context/date"
)
def date_context():

    return (
        date_context_service
        .get_date_context()
    )


@app.get(
    "/api/v1/context/week"
)
def week_context():

    return (
        date_context_service
        .get_week_context(
            days=7
        )
    )


# =========================================================
# WEEKLY RECOMMENDATION
# =========================================================

@app.post(
    "/api/v1/recommendations/weekly"
)
async def weekly_recommendation(
    payload: WeeklyRecommendationRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):

    calendar_event_context = None
    if payload.event_id is not None:
        calendar_event = await get_owned_calendar_event(
            db,
            event_id=payload.event_id,
            user_id=current_user.id,
        )
        if calendar_event is None:
            raise HTTPException(status_code=404, detail="Calendar event not found")
        calendar_event_context = {
            "event_id": str(calendar_event.id),
            "event_type": calendar_event.event_type,
            "title": calendar_event.title,
            "start_at": calendar_event.start_at.isoformat(),
            "end_at": (
                calendar_event.end_at.isoformat()
                if calendar_event.end_at is not None
                else None
            ),
            "location": calendar_event.location,
            "styling_context": dict(calendar_event.styling_context or {}),
        }

    try:

        owned_records = await list_owned_wardrobe(db, current_user.id)
        owned_items = [record_to_domain_item(record) for record in owned_records]

        result = await run_in_threadpool(
            service.generate,
            latitude=payload.latitude,
            longitude=payload.longitude,
            prefer_dress=payload.prefer_dress,
            days=payload.days,
            user_id=str(current_user.id),
            styling_request=payload.styling_request,
            wardrobe_items=owned_items,
            calendar_event=calendar_event_context,
        )
        result["generation_id"] = uuid4().hex

        # =================================================
        # OUTFIT EXPLANATIONS
        # =================================================

        for schedule_day in result.get(
            "schedule",
            [],
        ):
            outfit = schedule_day.get(
                "outfit"
            )
            weather = (
                schedule_day.get(
                    "weather"
                )
                or {}
            )
            explanation = (
                outfit_explainer.generate(
                    outfit=outfit,
                    weather=weather,
                )
            )
            schedule_day[
                "explanation"
            ] = explanation.to_dict()

        try:
            await persist_generated_recommendations(
                db,
                user_id=current_user.id,
                result=result,
                source="weekly",
            )
        except RecommendationPersistenceError:
            # Do not return a recommendation that cannot be authorized later.
            raise HTTPException(
                status_code=500,
                detail="Failed to persist recommendation ownership",
            )

        result = (
            prepare_public_response(
                result=result,
                request=request,
            )
        )

        return result

    except HTTPException:
        raise
    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail="Failed to generate recommendation",
        )


@app.get("/api/v1/recommendations/weekly/latest")
async def latest_weekly_recommendation(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    records = await list_owned_recommendations(
        db,
        user_id=current_user.id,
        source="weekly",
        limit=50,
    )
    owned_records = await list_owned_wardrobe(db, current_user.id)
    wardrobe_items = [record_to_domain_item(record) for record in owned_records]
    return _restore_weekly_response(records, wardrobe_items, request)


# =========================================================
# LIST WARDROBE
# =========================================================

@app.get(
    "/api/v1/wardrobe"
)
async def list_wardrobe(
    request: Request,
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):

    if current_user is None:
        items = service.repository.list_all()
    else:
        records = await list_owned_wardrobe(db, current_user.id)
        items = [record_to_domain_item(record) for record in records]

    public_items = [

        prepare_public_item(
            item=item,
            request=request,
            public_image=current_user is None,
        )

        for item in items
    ]

    return {

        "count":
            len(
                public_items
            ),

        "items":
            public_items,
    }


# =========================================================
# ANALYZE WARDROBE IMAGE
#
# Upload
#   -> save original
#   -> remove background
#   -> white model image
#   -> VLM + DINOv2
#   -> sanitizer
#   -> office filter
#   -> pending preview
#
# DOES NOT SAVE TO WARDROBE YET.
# =========================================================

@app.post(
    "/api/v1/wardrobe/analyze"
)
async def analyze_wardrobe_image(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):

    # =====================================================
    # READ FILE
    # =====================================================

    content = (
        file.file.read(
            MAX_UPLOAD_BYTES
            + 1
        )
    )

    if not content:

        raise HTTPException(
            status_code=400,
            detail="Uploaded image is empty",
        )

    if len(
        content
    ) > MAX_UPLOAD_BYTES:

        raise HTTPException(
            status_code=413,
            detail="Image exceeds 10 MB limit",
        )

    # =====================================================
    # SOURCE HASH
    # =====================================================

    source_sha256 = (
        sha256_bytes(
            content
        )
    )


    # =====================================================
    # DUPLICATE IN SAVED WARDROBE
    # =====================================================

    owned_records = await list_owned_wardrobe(db, current_user.id)
    duplicate_item = find_duplicate_wardrobe_item(
        source_sha256,
        items=[record_to_domain_item(record) for record in owned_records],
    )

    if duplicate_item is not None:

        duplicate_item_id = (
            duplicate_item[
                "item_id"
            ]
        )

        base_url = (
            str(
                request.base_url
            )
            .rstrip("/")
        )

        raise HTTPException(
            status_code=409,
            detail={
                "code":
                    "duplicate_wardrobe_item",

                "message":
                    (
                        "This image already exists "
                        "in the wardrobe."
                    ),

                "item_id":
                    duplicate_item_id,

                "image_url":
                    (
                        f"{base_url}"
                        f"/api/v1/wardrobe/"
                        f"{duplicate_item_id}"
                        f"/image"
                    ),
            },
        )


    # =====================================================
    # DUPLICATE PENDING ANALYSIS
    # =====================================================

    pending = find_duplicate_pending_analysis(
        source_sha256,
        owner_user_id=str(current_user.id),
    )

    if pending is not None:

        pending_analysis_id = (
            pending.get(
                "analysis_id"
            )
        )

        raise HTTPException(
            status_code=409,
            detail={
                "code":
                    "duplicate_pending_analysis",

                "message":
                    (
                        "This image has already "
                        "been analyzed and is "
                        "waiting for confirmation."
                    ),

                "analysis_id":
                    pending_analysis_id,
            },
        )
    # =====================================================
    # VERIFY IMAGE
    # =====================================================

    try:

        image = (
            Image.open(
                BytesIO(
                    content
                )
            )
        )

        image_format = (
            image.format
        )

        image.verify()

    except UnidentifiedImageError:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported or invalid image"
            ),
        )

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid image: {exc}"
            ),
        )

    # =====================================================
    # FORMAT
    # =====================================================

    extension = (
        IMAGE_EXTENSION_MAP.get(
            image_format
        )
    )

    if extension is None:

        raise HTTPException(
            status_code=400,
            detail=(
                "Supported formats: "
                "JPEG, PNG, WEBP"
            ),
        )

    # =====================================================
    # ANALYSIS ID
    # =====================================================

    analysis_id = (
        uuid4().hex
    )

    # =====================================================
    # SAVE ORIGINAL
    # =====================================================

    original_path = (
        UPLOAD_DIR
        / (
            f"{analysis_id}"
            f"_original"
            f"{extension}"
        )
    )

    with open(
        original_path,
        "wb",
    ) as f:

        f.write(
            content
        )

    # =====================================================
    # BACKGROUND REMOVAL + ATTRIBUTE AI
    # =====================================================

    try:

        analysis_service = (
            get_wardrobe_analysis_service()
        )

        result = await run_in_threadpool(
            analysis_service.analyze,
            original_image_path=original_path,
            analysis_id=analysis_id,
            source_sha256=source_sha256,
        )

        pending_path = ANALYSIS_DIR / f"{analysis_id}.json"
        with open(pending_path, "r", encoding="utf-8") as pending_file:
            pending_record = json.load(pending_file)
        pending_record["owner_user_id"] = str(current_user.id)
        with open(pending_path, "w", encoding="utf-8") as pending_file:
            json.dump(pending_record, pending_file, indent=2, ensure_ascii=False)

    except Exception as exc:

        logger.exception(
            "wardrobe_analysis_failed",
            extra={
                "request_id": getattr(
                    request.state,
                    "request_id",
                    None,
                ),
                "analysis_id": analysis_id,
                "filename": file.filename,
                "exception_type": type(exc).__name__,
            },
        )

        raise HTTPException(
            status_code=500,
            detail="Wardrobe analysis failed",
        )

    # =====================================================
    # PREVIEW URLS
    # =====================================================

    base_url = (
        str(
            request.base_url
        )
        .rstrip("/")
    )

    result[
        "images"
    ] = {

        "original_url":
            (
                f"{base_url}"
                f"/api/v1/wardrobe/"
                f"analysis/"
                f"{analysis_id}"
                f"/image/original"
            ),

        "transparent_url":
            (
                f"{base_url}"
                f"/api/v1/wardrobe/"
                f"analysis/"
                f"{analysis_id}"
                f"/image/transparent"
            ),

        "model_url":
            (
                f"{base_url}"
                f"/api/v1/wardrobe/"
                f"analysis/"
                f"{analysis_id}"
                f"/image/model"
            ),
    }

    return result


# =========================================================
# RESUME PENDING ANALYSIS
#
# A repeated upload can legitimately hit the duplicate-pending
# guard.  Return the saved analysis contract so the client can
# resume confirmation instead of forcing the user to analyze the
# same image again.
# =========================================================

@app.get(
    "/api/v1/wardrobe/analysis/{analysis_id}"
)
def get_wardrobe_analysis(
    analysis_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    record_path = ANALYSIS_DIR / f"{analysis_id}.json"

    if not record_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Analysis not found",
        )

    try:
        with open(record_path, "r", encoding="utf-8") as record_file:
            record = json.load(record_file)
    except (OSError, json.JSONDecodeError):
        raise HTTPException(
            status_code=404,
            detail="Analysis not found",
        )

    if record.get("owner_user_id") != str(current_user.id):
        raise HTTPException(
            status_code=404,
            detail="Analysis not found",
        )

    preview_item = record.get("preview_item") or {}
    base_url = str(request.base_url).rstrip("/")

    attributes = {
        field: preview_item.get(field)
        for field in (
            "category",
            "subcategory",
            "color",
            "pattern",
            "material",
            "style_tags",
            "design_details",
        )
    }

    return {
        "analysis_id": analysis_id,
        "status": "analyzed" if record.get("status") == "pending" else record.get("status"),
        "background_removed": True,
        "background_model": record.get("background_model"),
        "attributes": attributes,
        "preview_item": preview_item,
        "material_candidates": preview_item.get("material_candidates", []),
        "needs_confirmation": preview_item.get("needs_confirmation", []),
        "recognition_sources": preview_item.get("recognition_sources", {}),
        "office_relevance": preview_item.get("office_relevance"),
        "office_relevance_reasons": preview_item.get("office_relevance_reasons", []),
        "images": {
            "original_url": (
                f"{base_url}/api/v1/wardrobe/analysis/"
                f"{analysis_id}/image/original"
            ),
            "transparent_url": (
                f"{base_url}/api/v1/wardrobe/analysis/"
                f"{analysis_id}/image/transparent"
            ),
            "model_url": (
                f"{base_url}/api/v1/wardrobe/analysis/"
                f"{analysis_id}/image/model"
            ),
        },
    }


# =========================================================
# ANALYSIS IMAGE PREVIEW
# =========================================================

@app.get(
    "/api/v1/wardrobe/"
    "analysis/{analysis_id}/image/{variant}"
)
def wardrobe_analysis_image(
    analysis_id: str,
    variant: str,
    current_user: User = Depends(get_current_user),
):

    allowed_variants = {

        "original":
            "original_image_path",

        "transparent":
            "transparent_image_path",

        "model":
            "model_input_path",
    }

    path_key = (
        allowed_variants.get(
            variant
        )
    )

    if path_key is None:

        raise HTTPException(
            status_code=400,
            detail=(
                "variant must be "
                "original, transparent, or model"
            ),
        )

    record_path = (
        ANALYSIS_DIR
        / f"{analysis_id}.json"
    )

    if not record_path.is_file():

        raise HTTPException(
            status_code=404,
            detail="Analysis not found",
        )

    with open(
        record_path,
        "r",
        encoding="utf-8",
    ) as f:

        record = (
            json.load(
                f
            )
        )

    if record.get("owner_user_id") != str(current_user.id):
        raise HTTPException(
            status_code=404,
            detail="Analysis not found",
        )

    image_path = (
        record.get(
            "images",
            {},
        ).get(
            path_key
        )
    )

    if not image_path:

        raise HTTPException(
            status_code=404,
            detail=(
                "Analysis image not available"
            ),
        )

    image_path = (
        Path(
            image_path
        )
    )

    if not image_path.is_file():

        raise HTTPException(
            status_code=404,
            detail=(
                "Analysis image file not found"
            ),
        )

    return FileResponse(
        path=str(
            image_path
        )
    )


# =========================================================
# CONFIRM / EDIT / SAVE WARDROBE ITEM
# =========================================================

@app.post(
    "/api/v1/wardrobe/confirm"
)
async def confirm_wardrobe_analysis_v3(
    payload: WardrobeConfirmRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record_path = ANALYSIS_DIR / f"{payload.analysis_id}.json"
    if not record_path.is_file():
        raise HTTPException(status_code=404, detail="Analysis not found")

    try:
        with open(record_path, "r", encoding="utf-8") as record_file:
            pending_record = json.load(record_file)
    except (OSError, json.JSONDecodeError):
        raise HTTPException(status_code=404, detail="Analysis not found")

    if pending_record.get("owner_user_id") != str(current_user.id):
        raise HTTPException(status_code=404, detail="Analysis not found")

    base_item = pending_record.get("preview_item", {})
    try:
        validated_attributes = wardrobe_taxonomy_validator.validate_attributes(
            attributes=payload.attributes,
            base_item=base_item,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    try:
        analysis_service = get_wardrobe_analysis_service()
        item = await run_in_threadpool(
            analysis_service.confirm,
            analysis_id=payload.analysis_id,
            attributes=validated_attributes,
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Analysis not found")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to confirm wardrobe item")

    try:
        db_record = new_record_from_domain(user_id=current_user.id, item=item)
        db.add(db_record)
        await db.commit()
        await db.refresh(db_record)
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to persist wardrobe item")

    return {
        "status": "saved",
        "item": prepare_public_item(
            item=record_to_domain_item(db_record),
            request=request,
        ),
    }

def confirm_wardrobe_analysis_legacy(
    payload: WardrobeConfirmRequest,
    request: Request,
):

    try:

        analysis_service = (
            get_wardrobe_analysis_service()
        )

        record_path = (
            ANALYSIS_DIR
            / f"{payload.analysis_id}.json"
        )

        if not record_path.is_file():

            raise HTTPException(
                status_code=404,
                detail="Analysis not found",
            )

        with open(
            record_path,
            "r",
            encoding="utf-8",
        ) as f:

            pending_record = (
                json.load(
                    f
                )
            )

        base_item = (
            pending_record.get(
                "preview_item",
                {},
            )
        )

        try:

            validated_attributes = (
                wardrobe_taxonomy_validator
                .validate_attributes(
                    attributes=(
                        payload.attributes
                    ),
                    base_item=(
                        base_item
                    ),
                )
            )

        except ValueError as exc:

            raise HTTPException(
                status_code=400,
                detail=str(
                    exc
                ),
            )

        item = (
            analysis_service.confirm(
                analysis_id=(
                    payload.analysis_id
                ),
                attributes=(
                    validated_attributes
                ),
            )
        )

    except FileNotFoundError:

        raise HTTPException(
            status_code=404,
            detail="Analysis not found",
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=409,
            detail=str(
                exc
            ),
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(
                exc
            ),
        )

    return {

        "status":
            "saved",

        "item":
            prepare_public_item(
                item=item,
                request=request,
            ),
    }


# =========================================================
# WARDROBE IMAGE
# =========================================================

@app.get(
    "/api/v1/wardrobe/{item_id}/image"
)
async def wardrobe_image_v3(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = await get_owned_wardrobe(
        db,
        user_id=current_user.id,
        item_id=item_id,
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Wardrobe item not found")

    item = record_to_domain_item(record)
    image_path = item.get("transparent_image_path") or item.get("image_path")
    if not image_path:
        raise HTTPException(status_code=404, detail="Image path not available")
    path = Path(image_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Image file not found")
    return FileResponse(path=str(path))

@app.get(
    "/api/v1/wardrobe/public/{item_id}/image"
)
def wardrobe_image_public(
    item_id: str,
):
    return wardrobe_image_legacy(item_id)


def wardrobe_image_legacy(
    item_id: str,
):

    item = (
        find_wardrobe_item(
            item_id
        )
    )

    if item is None:

        raise HTTPException(
            status_code=404,
            detail="Wardrobe item not found",
        )

    # New items use the transparent image for UI.
    # Legacy items fall back to image_path.
    image_path = (

        item.get(
            "transparent_image_path"
        )

        or

        item.get(
            "image_path"
        )
    )

    if not image_path:

        raise HTTPException(
            status_code=404,
            detail="Image path not available",
        )

    path = (
        Path(
            image_path
        )
    )

    if not path.is_file():

        raise HTTPException(
            status_code=404,
            detail="Image file not found",
        )

    return FileResponse(
        path=str(
            path
        )
    )


# =========================================================
# WARDROBE DETAIL
# =========================================================

@app.get(
    "/api/v1/wardrobe/{item_id}"
)
async def wardrobe_detail_v3(
    item_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = await get_owned_wardrobe(
        db,
        user_id=current_user.id,
        item_id=item_id,
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Wardrobe item not found")
    return prepare_public_item(record_to_domain_item(record), request)

def wardrobe_detail_legacy(
    item_id: str,
    request: Request,
):

    item = (
        service
        .repository
        .get(
            item_id
        )
    )

    if item is None:

        raise HTTPException(
            status_code=404,
            detail="Wardrobe item not found",
        )

    return (
        prepare_public_item(
            item=item,
            request=request,
        )
    )


# =========================================================
# PATCH WARDROBE ITEM
# =========================================================

@app.patch(
    "/api/v1/wardrobe/{item_id}"
)
async def patch_wardrobe_item_v3(
    item_id: str,
    payload: WardrobePatchRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    db_record = await get_owned_wardrobe(
        db,
        user_id=current_user.id,
        item_id=item_id,
    )
    if db_record is None:
        raise HTTPException(status_code=404, detail="Wardrobe item not found")

    stored = record_to_domain_item(db_record)
    attributes = payload.attributes
    invalid_fields = set(attributes) - EDITABLE_WARDROBE_FIELDS
    if invalid_fields:
        raise HTTPException(
            status_code=400,
            detail="Fields are not editable: " + ", ".join(sorted(invalid_fields)),
        )

    try:
        attributes = wardrobe_taxonomy_validator.validate_attributes(
            attributes=attributes,
            base_item=stored,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    model_data = {
        key: value
        for key, value in stored.items()
        if key in WARDROBE_DATACLASS_FIELDS
    }
    try:
        item = WardrobeItem(**model_data)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to rebuild wardrobe item")

    recognition_sources = dict(getattr(item, "recognition_sources", {}) or {})
    for field, value in attributes.items():
        setattr(item, field, value)
        recognition_sources[field] = "user_edited"
    item.recognition_sources = recognition_sources

    needs_confirmation = set(getattr(item, "needs_confirmation", []) or [])
    for field, value in attributes.items():
        if value is not None and value != "":
            needs_confirmation.discard(field)
    if "material" in attributes and not attributes.get("material"):
        needs_confirmation.add("material")
    item.needs_confirmation = sorted(needs_confirmation)

    item = sanitize_wardrobe_item(item)
    item = wardrobe_office_filter.apply(item)
    updated = item.to_dict()
    for field in (
        "original_image_path",
        "transparent_image_path",
        "model_input_path",
        "source_sha256",
    ):
        if field in stored:
            updated[field] = stored[field]

    try:
        apply_domain_item_to_record(db_record, updated)
        await db.commit()
        await db.refresh(db_record)
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update wardrobe item")

    return {
        "status": "updated",
        "item": prepare_public_item(record_to_domain_item(db_record), request),
    }

def patch_wardrobe_item_legacy(
    item_id: str,
    payload: WardrobePatchRequest,
    request: Request,
):

    stored = (
        service
        .repository
        .get(
            item_id
        )
    )

    if stored is None:

        raise HTTPException(
            status_code=404,
            detail="Wardrobe item not found",
        )

    attributes = (
        payload.attributes
    )

    # =====================================================
    # CHECK EDITABLE FIELDS
    # =====================================================

    invalid_fields = (

        set(
            attributes.keys()
        )

        -

        EDITABLE_WARDROBE_FIELDS
    )

    if invalid_fields:

        raise HTTPException(
            status_code=400,
            detail=(
                "Fields are not editable: "
                + ", ".join(
                    sorted(
                        invalid_fields
                    )
                )
            ),
        )
    try:

        attributes = (
            wardrobe_taxonomy_validator
            .validate_attributes(
                attributes=(
                    attributes
                ),
                base_item=(
                    stored
                ),
            )
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(
                exc
            ),
        )
    # =====================================================
    # REBUILD DATACLASS
    # =====================================================

    model_data = {

        key:
            value

        for key, value in stored.items()

        if key
        in WARDROBE_DATACLASS_FIELDS
    }

    try:

        item = (
            WardrobeItem(
                **model_data
            )
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to rebuild wardrobe item: "
                f"{exc}"
            ),
        )

    # =====================================================
    # APPLY USER EDITS
    # =====================================================

    recognition_sources = (
        dict(
            getattr(
                item,
                "recognition_sources",
                {},
            )
            or {}
        )
    )

    for field, value in (
        attributes.items()
    ):

        setattr(
            item,
            field,
            value,
        )

        recognition_sources[
            field
        ] = (
            "user_edited"
        )

    item.recognition_sources = (
        recognition_sources
    )

    # =====================================================
    # CONFIRMATION STATE
    # =====================================================

    needs_confirmation = (
        set(
            getattr(
                item,
                "needs_confirmation",
                [],
            )
            or []
        )
    )

    for field, value in (
        attributes.items()
    ):

        # Only a real non-empty value confirms a field.
        if (
            value is not None
            and value != ""
        ):

            needs_confirmation.discard(
                field
            )

    # Material is special:
    # if user clears it, confirmation is required again.

    if "material" in attributes:

        material_value = (
            attributes.get(
                "material"
            )
        )

        if (
            material_value is None
            or material_value == ""
        ):

            needs_confirmation.add(
                "material"
            )

    item.needs_confirmation = (
        sorted(
            needs_confirmation
        )
    )

    # =====================================================
    # SANITIZE
    # =====================================================

    item = (
        sanitize_wardrobe_item(
            item
        )
    )

    # =====================================================
    # OFFICE FILTER
    # =====================================================

    item = (
        wardrobe_office_filter
        .apply(
            item
        )
    )

    updated = (
        item.to_dict()
    )

    # =====================================================
    # PRESERVE IMAGE METADATA
    # =====================================================

    for field in [

        "original_image_path",

        "transparent_image_path",

        "model_input_path",

        "source_sha256",

    ]:

        if field in stored:

            updated[
                field
            ] = (
                stored[
                    field
                ]
            )

    # =====================================================
    # UPDATED AT
    # =====================================================

    updated[
        "updated_at"
    ] = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    # =====================================================
    # SAVE
    # =====================================================

    service.repository.save(
        updated
    )

    return {

        "status":
            "updated",

        "item":
            prepare_public_item(
                item=updated,
                request=request,
            ),
    }


# =========================================================
# DELETE WARDROBE ITEM
# =========================================================

@app.delete(
    "/api/v1/wardrobe/{item_id}"
)
async def delete_wardrobe_item_v3(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = await get_owned_wardrobe(
        db,
        user_id=current_user.id,
        item_id=item_id,
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Wardrobe item not found")

    record.deleted_at = datetime.now(timezone.utc)
    try:
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete wardrobe item")
    return {"status": "deleted", "item_id": item_id}

def delete_wardrobe_item_legacy(
    item_id: str,
):

    item = (
        service
        .repository
        .get(
            item_id
        )
    )

    if item is None:

        raise HTTPException(
            status_code=404,
            detail="Wardrobe item not found",
        )

    deleted = (
        service
        .repository
        .delete(
            item_id
        )
    )

    if not deleted:

        raise HTTPException(
            status_code=500,
            detail="Failed to delete wardrobe item",
        )

    return {

        "status":
            "deleted",

        "item_id":
            item_id,
    }


# =========================================================
# FEEDBACK
# =========================================================

@app.post(
    "/api/v1/feedback"
)
async def create_feedback(
    payload: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):

    # =====================================================
    # EVENT TYPE
    # =====================================================

    if (
        payload.event_type
        not in SUPPORTED_FEEDBACK_EVENTS
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported feedback event: "
                f"{payload.event_type}"
            ),
        )

    if not payload.recommendation_id or not payload.recommendation_id.strip():
        raise HTTPException(
            status_code=400,
            detail="recommendation_id is required",
        )

    # =====================================================
    # EVENT-SPECIFIC VALIDATION
    # =====================================================

    if (
        payload.event_type
        == "item_replaced"
    ):

        required_metadata = (
            "slot",
            "old_item_id",
            "new_item_id",
        )

        missing_metadata = [

            field_name

            for field_name in required_metadata

            if not isinstance(
                payload.metadata.get(
                    field_name
                ),
                str,
            )
            or not payload.metadata.get(
                field_name
            ).strip()
        ]

        if missing_metadata:

            raise HTTPException(
                status_code=400,
                detail=(
                    "item_replaced requires "
                    "metadata fields: "
                    + ", ".join(
                        missing_metadata
                    )
                ),
            )

    if hasattr(
        payload,
        "model_dump",
    ):

        payload_data = (
            payload.model_dump()
        )

    else:

        payload_data = (
            payload.dict()
        )

    recommendation_id = payload_data.pop(
        "recommendation_id",
        None,
    )

    # The request's user_id is legacy input only. Identity comes from JWT.
    payload_data["user_id"] = str(current_user.id)

    recommendation = await get_owned_recommendation(
        db,
        recommendation_id=recommendation_id,
        user_id=current_user.id,
    )
    if recommendation is None:
        raise HTTPException(
            status_code=404,
            detail="Recommendation not found",
        )

    snapshot = dict(recommendation.snapshot or {})

    # Continue only after the authenticated recommendation ownership check.
    if recommendation is not None:
        # Validate wardrobe references supplied by mutation/replacement events.
        referenced_item_ids = list(payload.items.values())
        if payload.event_type == "item_replaced":
            referenced_item_ids.extend(
                [
                    payload.metadata.get("old_item_id"),
                    payload.metadata.get("new_item_id"),
                ]
            )
        for referenced_item_id in referenced_item_ids:
            if referenced_item_id is None:
                continue
            owned_item = await get_owned_wardrobe(
                db,
                user_id=current_user.id,
                item_id=str(referenced_item_id),
            )
            if owned_item is None:
                raise HTTPException(
                    status_code=404,
                    detail="Wardrobe item not found",
                )

        # ---------------------------------------------
        # IDEMPOTENCY
        #
        # Do not store the same event type twice for
        # the same recommendation and user.
        # ---------------------------------------------
        existing_events = (
            feedback_repository
            .list_all(
                user_id=(
                    payload_data.get(
                        "user_id",
                        "default",
                    )
                )
            )
        )

        for existing in existing_events:

            if existing.get(
                "event_type"
            ) != payload_data.get(
                "event_type"
            ):

                continue

            existing_metadata = (
                existing.get(
                    "metadata"
                )
                or {}
            )

            if not isinstance(
                existing_metadata,
                dict,
            ):

                continue

            if str(
                existing_metadata.get(
                    "recommendation_id"
                )
            ) == str(
                recommendation_id
            ):

                return {
                    "status": "already_saved",
                    "event": existing,
                }

        payload_data[
            "structure"
        ] = snapshot.get(
            "structure"
        )

        snapshot_items = snapshot.get(
            "items",
            {},
        )

        if not isinstance(
            snapshot_items,
            dict,
        ):

            snapshot_items = {}

        payload_data[
            "items"
        ] = {
            str(slot): item.get(
                "item_id"
            )
            for slot, item in snapshot_items.items()
            if isinstance(
                item,
                dict,
            )
            and item.get(
                "item_id"
            ) is not None
        }

        payload_data[
            "compatibility_score"
        ] = snapshot.get(
            "compatibility_score"
        )

        payload_data[
            "style_score"
        ] = snapshot.get(
            "style_score"
        )

        payload_data[
            "ranking_method"
        ] = snapshot.get(
            "ranking_method"
        )

        payload_data[
            "fusion_score"
        ] = snapshot.get(
            "fusion_score"
        )

        if payload_data[
            "fusion_score"
        ] is None:

            payload_data[
                "fusion_score"
            ] = snapshot.get(
                "personalized_score"
            )

        if payload_data[
            "fusion_score"
        ] is None:

            payload_data[
                "fusion_score"
            ] = snapshot.get(
                "base_score"
            )

        metadata = payload_data.get(
            "metadata"
        )

        if not isinstance(
            metadata,
            dict,
        ):

            metadata = {}

        metadata[
            "recommendation_id"
        ] = str(
            recommendation_id
        )

        metadata[
            "training_snapshot"
        ] = snapshot

        payload_data[
            "metadata"
        ] = metadata

    try:

        event = (
            FeedbackEvent(
                **payload_data
            )
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(
                exc
            ),
        )

    saved = (
        feedback_repository.add(
            event
        )
    )

    return {

        "status":
            "saved",

        "event":
            saved,
    }


@app.get(
    "/api/v1/feedback"
)
async def list_feedback(
    current_user: User = Depends(get_current_user),
):

    events = (
        feedback_repository
        .list_all(
            user_id=str(current_user.id)
        )
    )

    return {

        "user_id":
            str(current_user.id),

        "count":
            len(
                events
            ),

        "events":
            events,
    }


# =========================================================
# PREFERENCE PROFILE
# =========================================================

def build_user_preference_profile(
    user_id: str,
):

    events = (
        feedback_repository
        .list_all(
            user_id=user_id
        )
    )

    wardrobe_items = (
        service
        .repository
        .list_all()
    )

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

    preference_repository.save(
        profile
    )

    return profile


@app.post(
    "/api/v1/preferences/{user_id}/rebuild"
)
def rebuild_preferences(
    user_id: str,
):

    profile = (
        build_user_preference_profile(
            user_id
        )
    )

    return {
        "status": "rebuilt",
        "profile": profile.to_dict(),
    }


@app.get(
    "/api/v1/preferences/{user_id}"
)
def get_preferences(
    user_id: str,
):

    profile = (
        preference_repository.load(
            user_id
        )
    )

    if profile is None:
        profile = (
            build_user_preference_profile(
                user_id
            )
        )

    return {
        "profile": profile.to_dict(),
    }
