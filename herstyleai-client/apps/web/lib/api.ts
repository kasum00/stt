import {
  clearTokens,
  getAccessToken,
  setAccessToken,
} from "@/lib/auth/token-store";

export type User = {
  id: string;
  email: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
  last_login_at: string | null;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
  expires_in: number;
};

export type PasswordResetResponse = {
  message: string;
  reset_token?: string;
};

export type Profile = {
  id: string;
  user_id: string;
  display_name: string | null;
  avatar_url: string | null;
  timezone: string;
  locale: string;
  location_name: string | null;
  latitude: number | null;
  longitude: number | null;
  created_at: string | null;
  updated_at: string | null;
};

export type ProfilePatch = {
  display_name?: string | null;
  avatar_url?: string | null;
  timezone?: string | null;
  locale?: string | null;
  location_name?: string | null;
  latitude?: number | null;
  longitude?: number | null;
};

export type Preferences = {
  id: string;
  user_id: string;
  prefer_dress: boolean;
  preferred_colors: string[] | null;
  avoided_colors: string[] | null;
  preferred_categories: string[] | null;
  avoided_categories: string[] | null;
  preferred_styles: string[] | null;
  avoided_styles: string[] | null;
  notification_preferences: Record<string, unknown> | null;
};

export type PreferencesPatch = Partial<Omit<Preferences, "id" | "user_id">>;

export type FeedbackEventType =
  | "outfit_shown"
  | "outfit_opened"
  | "outfit_liked"
  | "outfit_disliked"
  | "outfit_saved"
  | "outfit_worn"
  | "outfit_skipped"
  | "outfit_regenerated"
  | "item_replaced"
  | "outfit_edited";

export type WardrobeItem = {
  item_id: string;
  category?: string | null;
  subcategory?: string | null;
  color?: string | null;
  pattern?: string | null;
  material?: string | null;
  style_tags?: string[] | null;
  design_details?: string[] | null;
  image_url?: string | null;
  image_path?: string | null;
  transparent_image_url?: string | null;
  transparent_url?: string | null;
  model_url?: string | null;
  source?: string | null;
  [key: string]: unknown;
};

export type AnalysisResult = {
  analysis_id: string;
  status?: string;
  category?: string | null;
  subcategory?: string | null;
  color?: string | null;
  pattern?: string | null;
  material?: string | null;
  style_tags?: string[] | null;
  design_details?: string[] | null;
  needs_confirmation?: string[] | null;
  preview_item?: WardrobeItem | null;
  attributes?: Partial<WardrobeItem> | null;
  images?: {
    original_url?: string | null;
    transparent_url?: string | null;
    model_url?: string | null;
  };
  [key: string]: unknown;
};

export type OutfitExplanation = {
  summary?: string;
  reasons?: string[];
  signals?: Record<string, unknown>;
};

export type Outfit = {
  recommendation_id?: string | null;
  structure?: string | null;
  score?: number | null;
  compatibility_score?: number | null;
  style_score?: number | null;
  fusion_score?: number | null;
  preference_score?: number | null;
  personalization_weight?: number | null;
  ranking_method?: string | null;
  personalization_method?: string | null;
  items?: Record<string, WardrobeItem>;
  explanation?: OutfitExplanation;
  scheduler?: Record<string, unknown>;
  [key: string]: unknown;
};

export type Weather = {
  date?: string | null;
  temperature?: number | null;
  temperature_c?: number | null;
  feels_like?: number | null;
  rain_probability?: number | null;
  precipitation_probability?: number | null;
  description?: string | null;
  condition?: string | null;
  [key: string]: unknown;
};

export type ScheduleDay = {
  day: number;
  structure?: string | null;
  status?: string | null;
  quality?: string | null;
  outfit?: Outfit | null;
  weather?: Weather | null;
  request_applied?: boolean;
  explanation?: OutfitExplanation;
  [key: string]: unknown;
};

export type CalendarEvent = {
  id: string;
  title: string;
  description: string | null;
  start_at: string;
  end_at: string | null;
  location: string | null;
  event_type: string | null;
  styling_context: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
};

