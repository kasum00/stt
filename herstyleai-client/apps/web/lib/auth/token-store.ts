"use client";

// Access tokens are intentionally memory-only. The refresh token is kept in
// the backend's HttpOnly cookie and is never exposed to JavaScript.
let accessTokenMemory: string | null = null;

export function getAccessToken(): string | null {
  return accessTokenMemory;
}

export function setAccessToken(accessToken: string): void {
  accessTokenMemory = accessToken;
}

export function clearTokens(): void {
  accessTokenMemory = null;
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event("herstyleai:auth-cleared"));
  }
}
