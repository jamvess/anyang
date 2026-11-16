"use client";

import Link from "next/link";
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import type { components } from "@/lib/api";
import { apiFetch } from "@/lib/auth";
import { ApiError, errorCode, getJSON, isAuthRedirect } from "./api";
import { POLL_MS } from "./poll";
import { materialStrings as t } from "./strings";

// Spec: specs/features/exam-prep/upload-page.md §2.1 · wireframe S09, S10 · api.md v1.10 + v1.13.
// Kinds and confidence come from the API; this page only shows them (apps/web/CLAUDE.md).

type Material = components["schemas"]["Material"];
type Ticket = components["schemas"]["MaterialUploadTicket"];

/** What the file picker offers; the API decides (api.md v1.10 · `unsupported_type`). */
const ACCEPT = ".pdf,image/*,.heic,.pptx,.docx";
/** api.md v1.13: 1 MB = 1,048,576 bytes. */
const BYTES_PER_MB = 1024 * 1024;

type Row = { key: number; file: File; state: "waiting" | "sending" | "sent" | "failed"; error?: string };
type Phase = { kind: "loading" } | { kind: "notFound" } | { kind: "failed" } | { kind: "files" } | { kind: "kinds" };
/** The result of sending one file: done, refused with a message, or a 401 (login is on its way). */
type Sent = { ok: true } | { ok: false; error: string } | { auth: true };

function size(bytes: number): string {
  return bytes < BYTES_PER_MB ? t.kb(Math.round(bytes / 1024)) : t.mb((bytes / BYTES_PER_MB).toFixed(1));
}

const waiting = (m: Material) => !m.kind_confirmed && m.status === "uploaded";