export type CalendarEventInput = {
  title: string;
  description?: string | null;
  start_at: string;
  end_at?: string | null;
  location?: string | null;
  event_type?: string | null;
  styling_context?: Record<string, unknown> | null;
};

export type SavedOutfit = {
  id: string;
  recommendation_id: string;
  title: string | null;
  snapshot: Record<string, unknown>;
  saved_at: string;
  created_at: string;
  updated_at: string;
};

export type WeeklyResponse = {
  days?: number;
  schedule: ScheduleDay[];
  location?: { latitude?: number; longitude?: number };
  styling_request?: string | null;
  request_constraints?: Record<string, unknown> | null;
  calendar_event?: Record<string, unknown> | null;
  [key: string]: unknown;
};

const WEEKLY_RECOMMENDATION_CACHE_KEY = "herstyleai:weekly-recommendation:v1";

export function cacheWeeklyRecommendation(value: WeeklyResponse) {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.setItem(WEEKLY_RECOMMENDATION_CACHE_KEY, JSON.stringify(value));
  } catch {
    // Storage can be unavailable in private browsing; the API result still works.
  }
}

export function readCachedWeeklyRecommendation(): WeeklyResponse | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.sessionStorage.getItem(WEEKLY_RECOMMENDATION_CACHE_KEY);
    if (!raw) return null;
    const value = JSON.parse(raw) as WeeklyResponse;
    return Array.isArray(value.schedule) ? value : null;
  } catch {
    return null;
  }
}

export type WeeklyRequest = {
  latitude: number;
  longitude: number;
  prefer_dress: boolean;
  days: number;
  styling_request?: string | null;
  event_id?: string | null;
};

export type FeedbackPayload = {
  event_type: FeedbackEventType;
  recommendation_id: string;
  structure?: string | null;
  items?: Record<string, string>;
  compatibility_score?: number | null;
  style_score?: number | null;
  fusion_score?: number | null;
  ranking_method?: string | null;
  metadata?: Record<string, unknown>;
};

export class ApiError extends Error {
  status: number;
  payload?: unknown;

