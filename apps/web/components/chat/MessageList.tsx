import { MessageText } from "./MessageText";
import { roomStrings } from "./strings";
import type { ChatMessage } from "./types";

type Speaker = "tutor" | "buddy" | "user";

const SPEAKERS: ReadonlySet<string> = new Set<Speaker>(["tutor", "buddy", "user"]);

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

export function MessageList({ messages, tutorName, buddyName, userName, streamingId = null, typing = false }: Props) {
  const names: Record<Speaker, string> = {
    tutor: tutorName,
    buddy: buddyName ?? "",
    user: userName ?? roomStrings.you,
  };
  // Progress cards and system messages are not shown in S2 (spec §9).
  const visible = messages
    .filter((m) => SPEAKERS.has(m.role))
    .sort((a, b) => Date.parse(a.created_at) - Date.parse(b.created_at));

  return (
    <ol className="flex flex-col">
      {visible.map((m, i) => {
        const role = m.role as Speaker;
        const continued = i > 0 && visible[i - 1].role === role;
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
              {m.input_mode === "image" && m.attachment_path && (
                <p className="my-1 inline-block rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-2 text-xs text-zinc-500">
                  📷 {fileName(m.attachment_path)}
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
