import { redirect } from "next/navigation";

export default function Home() {
  // Root page redirects to agents (which is in protected folder)
  redirect("/agents");
}