  constructor(message: string, status = 0, payload?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

const configuredApiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
if (!configuredApiBaseUrl && process.env.NODE_ENV === "production") {
  throw new Error("NEXT_PUBLIC_API_BASE_URL must be set for production builds");
}
const API_BASE_URL = (
  configuredApiBaseUrl ?? "http://127.0.0.1:8000"
).replace(/\/$/, "");

export function resolveMediaUrl(value?: string | null): string | null {
  if (!value) return null;
  if (/^https?:\/\//i.test(value)) return value;
  return `${API_BASE_URL}${value.startsWith("/") ? value : `/${value}`}`;
}

function messageFromPayload(payload: unknown, fallback: string): string {
  if (typeof payload === "string" && payload.trim()) return payload;
  if (payload && typeof payload === "object") {
    const record = payload as Record<string, unknown>;
    const detail = record.detail ?? record.message ?? record.error;
    if (typeof detail === "string" && detail.trim()) return detail;
    if (Array.isArray(detail)) return "Yêu cầu không hợp lệ. Vui lòng kiểm tra lại thông tin.";
  }
  return fallback;
}

type RequestOptions = RequestInit & {
  skipAuth?: boolean;
  skipRefresh?: boolean;
};

async function performRequest<T>(
  path: string,
  init: RequestOptions = {},
  timeoutMs = 30000,
): Promise<T> {
  const controller = new AbortController();
  const timer = globalThis.setTimeout(() => controller.abort(), timeoutMs);
  const { skipAuth, ...fetchInit } = init;
  const headers = new Headers(fetchInit.headers);
  if (fetchInit.body && !(fetchInit.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (!skipAuth) {
    const accessToken = getAccessToken();
    if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  }

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...fetchInit,
      credentials: "include",
      headers,
      signal: controller.signal,
    });
    const text = await response.text();
    let payload: unknown = null;
    if (text) {
      try {
        payload = JSON.parse(text) as unknown;
      } catch {
        payload = text;
      }
    }
    if (!response.ok) {
      throw new ApiError(
        messageFromPayload(payload, "Không thể kết nối với HerStyleAI."),
        response.status,
        payload,
      );
    }
    return payload as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError("Kết nối quá thời gian. Vui lòng thử lại.");
    }
    throw new ApiError("Không thể kết nối máy chủ. Hãy kiểm tra API đang chạy rồi thử lại.");
  } finally {
    globalThis.clearTimeout(timer);
  }
}

let refreshPromise: Promise<boolean> | null = null;

async function refreshOnce(): Promise<boolean> {
  if (refreshPromise) return refreshPromise;

  refreshPromise = performRequest<TokenResponse>(
    "/api/v1/auth/refresh",
    {
      method: "POST",
      skipAuth: true,
      skipRefresh: true,
    },
  ).then((tokens) => {
    setAccessToken(tokens.access_token);
    return true;
  }).catch((error) => {
    // A temporary network/server failure must not erase the user's session.
    // Only a confirmed 401 means that the refresh cookie is no longer valid.
    if (error instanceof ApiError && error.status === 401) return false;
    throw error;
  }).finally(() => {
    refreshPromise = null;
  });
  return refreshPromise;
}

function isAuthEndpoint(path: string) {
  return /^\/api\/v1\/auth\/(register|login|refresh|logout|forgot-password|reset-password)$/.test(path);
}

async function request<T>(
  path: string,
  init: RequestOptions = {},
  timeoutMs = 30000,
): Promise<T> {
  try {
    return await performRequest<T>(path, init, timeoutMs);
  } catch (error) {
    if (
      error instanceof ApiError &&
      error.status === 401 &&
      !init.skipRefresh &&
      !isAuthEndpoint(path)
    ) {
      if (await refreshOnce()) {
        return performRequest<T>(path, init, timeoutMs);
      }
      clearTokens();
      throw new ApiError("Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.", 401);
    }
    throw error;
  }
}

function queryString(values: Record<string, string | number | undefined>) {
  const params = new URLSearchParams();
  Object.entries(values).forEach(([key, value]) => {
    if (value !== undefined) params.set(key, String(value));
  });
  const result = params.toString();
  return result ? `?${result}` : "";
}

export const api = {
  register(email: string, password: string) {
    return request<User>("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
      skipAuth: true,
      skipRefresh: true,
    });
  },

