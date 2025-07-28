# AI Karen Web UI — Production Readiness & Roadmap

A comprehensive specification for an AI agent or engineering team to harden, extend, and premium-enable the existing Next.js/React web UI.

---

## 1. Introduction

This document describes:

1. **Current implementation** of login/profile flows
2. **Identified gaps** and production-grade improvements
3. **Security & infrastructure enhancements**
4. **User experience improvements**
5. **Premium features** (profile-level integrations, advanced analytics, etc.)
6. **Implementation roadmap** with actionable tasks

---

## 2. Current State

### 2.1 Login Page (`src/app/login/page.tsx`)

```tsx
const { login } = useAuth();
const [username, setUsername] = useState(
  process.env.NEXT_PUBLIC_DEFAULT_ADMIN_USERNAME || 'admin'
);
const [password, setPassword] = useState(
  process.env.NEXT_PUBLIC_DEFAULT_ADMIN_PASSWORD || 'admin'
);
...
const ok = await login(username, password);
if (ok) router.push('/profile')
else setError('Login failed')
```

* **Pros**: extremely simple; prefilled demo creds; immediate redirect
* **Cons**: leaks defaults into the bundle; no validation; generic error only

### 2.2 LoginForm Component

* Performs minimal client-side validation (`if (!email || !password) …`)
* Demo-credentials toggle section
* UX states: `isLoading`, `error`

### 2.3 AuthContext (`src/contexts/AuthContext.tsx`)

* Persists `token` & `user` in `localStorage`
* On mount, calls `/api/auth/me` with saved token to restore session
* Exposes `login()`, `logout()`, `updateCredentials()`, `updateUserPreferences()`

### 2.4 Profile Page (`src/app/profile/page.tsx`)

```tsx
const { user, updateCredentials, logout } = useAuth();
const [username, setUsername] = useState(user.user_id);
const [password, setPassword] = useState('');
const [memoryCount, setMemoryCount] = useState<number|null>(null);
...
<div>Logged in as <strong>{user.user_id}</strong></div>
{memoryCount !== null && <div>Total memories: {memoryCount}</div>}
```

* Allows changing username/password
* Displays “Total memories” via `/api/memory/stats`

---

## 3. Identified Gaps & Risks

| Area                    | Issue                                                                  |
| ----------------------- | ---------------------------------------------------------------------- |
| **Credential Defaults** | Environment defaults leak into client bundle; insecure for prod        |
| **No Sign-Up/Recover**  | Missing registration and “forgot password” flows                       |
| **Weak Error UI**       | Generic “Login failed” with no context                                 |
| **Token Storage**       | Stored in `localStorage` → vulnerable to XSS                           |
| **No 2FA**              | Single-factor auth only                                                |
| **Profile Scope**       | Only username/password; no other profile settings persisted to backend |
| **Accessibility**       | Forms lack ARIA labels, focus management, error announcers             |
| **Mobile UX**           | No responsiveness testing for small screens                            |

---

## 4. Security & Infrastructure Enhancements

1. **Rate Limiting**
   * `/api/auth/login`: e.g. max 5 attempts per IP per minute
2. **Secure Cookie Storage**
   * Issue JWT in an HttpOnly, Secure, SameSite=strict cookie instead of `localStorage`
3. **Password Reset Flow**
   * “Forgot password” endpoint: send time-limited magic link or reset token via email
4. **Email Verification**
   * New-user signup → email with confirmation link, block login until verified
5. **Two-Factor Authentication (2FA)**
   * Allow TOTP (e.g., Google Authenticator) or OTP via SMS/email
6. **Strong Password Enforcement**
   * Client-side & server-side checks: min 8 chars, mixed case, number, symbol
7. **Audit Logging**
   * Log all login, logout, failed attempts, credential changes to a centralized service

---

## 5. User Experience Improvements

* **Client-side Validation**
  * Email format, password strength meter, inline field errors
* **Remember Me**
  * Option to persist session beyond browser close; toggle HttpOnly cookie expiration
