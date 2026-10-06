# HerStyleAI web

Next.js App Router frontend for the HerStyleAI FastAPI backend.

## Local setup

```powershell
Set-Location "E:\stt\herstyleai-client\apps\web"
npm install
Copy-Item .env.example .env.local
npm run dev
```

The local API URL is configured through `NEXT_PUBLIC_API_BASE_URL`; the default is `http://127.0.0.1:8000`.

The browser talks only to FastAPI. It never connects directly to PostgreSQL and no backend secret belongs in the frontend environment.

## Authentication model

The API client adds the short-lived access-token bearer header centrally and
sends `credentials: include` for the backend refresh cookie. Rotating refresh
tokens are replaced atomically through a single in-flight refresh promise, so
concurrent `401` responses do not reuse the same refresh token. The refresh
token is `HttpOnly` and never enters JavaScript, `localStorage`, or
`sessionStorage`. Logout clears the server session when possible and always
clears client auth state and private page state.

The forgot-password flow calls `/api/v1/auth/forgot-password`; reset links use
the `/reset-password` page and submit the one-time token to
`/api/v1/auth/reset-password`.

Production uses an explicit `NEXT_PUBLIC_API_BASE_URL=https://...`; no backend
secret belongs in the frontend environment.

## Verification

```powershell
npm run lint
npx tsc --noEmit
npm run build
```

Run the backend first, then verify register, login, `/me`, refresh, logout, profile/preferences, wardrobe, recommendations/feedback, saved outfits and calendar events with two separate users.