export function UploadPage({ prepId, navigate }: { prepId: string; navigate: (href: string) => void }) {
  const [phase, setPhase] = useState<Phase>({ kind: "loading" });
  const [attempt, setAttempt] = useState(0);
  const [rows, setRows] = useState<Row[]>([]);
  const [sending, setSending] = useState(false);
  const [materials, setMaterials] = useState<Material[]>([]);
  const [round, setRound] = useState(0);
  const [confirming, setConfirming] = useState(false);
  const [confirmFailed, setConfirmFailed] = useState(false);
  const nextKey = useRef(0);
  // Next keeps a page it leaves hidden (React <Activity>), with its state: work that ends after the
  // user left must not move them (upload-page.md §2.3 · as CreatePrepForm).
  const visible = useRef(true);
  useLayoutEffect(() => {
    visible.current = true;
    return () => {
      visible.current = false;
    };
  }, []);

  const listPath = `/exam-preps/${prepId}/materials`;

  // Opening: files not confirmed yet → the kinds step at once (UC-02 E6), else choosing files.
  useEffect(() => {
    const controller = new AbortController();
    getJSON<Material[]>(listPath, controller.signal).then(
      (list) => {
        if (controller.signal.aborted) return;
        const open = list.filter((m) => !m.kind_confirmed);
        if (open.length > 0) {
          setMaterials(list);
          setPhase({ kind: "kinds" });
        } else {
          setPhase((prev) => (prev.kind === "kinds" ? prev : { kind: "files" }));
        }
      },
      (e) => {
        if (controller.signal.aborted || isAuthRedirect(e)) return;
        setPhase(e instanceof ApiError && e.status === 404 ? { kind: "notFound" } : { kind: "failed" });
      },
    );
    return () => controller.abort();
  }, [listPath, attempt]);

  // The kinds step: ask again every POLL_MS while AI has not looked at a file yet (§2.1.2 item 2).
  const inKinds = phase.kind === "kinds";
  useEffect(() => {
    if (!inKinds) return;
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout> | undefined;
    const run = async () => {
      try {
        const list = await getJSON<Material[]>(listPath, controller.signal);
        if (controller.signal.aborted) return;
        setMaterials(list);
        if (list.some(waiting)) timer = setTimeout(run, POLL_MS);
      } catch (e) {
        if (controller.signal.aborted || isAuthRedirect(e)) return;
        timer = setTimeout(run, POLL_MS); // a failed poll is asked again
      }
    };
    run();
    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [inKinds, listPath, round]);

  function choose(files: FileList | null) {
    if (!files) return;
    const added = [...files].map((file) => ({ key: nextKey.current++, file, state: "waiting" as const }));
    setRows((prev) => [...prev, ...added]);
  }

  const update = (key: number, change: Partial<Row>) =>
    setRows((prev) => prev.map((r) => (r.key === key ? { ...r, ...change } : r)));

  async function sendOne(file: File): Promise<Sent> {
    try {
      const res = await apiFetch(listPath, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          file_name: file.name,
          content_type: file.type || "application/octet-stream",
          size_bytes: file.size,
        }),
      });
      if (res.status === 401) return { auth: true };
      if (!res.ok) {
        const code = await errorCode(res);
        if (code === "unsupported_type") return { ok: false, error: t.unsupported };
        if (code === "file_too_large") return { ok: false, error: t.tooLarge };
        return { ok: false, error: t.uploadFailed };
      }
      const ticket: Ticket = await res.json();
      // The stub's URL cannot be used (as room-photo-send.md §2 item 2): skip the PUT.
      if (res.headers.get("X-Stub") !== "true") {
        // A signed URL: no Authorization, not through apiFetch.
        const put = await fetch(ticket.upload_url, {
          method: "PUT",
          headers: file.type ? { "Content-Type": file.type } : {},
          body: file,
        });
        if (!put.ok) return { ok: false, error: t.uploadFailed };
      }
      const done = await apiFetch(`/materials/${ticket.material_id}/uploaded`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });
      if (done.status === 401) return { auth: true };
      return done.ok ? { ok: true } : { ok: false, error: t.uploadFailed };
    } catch {
      return { ok: false, error: t.uploadFailed };
    }
  }

  // One file after the other, in the order of the list (§2.1.1 item 5).
  async function send() {
    if (sending) return;
    setSending(true);
    let anySent = rows.some((r) => r.state === "sent");
    for (const row of rows.filter((r) => r.state !== "sent")) {
      update(row.key, { state: "sending", error: undefined });
      const result = await sendOne(row.file);
      if ("auth" in result) {
        update(row.key, { state: "waiting" });
        return; // the button stays disabled while apiFetch leaves for the login page
      }
      if (result.ok) {
        update(row.key, { state: "sent" });
        anySent = true;
      } else {
        update(row.key, { state: "failed", error: result.error });
      }
    }
    setSending(false);
    if (anySent && visible.current) {
      setRound((n) => n + 1);
      setPhase({ kind: "kinds" });
    }
  }

  async function confirm(chosen: Material[]) {
    if (confirming) return;
    setConfirming(true);
    setConfirmFailed(false);
    try {
      const res = await apiFetch(`/exam-preps/${prepId}/materials/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ materials: chosen.map((m) => ({ id: m.id, kind: m.kind })) }),
      });
      if (res.status === 401) return; // stays disabled until the login page loads
      setConfirming(false);
      if (res.ok) {
        if (visible.current) navigate(`/preps/${prepId}/progress`);
        return;
      }
      // A file changed meanwhile: read the list again, no message (§2.1.2 item 5).
      if (res.status === 409 && (await errorCode(res)) === "not_classified") setRound((n) => n + 1);
      else setConfirmFailed(true);
    } catch {
      setConfirming(false);
      setConfirmFailed(true);
    }
  }

  function startOver() {
    setRows([]);
    setMaterials([]);
    setPhase({ kind: "files" });
  }

  if (phase.kind === "loading") return <p className="p-8 text-sm text-zinc-600">{t.loading}</p>;
  if (phase.kind === "notFound") {
    return (
      <div className="p-8 text-sm">
        <p className="mb-2">{t.notFound}</p>
        <Link href="/" className="underline">
          {t.backHome}
        </Link>
      </div>
    );
  }
  if (phase.kind === "failed") {
    return (
      <div className="p-8 text-sm">
        <p className="mb-2">{t.loadFailed}</p>
        <button
          type="button"
          onClick={() => (setPhase({ kind: "loading" }), setAttempt((n) => n + 1))}
          className="underline"
        >
          {t.retry}
        </button>
      </div>
    );
  }

  const failedUploads = rows.filter((r) => r.state === "failed");

  if (phase.kind === "kinds") {
    const open = materials.filter((m) => !m.kind_confirmed);
    const classified = open.filter((m) => m.status === "classified");
    const stillLooking = open.some(waiting);
    const noneReadable = !stillLooking && classified.length === 0;
    return (
      <main className="mx-auto flex w-full max-w-2xl flex-col gap-4 p-8">
        <div>
          <h1 className="text-lg font-semibold">{t.kindsTitle}</h1>
          <p className="text-sm text-zinc-500">{t.kindsSubtitle}</p>
        </div>
        <ul className="flex flex-col gap-2">
          {open.map((m) => (
            <li key={m.id} data-material-id={m.id} className="rounded-lg border border-zinc-200 px-4 py-3 text-sm">
              <p className="font-medium">{m.file_name}</p>
              {m.status === "uploaded" && <p className="text-zinc-500">{t.classifying}</p>}
              {m.status === "classified" && m.kind && (
                <p className="text-zinc-700">
                  <span>{t.kind[m.kind]}</span>
                  {m.kind_confidence !== null && (
                    <span className="ml-2 text-xs text-zinc-500">{t.sure(Math.round(m.kind_confidence * 100))}</span>
                  )}
                </p>
              )}
              {m.status === "failed" && <p className="text-red-700">{m.error ?? t.unreadable}</p>}
            </li>
          ))}
          {failedUploads.map((r) => (
            <li key={`upload-${r.key}`} className="rounded-lg border border-zinc-200 px-4 py-3 text-sm">
              <p className="font-medium">{r.file.name}</p>
              <p className="text-red-700">{r.error}</p>
            </li>
          ))}
        </ul>
        {noneReadable ? (
          <div className="flex flex-col items-start gap-2 text-sm">
            <p>{t.noneReadable}</p>
            <button type="button" onClick={startOver} className="underline">
              {t.startOver}
            </button>
          </div>
        ) : (
          <div>
            <button
              type="button"
              disabled={stillLooking || classified.length === 0 || confirming}
              onClick={() => confirm(classified)}
              className="rounded-lg bg-zinc-900 px-4 py-2 text-sm text-white disabled:opacity-40"
            >
              {t.confirm}
            </button>
            {confirmFailed && (
              <p role="alert" className="mt-1 text-xs text-red-700">
                {t.confirmFailed}
              </p>
            )}
          </div>
        )}
      </main>
    );
  }

  return (
    <main className="mx-auto flex w-full max-w-2xl flex-col gap-4 p-8">
      <div>
        <h1 className="text-lg font-semibold">{t.uploadTitle}</h1>
        <p className="text-sm text-zinc-500">{t.uploadSubtitle}</p>
      </div>
      <label className="flex flex-col gap-1 text-sm text-zinc-700">
        {t.choose}
        <input
          type="file"
          multiple
          accept={ACCEPT}
          disabled={sending}
          onChange={(e) => {
            choose(e.target.files);
            e.target.value = ""; // the same file can be chosen again
          }}
          className="text-sm"
        />
      </label>
      <ul className="flex flex-col gap-2">
        {rows.map((r) => (
          <li
            key={r.key}
            data-file-row
            className="flex items-center justify-between gap-3 rounded-lg border border-zinc-200 px-4 py-2 text-sm"
          >
            <span className="min-w-0">
              <span className="font-medium">{r.file.name}</span>
              <span className="ml-2 text-xs text-zinc-500">{size(r.file.size)}</span>
              {r.state === "sending" && <span className="ml-2 text-xs text-zinc-500">{t.uploading}</span>}
              {r.state === "sent" && <span className="ml-2 text-xs text-zinc-500">{t.uploaded}</span>}
              {r.state === "failed" && <span className="ml-2 text-xs text-red-700">{r.error}</span>}
            </span>
            {r.state !== "sent" && (
              <button
                type="button"
                disabled={sending}
                onClick={() => setRows((prev) => prev.filter((x) => x.key !== r.key))}
                className="text-xs underline disabled:opacity-40"
              >
                {t.remove}
              </button>
            )}
          </li>
        ))}
      </ul>
      <div className="flex items-center gap-4">
        <button
          type="button"
          disabled={sending || !rows.some((r) => r.state !== "sent")}
          onClick={send}
          className="rounded-lg bg-zinc-900 px-4 py-2 text-sm text-white disabled:opacity-40"
        >
          {t.send}
        </button>
        <Link href="/" className="text-sm text-zinc-600 underline">
          {t.back}
        </Link>
      </div>
    </main>
  );
}
