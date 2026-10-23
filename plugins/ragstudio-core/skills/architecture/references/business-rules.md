# RAGStudio business rules (condensed from RAGStudio_Feature_Detail_V7.pdf)

Each rule names the service that enforces it. If code disagrees with this file, ask the user which is right.

## Auth (Keycloak; account-service mirrors status)
- Roles: USER (on sign up), ADMIN (only via Keycloak admin console). One account per user.
- Sign up: email + password (8-64 chars, not equal to email, common passwords blocked), ToS checkbox; Google, GitHub (users only).
- Email verification link 24 h, resend allowed. Reset link 15 min, single use, logs out other sessions.
- Sign in error is always "Invalid email or password". Lock after 5 failures: 1, 2, 3 ... 15 min (Keycloak brute force).
- Forgot password always answers "If an account exists, we've sent a link".
- MFA: TOTP 6 digits; optional for USER, required for ADMIN. No SMS/email OTP/magic link in v1.
- Linking a social account with the same email requires password confirmation.
- Mobile: Face ID/fingerprint required for ADMIN, optional for USER.

## Account lifecycle (account-service)
- Status: UNVERIFIED (cannot sign in) -> ACTIVE -> SUSPENDED (cannot sign in, bots offline) / PENDING_DELETION.
- Change email: verify the new address (24 h link); old email stays active until verified.
- Change password logs out all other sessions.
- Delete: retype email -> PENDING_DELETION immediately; bots offline ("This chatbot is no longer available").
  Sign in within 7 days -> "Restore account" -> ACTIVE, bots return as PAUSED. After 7 days: purge everything.
- Suspend/reactivate needs a reason, emailed to the user; the user appeals by replying to the email.
- Quota defaults: 5 bots, 5 GB (platform_settings); admin can lower or raise per user.
- Every admin action is audited with its reason.

## Chatbot (chatbot-service)
- Create: name <= 50, description <= 200, chat model (default preselected), embedding model (locked forever),
  instructions, tone, answer behaviour, language; knowledge base step skippable. Starts DRAFT. Bot quota checked.
- Status transitions:
  | From | To | Who | When |
  |---|---|---|---|
  | - | DRAFT | owner | create |
  | DRAFT | PENDING | system | first document READY |
  | PENDING | ACTIVE | owner | publish; checklist: >= 1 READY doc, model selected, >= 1 channel |
  | ACTIVE | PAUSED | owner | pause (web or mobile) |
  | PAUSED | ACTIVE | owner | resume |
  | ACTIVE, PAUSED, PENDING | DRAFT | system | last document deleted; channels go offline |
  | ACTIVE, PAUSED | DISABLED | admin | force disable, reason required, owner emailed + pushed, audited |
  | DISABLED | PAUSED | admin | approve appeal or re-enable, reason required |
  | any | deleted | owner | retype bot name |
- DISABLED: owner can still edit docs and settings, but nothing can make it go live except an admin.
- Owner SUSPENDED or PENDING_DELETION: status unchanged, owner_offline = true, all channels answer offline.
- Playground works in every status except DRAFT and DISABLED.
- Guest messages: PAUSED "This assistant is temporarily unavailable"; DISABLED "This chatbot has been disabled";
  deleted/owner offline "This chatbot is no longer available".
- List: search by name, filter by status, sort by name a-z/z-a or message count.

## Configuration (chatbot-service validates, ai-rag-service applies)
- Ranges: temperature 0-1 (0.4); max response 256-4096 (1024); top K 1-20 (5); search SEMANTIC/KEYWORD/HYBRID (HYBRID);
  max context 1000-8000 (4000) and <= model context window - max response; chunk size 200-1000 (500); overlap 0-200 (50).
  Limits live in setting_limits so admins can change them.
