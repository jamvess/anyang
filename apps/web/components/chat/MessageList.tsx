import { MessageText } from "./MessageText";
import { OcrConfirmCard } from "./OcrConfirmCard";
import { ProblemCard } from "./ProblemCard";
import { ProgressCard, type ProgressCardData } from "./ProgressCard";
import { roomStrings } from "./strings";
import type { ChatMessage } from "./types";

type Speaker = "tutor" | "buddy" | "user";

const SPEAKERS: ReadonlySet<string> = new Set<Speaker>(["tutor", "buddy", "user"]);

/**
 * Messages of the same speaker this many minutes apart or more get their own
 * name and time again (chat-room-ui.md AC-3b). A UI value, not a learning-model one.
 */
export const MESSAGE_GROUP_GAP_MIN = 5;
const GAP_MS = MESSAGE_GROUP_GAP_MIN * 60 * 1000;

// Honorifics dropped before taking the initial, so "พี่ตาล" shows "ต" like the wireframe.
const NAME_PREFIXES = ["พี่", "น้อง", "ครู"];
// Thai leading vowels are written before the consonant they follow in speech.
const LEADING_VOWELS = /^[เแโใไ]+/;

/** Avatar letter for a display name (spec §2). */
export function avatarInitial(name: string): string {
  let rest = name.trim();
  const prefix = NAME_PREFIXES.find((p) => rest.startsWith(p) && rest.length > p.length);
  if (prefix) rest = rest.slice(prefix.length).trim();
  rest = rest.replace(LEADING_VOWELS, "") || rest;
  return Array.from(rest || name)[0] ?? "";
}

const timeFormat = new Intl.DateTimeFormat("th-TH", {
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
  timeZone: "Asia/Bangkok",
});

const AVATAR_STYLE: Record<Speaker, string> = {
  tutor: "bg-indigo-100 text-indigo-700",
  buddy: "bg-zinc-200 text-zinc-600",
  user: "bg-zinc-900 text-white",
};

function fileName(path: string): string {
  return path.split("/").pop() ?? path;
}

type Props = {
  messages: ChatMessage[];
  tutorName: string;
  buddyName: string | null;
  userName?: string;
  /** Id of the bubble still receiving tokens: its unclosed math stays hidden. */
  streamingId?: string | null;
  /** Show the tutor's "•••" bubble at the end while waiting for the reply. */
  typing?: boolean;
  /** Buttons of a handwriting confirm card, by message id (ocr-confirm-card.md). */
  onOcrConfirm?: (id: string, lines: string[]) => void;
  onOcrRetake?: (id: string) => void;
};

function Avatar({ role, name }: { role: Speaker; name: string }) {
  return (
    <span
      data-avatar={role}
      aria-hidden
      className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs ${AVATAR_STYLE[role]}`}
    >
      {avatarInitial(name)}
    </span>
  );
}

export function MessageList({
  messages,
  tutorName,
  buddyName,
  userName,
  streamingId = null,
  typing = false,
  onOcrConfirm,
  onOcrRetake,
}: Props) {
  const names: Record<Speaker, string> = {
    tutor: tutorName,
    buddy: buddyName ?? "",
    user: userName ?? roomStrings.you,
  };
  // Bubbles for speakers, a progress card for card messages that carry one (progress-card.md);
  // system messages and empty cards are not shown (chat-room-ui.md AC-4).
  const visible = messages
    .filter((m) => SPEAKERS.has(m.role) || (m.role === "card" && (m.card || m.problem || m.ocr)))
    .sort((a, b) => Date.parse(a.created_at) - Date.parse(b.created_at));

  return (
    <ol className="flex flex-col">
      {visible.map((m, i) => {
        if (m.role === "card") {
          // Not a bubble: no data-role. Also breaks the grouping of the messages around it.
          return (
            <li key={m.id}>
              {m.ocr ? (
                <OcrConfirmCard
                  preview={m.ocr.preview}
                  status={m.ocr.status}
                  onConfirm={(lines) => onOcrConfirm?.(m.id, lines)}
                  onRetake={() => onOcrRetake?.(m.id)}
                />
              ) : m.problem ? (
                <ProblemCard problem={m.problem} />
              ) : (
                <ProgressCard card={m.card as unknown as ProgressCardData} />
              )}
            </li>
          );
        }
        const role = m.role as Speaker;
        const prev = visible[i - 1];
        const continued =
          i > 0 && prev.role === role && Date.parse(m.created_at) - Date.parse(prev.created_at) < GAP_MS;
        return (
          <li key={m.id} data-role={role} className={`flex gap-3 ${continued ? "mt-1" : "mt-4"}`}>
            {continued ? <span className="w-8 shrink-0" aria-hidden /> : <Avatar role={role} name={names[role]} />}
            <div className="min-w-0 text-sm leading-7">
              {!continued && (
                <p className="text-[13px] font-semibold">
                  <span>{names[role]}</span>
                  <time dateTime={m.created_at} className="ml-2 font-mono text-[11px] font-normal text-zinc-400">
                    {timeFormat.format(new Date(m.created_at))}
                  </time>
                </p>
              )}
              {m.input_mode === "image" && (m.attachment_name || m.attachment_path) && (
                <p className="my-1 inline-block rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-2 text-xs text-zinc-500">
                  {/* attachment_name first: the Storage path is a uuid (api.md v1.3 · AC-6b) */}
                  📷 {m.attachment_name || fileName(m.attachment_path!)}
                </p>
              )}
              {m.content && <MessageText content={m.content} streaming={m.id === streamingId} />}
            </div>
          </li>
        );
      })}
      {typing && (
        // Not a message: no data-role, it disappears with the first token.
        <li className="mt-4 flex gap-3">
          <Avatar role="tutor" name={tutorName} />
          <div className="min-w-0 text-sm leading-7">
            <p className="text-[13px] font-semibold">{tutorName}</p>
            <span role="status" aria-label={roomStrings.typing} className="tracking-widest text-zinc-400">
              •••
            </span>
          </div>
        </li>
      )}
    </ol>
  );
}
