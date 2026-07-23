import { NavLink } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import {
  LayoutDashboard, Server, Filter, Search, FileWarning, LogOut, Shield,
} from "lucide-react";
import clsx from "clsx";
import ZainLogo from "./ZainLogo";

const NAV = [
  { to: "/dashboard", label: "Overview",       icon: LayoutDashboard },
  { to: "/sources",   label: "Sources",        icon: Server },
  { to: "/filters",   label: "Filter Rules",   icon: Filter },
  { to: "/logs",      label: "Log Search",     icon: Search },
  { to: "/audit",     label: "Audit",          icon: FileWarning },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950">
      {/* Sidebar */}
      <aside className="flex flex-col w-56 flex-shrink-0 border-r border-slate-800 bg-slate-900/50">
        {/* Logo */}
        <div className="flex flex-col items-start px-4 py-4 border-b border-slate-800 gap-1">
          <ZainLogo className="h-9 w-auto" />
          <span className="text-[10px] text-slate-500 uppercase tracking-widest pl-0.5">
            LogStream
          </span>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                clsx(
                  "flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                  isActive
                    ? "bg-brand-600/20 text-brand-400 border border-brand-700/50"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
                )
              }
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* User footer */}
        <div className="px-4 py-4 border-t border-slate-800">
          <div className="flex items-center gap-2 mb-3">
            <div className="flex items-center justify-center w-7 h-7 bg-slate-700 rounded-full">
              <Shield className="w-3.5 h-3.5 text-slate-300" />
            </div>
            <div className="min-w-0">
              <p className="text-xs font-medium text-slate-200 truncate">{user?.username}</p>
              <p className="text-[10px] text-slate-500 capitalize">{user?.role}</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="flex items-center gap-2 text-xs text-slate-500 hover:text-red-400 transition-colors w-full"
          >
            <LogOut className="w-3.5 h-3.5" />
            Sign out
          </button>
          <p className="text-[9px] text-slate-700 mt-3 leading-tight">
            Developed by Eng. Yacoub Smadi
          </p>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  );
}
