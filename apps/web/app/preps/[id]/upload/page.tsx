import { Suspense } from "react";
import { UploadRoute } from "@/components/materials/MaterialRoutes";
import { materialStrings as t } from "@/components/materials/strings";

type Params = Promise<{ id: string }>;

// The files load from the API in the browser (spec: specs/features/exam-prep/upload-page.md §2.1).
// params are request data, so they are read inside Suspense (Next.js prerendering), like the room page.
export default function UploadPageRoute({ params }: { params: Params }) {
  return (
    <Suspense fallback={<p className="p-8 text-sm text-zinc-600">{t.loading}</p>}>
      <Upload params={params} />
    </Suspense>
  );
}

async function Upload({ params }: { params: Params }) {
  const { id } = await params;
  return <UploadRoute prepId={id} />;
}
