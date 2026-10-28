import { Suspense } from "react";
import { ScopeReviewRoute } from "@/components/scope/ScopeReviewRoute";
import { scopeStrings as t } from "@/components/scope/strings";

type Params = Promise<{ id: string }>;

// The scope loads from the API in the browser (spec: specs/features/scope/scope-review.md).
// params are request data, so they are read inside Suspense (Next.js prerendering), like the room page.
export default function ScopePage({ params }: { params: Params }) {
  return (
    <Suspense fallback={<p className="p-8 text-sm text-zinc-600">{t.loading}</p>}>
      <Scope params={params} />
    </Suspense>
  );
}

async function Scope({ params }: { params: Params }) {
  const { id } = await params;
  return <ScopeReviewRoute prepId={id} />;
}
