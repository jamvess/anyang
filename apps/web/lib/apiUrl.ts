/**
 * Base URL of the API. Read per call, not at module load, so `next build`
 * works without the env (same as lib/supabase.ts).
 */
export function apiUrl(path: string): string {
  const base = process.env.NEXT_PUBLIC_API_URL;
  if (!base) throw new Error("NEXT_PUBLIC_API_URL must be set");
  return `${base.replace(/\/$/, "")}${path}`;
}
