import { createBrowserClient } from "@supabase/ssr";

/**
 * Supabase client for Client Components (auth session lives in cookies).
 * Env is read here, not at module load, so `next build` works without it.
 */
export function createClient() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !anonKey) {
    throw new Error(
      "NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY must be set",
    );
  }
  return createBrowserClient(url, anonKey);
}
