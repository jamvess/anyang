# apps/web — frontend conventions

Next.js (App Router) + TypeScript (strict) + Tailwind CSS + KaTeX, deployed on Vercel. Read the root `CLAUDE.md` first.

## Layout

```
apps/web/
├─ app/                    # routes (App Router)
│  ├─ (auth)/              # login, signup
│  ├─ onboarding/          # tutor + buddy persona
│  ├─ preps/[id]/          # exam prep: upload, confirm types, scope, room
│  └─ page.tsx             # home (exam preps + readiness)
├─ components/
│  ├─ chat/                # MessageList, Bubble (tutor/buddy/user), ProblemCard,
│  │                       #   ProgressCard, OcrPreview, Composer (text/voice/photo)
│  ├─ scope/               # TopicCard, StarBadge, ChangeLog
│  └─ math/                # Tex (KaTeX wrapper)
├─ lib/
│  ├─ api.ts               # typed client generated from the API OpenAPI schema
│  ├─ sse.ts               # POST + ReadableStream SSE reader (EventSource is GET-only)
│  └─ supabase.ts          # @supabase/ssr client
└─ tests/                  # Vitest + Testing Library; Playwright later (e2e)
```

## Rules

- **No business logic in the browser.** Mastery, stars, readiness, buddy decisions come from the API. The frontend renders them.
- The chat room has **no answer choice buttons** (TM-06). Input is text, voice (transcript goes into the composer, user presses send) or photo.
- Stream with `fetch` + `ReadableStream` and parse SSE events; event names come from `specs/system/api.md`.
- Every number, star and level shown must come from the API response, never computed client-side.
- Math is rendered with KaTeX through `components/math/Tex.tsx` only.
- Generate API types from the backend OpenAPI schema (`pnpm gen:api`), do not hand-write request types.
- Accessibility: every interactive element is reachable by keyboard and has a label.
- User-facing text is Thai. Keep strings in one place per screen so they are easy to review.

## Testing patterns

- Component tests named with requirement ID: `it('TM08 renders block LaTeX in tutor bubble')`.
- Mock the SSE stream with recorded event sequences from `tests/fixtures/sse/*.txt`.
