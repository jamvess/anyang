import { Suspense } from "react";
import { SignupRoute } from "@/components/auth/AuthRoutes";
import { authStrings as t } from "@/components/auth/strings";

type SearchParams = Promise<{ [key: string]: string | string[] | undefined }>;

// Email + password sign-up (spec: specs/features/platform/web-signup.md §2.1). searchParams are
// request data, so they are read inside Suspense (Next.js prerendering), like the login page.
export default function SignupPage({ searchParams }: { searchParams: SearchParams }) {
  return (
    <Suspense fallback={<p className="p-8 text-sm text-zinc-600">{t.loading}</p>}>
      <Signup searchParams={searchParams} />
    </Suspense>
  );
}

async function Signup({ searchParams }: { searchParams: SearchParams }) {
  const { next } = await searchParams;
  return <SignupRoute next={typeof next === "string" ? next : undefined} />;
}
