import { PrepList } from "@/components/preps/PrepList";

// Home: the user's exam preps, read from the API in the browser
// (spec: specs/features/exam-prep/prep-list-page.md §2.1 · S07, S27).
export default function Home() {
  return <PrepList />;
}