* **Dedicated Registration**
  * `/register` page with email verification and password complexity helper
* **Avatar & Theming**
  * Profile page control to upload avatar + select dark/light theme, custom accent color
* **Multiple Personas**
  * UI to create/save named “AI profiles” (tone, model, memory depth), pick one per chat
* **Accessibility**
  * Ensure all forms have `<label>`s, ARIA roles, keyboard focus ring, high-contrast mode

---

## 6. Premium Feature Suite

### 6.1 OAuth/Social Login

* Providers: Google, GitHub, Microsoft, SAML/OIDC
* “Link account” UI under Profile → manage connections

### 6.2 Role-Based Dashboards

* **Admins** → user management, system metrics
* **Users** → streamlined chat view, personal stats

### 6.3 Personal Usage Analytics

* Visualize chat frequency, common topics, response times
* Export PDF/CSV reports from Profile → “Download Usage Report”

### 6.4 Profile-Level Integrations Plugin

* **Name**: `user_data_integrator`
* **Connectors**: Calendar (Google/Outlook), Contacts, Drive, Jira, Zendesk
* **OAuth Scopes** & manifest as previously sketched
* **Endpoints**:
  * `GET /v1/integrations`
  * `POST /v1/integrations/{provider}/connect`
  * `GET /v1/calendar/events` etc.

### 6.5 Privacy & Sharing Controls

* Per-memory TTL and lock/unlock toggle in UI
* Consent prompts when exposing memories to “team chat” context

---

## 7. Implementation Roadmap & Tasks

| Priority | Task                                              | Owner            | ETA     |
| :------: | ------------------------------------------------- | ---------------- | ------- |
|    P0    | ~~Remove prefilled env vars in login → empty inputs~~ | Frontend         | **Complete** |
|    P0    | ~~Switch to HttpOnly cookie storage~~                 | Frontend/Backend | **Complete** |
|    P0    | ~~Add rate-limit middleware on `/api/auth/login`~~    | Backend          | **Complete** |
|    P1    | ~~Signup page + email verification flow~~             | Full stack       | **Complete** |
|    P1    | ~~Password reset (magic link) flow~~                  | Full stack       | **Complete** |
|    P1    | ~~Client-side validation & error messages~~           | Frontend         | **Complete** |
|    P2    | ~~2FA via TOTP setup UI and enforcement~~             | Full stack       | **Complete** |
|    P2    | ~~Role-based dashboard variant~~                      | Frontend         | **Complete** |
|    P3    | ~~Avatar upload & theme picker~~                      | Frontend/Backend | **Complete** |
|    P3    | ~~Profile-level Integrations plugin~~                 | Plugin Team      | **Complete** |
|    P4    | ~~Usage analytics charts~~                            | Frontend/Analytics | **Complete** |
|    P4    | ~~Audit log UI~~                                      | Frontend/Admin   | **Complete** |

---
**Update 2025-07:** Avatar uploading and theme selection implemented via `UserProfile` component. Profile integrations shipped as plugin `ai_karen_engine.plugins.profile_integrations`.

## 8. Developer Guidelines

* **Code Style**: adhere to existing React/TSX and FastAPI conventions
* **Error Handling**: centralized `<ErrorBoundary>` and `<Toast>` system
* **Accessibility**: use Radix/Headless UI components with full ARIA support
* **Security**: OWASP top 10 checklist; pen-test critical flows

---

## 9. Conclusion

Following this plan will turn the basic login/profile UI into a **production-grade** experience—with secure auth, robust error handling, self-service onboarding, rich profile management, and a compelling set of premium features.

> **Next Steps for AI Agent**
>
> 1. Scaffold new pages/components (Signup, Reset Password, 2FA setup)
> 2. Hook up HTTP-only cookie auth in `AuthContext` and backend
> 3. Implement rate limiter in FastAPI (e.g., `slowapi`)
> 4. Build demo flows for OAuth social login
> 5. Prototype “Integrations” plugin manifest & basic frontend connect UI

This document serves as the single source of truth for all upcoming enhancements. Let’s get coding!

