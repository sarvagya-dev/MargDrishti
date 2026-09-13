import { Link } from "@tanstack/react-router";

const linkBase =
  "px-3 py-1.5 text-sm font-medium text-slate-600 rounded-md hover:bg-slate-100 hover:text-navy transition-colors";

export default function TopNav() {
  return (
    <header className="sticky top-0 z-[1000] border-b border-slate-200 bg-white">
      <div className="mx-auto flex h-14 max-w-[1600px] items-center justify-between px-5">
        <Link to="/authority" className="flex items-center gap-2">
          <span className="text-lg font-bold tracking-tight text-navy">MargDrishti</span>
          <span className="hidden text-xs text-slate-500 sm:inline">
            Road Risk Intelligence
          </span>
        </Link>
        <nav className="flex items-center gap-1">
          <Link
            to="/authority"
            className={linkBase}
            activeOptions={{ exact: true }}
            activeProps={{ className: "bg-slate-100 text-navy" }}
          >
            Overview
          </Link>
          <Link
            to="/authority/cases"
            className={linkBase}
            activeProps={{ className: "bg-slate-100 text-navy" }}
          >
            Cases
          </Link>
          <Link
            to="/driver"
            className={linkBase}
            activeProps={{ className: "bg-slate-100 text-navy" }}
          >
            Driver View
          </Link>
        </nav>
      </div>
    </header>
  );
}
