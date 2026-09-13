import { createFileRoute, Outlet } from "@tanstack/react-router";
// @ts-expect-error - JS component
import TopNav from "@/components/TopNav";

export const Route = createFileRoute("/authority")({
  component: AuthorityLayout,
});

function AuthorityLayout() {
  return (
    <div className="min-h-screen bg-slate-50">
      <TopNav />
      <Outlet />
    </div>
  );
}