- Tone presets are fixed text; CUSTOM <= 300 chars; both appended to the system prompt as "Tone: ...".
- Starter questions: max 4, reorderable.
- Changing chunk size/overlap needs confirmation and re-indexes every document; old index keeps answering until the new one is READY.
- Admin disables/removes a chat model -> bots using it switch to the system fallback (on_system_fallback = true), owners notified, never taken offline.
- Cannot disable/remove the default or fallback model; cannot disable/remove an embedding model any chatbot uses.
- Fallback model: chat type only, must differ from the default chat model.

## Answering (ai-rag-service)
- Answer only from the chatbot's own documents, with citations. Not found -> "Sorry, I couldn't find that in my knowledge base." in the guest's language, no citation, counted as unanswered.
- Language: AUTO replies in the guest's language (KM, EN, KO; mixed text: majority wins). Unsupported language or no supported majority -> English, plus "I can answer in Khmer, English, or Korean". A fixed language always wins.
- Chat model fails -> system fallback answers automatically; both fail -> error + owner push.
- Citations: markers (1), (2) inline; All Sources list; hover shows type icon, name, location.
  Location: PDF page; DOCX/MD nearest heading; XLSX sheet + row range; TXT line range; web page URL.
- Source visibility: FULL_DOCUMENT (guest can open), NAME_ONLY (default; name + location only), HIDDEN (nothing for guests; owner still sees in Playground).

## Knowledge base (knowledge-service + ai-ingestion-worker in ragstudio-ai-service)
- Types: PDF, DOCX, TXT, MD, XLSX; max 20 MB per file; blocked when storage quota reached; drag/drop, multi-file, per-file progress.
- Duplicate: same name or same SHA-256 in the chatbot -> Replace (re-index) or Skip; web pages: same URL.
- Web import: 1-10 links per import, one page per link, per-link failure reason, preview (url, title, content, status) before import; Refresh re-scrapes and re-indexes.
- Status QUEUED -> PROCESSING -> READY / FAILED (reason shown, retry). Rename, replace, delete; search by name; filter by type, status.
- Storage push at 80% (can turn off) and 100% (always on).

## Channels (chatbot-service config, chat-service runtime)
- Public link: generate, enable/disable, regenerate (old link dies), optional expiry, optional QR.
- Guest session: no sign in, starter questions, context only while the page is open; reopening starts fresh.
- Widget: allowed domains list (example.com format), JS snippet, enable/disable; Origin must match.
- Telegram: bot token -> webhook set automatically; status CONNECTED/ERROR with reason; disconnect.
- Source opening: public link uses the built-in Document Viewer; widget and Telegram open a new browser tab.

## Feedback and reports (chat-service)
- Guest marks Helpful / Not helpful, or reports Inaccurate / Unhelpful with optional comment; one feedback per answer.
- Guest chat history is not stored: only the question (for analytics); the answer is stored only when reported.
- Owner gets a push; report status OPEN -> RESOLVED / DISMISSED by the owner. Playground messages are not counted and cannot be reported.

## Appeals (chatbot-service)
- Only when DISABLED; message required, <= 500 chars; one PENDING per chatbot.
- PENDING -> APPROVED (bot PAUSED) or REJECTED (reason shown; new appeal allowed). Owner emailed + pushed; audited.

## Analytics (analytics-notification-service, analytics module)
- Owner: documents, storage, index size; messages, sessions, guests, active sessions; daily/weekly/monthly; per channel (Playground, Public link, Telegram, Widget); unanswered, helpful counts, reported list; usage vs quota.
- Admin cards: registered, active (signed in last 30 days), unverified users; total and published bots; messages today vs yesterday and month vs last month; open reports; pending appeals.
- Admin charts: new users, active users, chatbots, messages, storage, token usage by model; top users by tokens.

## Notifications (analytics-notification-service, notification module)
- Owner push: KB processing failed, URL scraping failed, LLM failed (model + fallback), storage 80%, inaccurate report, unhelpful report;
  always on: disabled by admin, appeal decided, re-enabled, model switched to fallback, storage 100%.
- Admin push: high error rate, user report, backend API error, new appeal; always on: unhandled system error, LLM unavailable, DB connection failure.
- Each non-always-on alert can be turned on/off.
