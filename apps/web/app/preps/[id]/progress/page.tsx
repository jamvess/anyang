import { Suspense } from "react";
import { ProgressRoute } from "@/components/materials/MaterialRoutes";
import { materialStrings as t } from "@/components/materials/strings";

type Params = Promise<{ id: string }>;

// The reading progress loads from the API in the browser (spec: specs/features/exam-prep/upload-page.md §2.2).
// params are request data, so they are read inside Suspense (Next.js prerendering), like the room page.
export default function ProgressPageRoute({ params }: { params: Params }) {
  return (
    <Suspense fallback={<p className="p-8 text-sm text-zinc-600">{t.loading}</p>}>
      <Progress params={params} />
    </Suspense>
  );
}

async function Progress({ params }: { params: Params }) {
  const { id } = await params;
  return <ProgressRoute prepId={id} />;
}
