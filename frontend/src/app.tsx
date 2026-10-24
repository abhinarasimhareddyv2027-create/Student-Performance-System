import { lazy, Suspense, useEffect } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import type { ReactNode } from "react";
import { Toaster } from "sonner";
import { AppShell } from "./components/app-shell";
import { useAuth } from "./services/auth";
import { LoadingState } from "./components/ui/state";

const LoginPage = lazy(() => import("./pages/login").then((module) => ({ default: module.LoginPage })));
const DashboardPage = lazy(() => import("./pages/dashboard").then((module) => ({ default: module.DashboardPage })));
const ProfilesPage = lazy(() => import("./pages/profiles").then((module) => ({ default: module.ProfilesPage })));
const ModulePage = lazy(() => import("./pages/module").then((module) => ({ default: module.ModulePage })));

function ProtectedApp() {
  const { user, loading } = useAuth();
  if (loading) return <LoadingState label="Checking your session" />;
  if (!user) return <Navigate to="/login" replace />;
  return <AppShell />;
}

function RoleGate({ roles, children }: { roles: string[]; children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <LoadingState label="Checking your access" />;
  if (!user) return <Navigate to="/login" replace />;
  return roles.includes(user.role) ? children : <Navigate to="/" replace />;
}

export function App() {
  const { user } = useAuth();
  useEffect(() => {
    document.documentElement.classList.add("dark");
  }, []);

  return (
    <>
    <Toaster position="top-right" richColors theme="system" />
    <Suspense fallback={<LoadingState label="Opening workspace" />}><Routes>
      <Route path="/login" element={user ? <Navigate to="/" replace /> : <LoginPage />} />
      <Route element={<ProtectedApp />}>
        <Route index element={<DashboardPage />} />
        <Route path="students" element={<RoleGate roles={["admin", "teacher"]}><ProfilesPage kind="students" /></RoleGate>} />
        <Route path="employees" element={<RoleGate roles={["admin", "employee"]}><ProfilesPage kind="employees" /></RoleGate>} />
        <Route path="settings" element={<RoleGate roles={["admin", "teacher", "employee"]}><ModulePage kind="settings" /></RoleGate>} />
        <Route path="academics" element={<RoleGate roles={["admin", "teacher"]}><ModulePage kind="academics" /></RoleGate>} />
        <Route path="attendance" element={<RoleGate roles={["admin", "teacher", "employee"]}><ModulePage kind="attendance" /></RoleGate>} />
        <Route path="leaves" element={<RoleGate roles={["admin", "teacher", "employee"]}><ModulePage kind="leaves" /></RoleGate>} />
        <Route path="activities" element={<RoleGate roles={["admin", "teacher"]}><ModulePage kind="activities" /></RoleGate>} />
        <Route path="tasks" element={<RoleGate roles={["admin", "teacher", "employee"]}><ModulePage kind="tasks" /></RoleGate>} />
        <Route path="analytics" element={<RoleGate roles={["admin", "teacher", "employee"]}><ModulePage kind="analytics" /></RoleGate>} />
        <Route path="reports" element={<RoleGate roles={["admin", "teacher"]}><ModulePage kind="reports" /></RoleGate>} />
        <Route path="users" element={<RoleGate roles={["admin"]}><ModulePage kind="users" /></RoleGate>} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes></Suspense>
    </>
  );
}