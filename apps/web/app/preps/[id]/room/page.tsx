import { Suspense } from "react";
import { roomStrings as t } from "@/components/chat/strings";
import { TutorRoom } from "@/components/chat/TutorRoom";

type Params = Promise<{ id: string }>;

// The room loads from the API in the browser (spec: specs/features/tutor/room-http.md).
// params are request data, so they are read inside Suspense (Next.js prerendering).
export default function RoomPage({ params }: { params: Params }) {
  return (
    <Suspense fallback={<p className="p-8 text-sm text-zinc-600">{t.loading}</p>}>
      <Room params={params} />
    </Suspense>
  );
}

async function Room({ params }: { params: Params }) {
  const { id } = await params;
  return <TutorRoom prepId={id} />;
}
