import { useState } from "react";
import {
  Activity, BarChart3, BookOpenCheck, BriefcaseBusiness, CalendarCheck2,
  ChevronLeft, ClipboardList, FileBarChart2, GraduationCap, LayoutDashboard,
  LogOut, Menu, Settings2, ShieldCheck, Users, UserRound, X,
} from "lucide-react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../services/auth";
import { Button } from "./ui/button";
import { ThemeToggle } from "./theme-toggle";

const navigation = [
  { label: "Dashboard", path: "/", icon: LayoutDashboard, roles: ["admin", "teacher", "employee"] },
  { label: "Students", path: "/students", icon: GraduationCap, roles: ["admin", "teacher"] },
  { label: "Employees", path: "/employees", icon: BriefcaseBusiness, roles: ["admin"] },
  { label: "Academics", path: "/academics", icon: BookOpenCheck, roles: ["admin", "teacher"] },
  { label: "Attendance", path: "/attendance", icon: CalendarCheck2, roles: ["admin", "teacher", "employee"] },
  { label: "Leave", path: "/leaves", icon: ClipboardList, roles: ["admin", "teacher", "employee"] },
  { label: "Activities", path: "/activities", icon: Activity, roles: ["admin", "teacher"] },
  { label: "Tasks & reviews", path: "/tasks", icon: ClipboardList, roles: ["admin", "teacher", "employee"] },
  { label: "Analytics", path: "/analytics", icon: BarChart3, roles: ["admin", "teacher", "employee"] },
  { label: "Reports", path: "/reports", icon: FileBarChart2, roles: ["admin", "teacher"] },
  { label: "Users & roles", path: "/users", icon: ShieldCheck, roles: ["admin"] },
  { label: "Settings", path: "/settings", icon: Settings2, roles: ["admin", "teacher", "employee"] },
];

export function AppShell() {
  const { user, signOut } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const current = navigation.find((item) => item.path === location.pathname);
  const items = navigation.filter((item) => user && item.roles.includes(user.role));

  const logout = async () => {
    await signOut();
    navigate("/login", { replace: true });
  };

  return (
    <div className="app-frame">
      {mobileOpen && <button aria-label="Close navigation" className="mobile-scrim" onClick={() => setMobileOpen(false)} />}
      <aside className={`sidebar ${collapsed ? "sidebar-collapsed" : ""} ${mobileOpen ? "sidebar-mobile-open" : ""}`}>
        <div className="brand-row">
          <div className="brand-mark"><span>SP</span></div>
          {!collapsed && <div className="brand-copy"><strong>Northstar</strong><span>Performance office</span></div>}
          <Button className="sidebar-collapse" variant="ghost" size="icon" aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"} onClick={() => setCollapsed(!collapsed)}>
            <ChevronLeft className={`size-4 transition-transform ${collapsed ? "rotate-180" : ""}`} />
          </Button>
          <Button className="sidebar-close" variant="ghost" size="icon" aria-label="Close navigation" onClick={() => setMobileOpen(false)}><X className="size-4" /></Button>
        </div>
        <div className="nav-caption">WORKSPACE</div>
        <nav className="nav-list" aria-label="Main navigation">
          {items.map(({ label, path, icon: Icon }) => (
            <NavLink key={path} to={path} end={path === "/"} title={collapsed ? label : undefined} onClick={() => setMobileOpen(false)} className={({ isActive }) => `nav-item ${isActive ? "nav-item-active" : ""}`}>
              <Icon className="size-[18px] shrink-0" strokeWidth={1.8} />
              {!collapsed && <span>{label}</span>}
              {!collapsed && path === "/students" && <span className="nav-count">01</span>}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-note"><div className="note-orbit" /><div><strong>Academic year</strong><span>2026 / 2027</span></div></div>
          <button className="profile-mini" onClick={() => navigate("/settings")}>
            <span className="avatar">{user?.username.slice(0, 1).toUpperCase()}</span>
            {!collapsed && <span className="profile-copy"><strong>{user?.username}</strong><small>{user?.role}</small></span>}
            {!collapsed && <Users className="ml-auto size-4 text-muted" />}
          </button>
        </div>
      </aside>

      <main className="main-column">
        <header className="topbar">
          <div className="topbar-left">
            <Button className="mobile-menu" variant="ghost" size="icon" aria-label="Open navigation" onClick={() => setMobileOpen(true)}><Menu className="size-5" /></Button>
            <div className="breadcrumbs"><span>Workspace</span><span className="crumb-slash">/</span><strong>{current?.label || "Dashboard"}</strong></div>
          </div>
          <div className="topbar-actions">
            <span className="live-status"><i /> Live database</span>
            <ThemeToggle />
            <span className="topbar-divider" />
            <span className="topbar-user"><UserRound className="size-4" />{user?.username}</span>
            <Button variant="ghost" size="icon" aria-label="Sign out" title="Sign out" onClick={logout}><LogOut className="size-4" /></Button>
          </div>
        </header>
        <div className="page-viewport"><Outlet /></div>
      </main>
    </div>
  );
}