  async login(email: string, password: string) {
    const tokens = await request<TokenResponse>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
      skipAuth: true,
      skipRefresh: true,
    });
    setAccessToken(tokens.access_token);
    return tokens;
  },

  async refresh() {
    if (!(await refreshOnce())) throw new ApiError("Phiên đăng nhập đã hết hạn.", 401);
    const accessToken = getAccessToken();
    if (!accessToken) throw new ApiError("Phiên đăng nhập đã hết hạn.", 401);
    return { access_token: accessToken };
  },

  logout() {
    return request<{ status: string }>("/api/v1/auth/logout", {
      method: "POST",
      skipAuth: true,
      skipRefresh: true,
    });
  },

  getMe() {
    return request<User>("/api/v1/auth/me");
  },

  updateMe(email: string) {
    return request<User>("/api/v1/auth/me", {
      method: "PATCH",
      body: JSON.stringify({ email }),
    });
  },

  changePassword(currentPassword: string, newPassword: string) {
    return request<{ status: string }>("/api/v1/auth/change-password", {
      method: "POST",
      body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
    });
  },

  requestPasswordReset(email: string) {
    return request<PasswordResetResponse>("/api/v1/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email }),
      skipAuth: true,
      skipRefresh: true,
    });
  },

  resetPassword(token: string, newPassword: string) {
    return request<PasswordResetResponse>("/api/v1/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ token, new_password: newPassword }),
      skipAuth: true,
      skipRefresh: true,
    });
  },

  getProfile() {
    return request<Profile>("/api/v1/profile");
  },

  patchProfile(payload: ProfilePatch) {
    return request<Profile>("/api/v1/profile", {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },

  getPreferences() {
    return request<Preferences>("/api/v1/preferences");
  },

  patchPreferences(payload: PreferencesPatch) {
    return request<Preferences>("/api/v1/preferences", {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },

  getDateContext() {
    return request<Record<string, unknown>>("/api/v1/context/date");
  },

  getWeekContext() {
    return request<Record<string, unknown>>("/api/v1/context/week");
  },

  getWardrobe() {
    return request<{ count: number; items: WardrobeItem[] }>("/api/v1/wardrobe");
  },

  getWardrobeItem(itemId: string) {
    return request<WardrobeItem>(`/api/v1/wardrobe/${encodeURIComponent(itemId)}`);
  },

  analyzeGarment(file: File) {
    const body = new FormData();
    body.append("file", file);
    return request<AnalysisResult>("/api/v1/wardrobe/analyze", { method: "POST", body }, 120000);
  },

  getPendingAnalysis(analysisId: string) {
    return request<AnalysisResult>(
      `/api/v1/wardrobe/analysis/${encodeURIComponent(analysisId)}`,
    );
  },

  confirmGarment(analysisId: string, attributes: Record<string, unknown>) {
    return request<{ status: string; item: WardrobeItem }>("/api/v1/wardrobe/confirm", {
      method: "POST",
      body: JSON.stringify({ analysis_id: analysisId, attributes }),
    });
  },

  updateGarment(itemId: string, attributes: Record<string, unknown>) {
    return request<{ status: string; item: WardrobeItem }>(
      `/api/v1/wardrobe/${encodeURIComponent(itemId)}`,
      { method: "PATCH", body: JSON.stringify({ attributes }) },
    );
  },

  deleteGarment(itemId: string) {
    return request<{ status: string; item_id: string }>(
      `/api/v1/wardrobe/${encodeURIComponent(itemId)}`,
      { method: "DELETE" },
    );
  },

  getWeeklyRecommendation(payload: WeeklyRequest) {
    return request<WeeklyResponse>("/api/v1/recommendations/weekly", {
      method: "POST",
      body: JSON.stringify(payload),
    }, 180000);
  },

  sendFeedback(payload: FeedbackPayload) {
    return request<Record<string, unknown>>("/api/v1/feedback", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  saveOutfit(recommendationId: string, title?: string | null) {
    return request<SavedOutfit>("/api/v1/saved-outfits", {
      method: "POST",
      body: JSON.stringify({ recommendation_id: recommendationId, title }),
    });
  },

  listSavedOutfits() {
    return request<{ count: number; items: SavedOutfit[] }>("/api/v1/saved-outfits");
  },

  getSavedOutfit(savedOutfitId: string) {
    return request<SavedOutfit>(`/api/v1/saved-outfits/${encodeURIComponent(savedOutfitId)}`);
  },

  updateSavedOutfit(savedOutfitId: string, title: string | null) {
    return request<SavedOutfit>(`/api/v1/saved-outfits/${encodeURIComponent(savedOutfitId)}`, {
      method: "PATCH",
      body: JSON.stringify({ title }),
    });
  },

  deleteSavedOutfit(savedOutfitId: string) {
    return request<{ status: string; id: string }>(`/api/v1/saved-outfits/${encodeURIComponent(savedOutfitId)}`, {
      method: "DELETE",
    });
  },

  listCalendarEvents(filters: { from?: string; to?: string; limit?: number; offset?: number } = {}) {
    return request<{ count: number; items: CalendarEvent[]; limit: number; offset: number }>(
      `/api/v1/calendar-events${queryString(filters)}`,
    );
  },

  createCalendarEvent(payload: CalendarEventInput) {
    return request<CalendarEvent>("/api/v1/calendar-events", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  getCalendarEvent(eventId: string) {
    return request<CalendarEvent>(`/api/v1/calendar-events/${encodeURIComponent(eventId)}`);
  },

  updateCalendarEvent(eventId: string, payload: Partial<CalendarEventInput>) {
    return request<CalendarEvent>(`/api/v1/calendar-events/${encodeURIComponent(eventId)}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },

  deleteCalendarEvent(eventId: string) {
    return request<{ status: string; id: string }>(`/api/v1/calendar-events/${encodeURIComponent(eventId)}`, {
      method: "DELETE",
    });
  },
};
