import { Suspense } from "react";
import { LoginRoute } from "@/components/auth/AuthRoutes";
import { authStrings as t } from "@/components/auth/strings";

type SearchParams = Promise<{ [key: string]: string | string[] | undefined }>;

// Email + password sign-in (spec: specs/features/platform/web-login.md §2.1). searchParams are
// request data, so they are read inside Suspense (Next.js prerendering), like the room page.
export default function LoginPage({ searchParams }: { searchParams: SearchParams }) {
  return (
    <Suspense fallback={<p className="p-8 text-sm text-zinc-600">{t.loading}</p>}>
      <Login searchParams={searchParams} />
    </Suspense>
  );
}

async function Login({ searchParams }: { searchParams: SearchParams }) {
  const { next } = await searchParams;
  return <LoginRoute next={typeof next === "string" ? next : undefined} />;
}
