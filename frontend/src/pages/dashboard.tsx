import { useEffect, useState } from "react";
import { Activity, ArrowUpRight, BriefcaseBusiness, GraduationCap, ListTodo, Percent, UsersRound } from "lucide-react";
import { Bar, BarChart, CartesianGrid, Cell, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Card, CardContent, CardHeader } from "../components/ui/card";
import { EmptyState, ErrorState } from "../components/ui/state";
import { api, ApiError } from "../services/api";
import type { AcademicAnalytics, Overview } from "../types/api";

const chartColors = ["#53d6c6", "#9b83ec", "#e7a45a", "#6aaee8", "#e8799e", "#a8c263"];

function Metric({ label, value, icon: Icon, note, tone = "teal" }: { label: string; value: string; icon: typeof UsersRound; note: string; tone?: "teal" | "violet" | "amber" | "blue" }) {
  return <article className="metric-card"><div className="metric-top"><span>{label}</span><span className={`metric-icon tone-${tone}`}><Icon className="size-4" /></span></div><div className="metric-value">{value}</div><div className="metric-note">{note}</div></article>;
}

function ChartPanel({ title, detail, children }: { title: string; detail: string; children: React.ReactNode }) {
  return <Card className="chart-card"><CardHeader className="chart-header"><div><h2>{title}</h2><p>{detail}</p></div><ArrowUpRight className="size-4 text-muted" /></CardHeader><CardContent className="chart-body">{children}</CardContent></Card>;
}

export function DashboardPage() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [analytics, setAnalytics] = useState<AcademicAnalytics | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const [summary, academic] = await Promise.all([api.overview(), api.academicAnalytics().catch(() => null)]);
      setOverview(summary);
      setAnalytics(academic);
    } catch (reason) {
      setError(reason instanceof ApiError && reason.status === 401 ? "Your session expired. Sign in again." : reason instanceof Error ? reason.message : "Dashboard data could not be loaded.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void load(); }, []);

  if (loading) return <div className="space-y-4"><div className="page-heading"><div><div className="eyebrow">INSTITUTION OVERVIEW</div><h1>Dashboard</h1></div></div><div className="metric-grid">{[0, 1, 2, 3].map((value) => <div className="skeleton" key={value} />)}</div><div className="chart-grid"><div className="skeleton" /><div className="skeleton" /></div></div>;
  if (error || !overview) return <ErrorState message={error || "Dashboard data unavailable."} onRetry={() => void load()} />;

  const percent = (value: number | null) => value === null ? "—" : `${value.toFixed(1)}%`;
  const restricted = overview.total_students === null;
  const trend = analytics?.performance_trends ?? [];
  const subjectData = analytics?.subject_averages ?? [];
  const gradeData = analytics?.grade_distribution.filter((item) => item.count > 0) ?? [];

  return <div>
    <div className="page-heading"><div><p className="eyebrow">INSTITUTION OVERVIEW</p><h1>Dashboard</h1><p>Live summaries calculated from records in the database.</p></div></div>
    <section className="metric-grid" aria-label="Performance summary">
      <Metric label="Active students" value={restricted ? "Restricted" : String(overview.total_students)} icon={GraduationCap} note="Non-archived profiles" tone="teal" />
      <Metric label="Active employees" value={restricted ? "Restricted" : String(overview.total_employees)} icon={BriefcaseBusiness} note="Active staff profiles" tone="violet" />
      <Metric label="Average marks" value={percent(overview.average_marks_percentage)} icon={Percent} note="Entered marks only" tone="blue" />
      <Metric label="Pass percentage" value={percent(overview.pass_percentage)} icon={Activity} note="Configured exam pass marks" tone="amber" />
    </section>
    <section className="chart-grid" aria-label="Academic analytics">
      <ChartPanel title="Academic trend" detail="Average entered-mark percentage by exam period">
        {trend.length ? <ResponsiveContainer width="100%" height="100%"><LineChart data={trend} margin={{ top: 10, right: 18, bottom: 0, left: -18 }}><CartesianGrid stroke="var(--border)" strokeDasharray="3 5" vertical={false} /><XAxis dataKey="semester" tick={{ fill: "var(--text-muted)", fontSize: 10 }} axisLine={false} tickLine={false} /><YAxis domain={[0, 100]} tick={{ fill: "var(--text-muted)", fontSize: 10 }} axisLine={false} tickLine={false} /><Tooltip contentStyle={{ background: "var(--surface-raised)", border: "1px solid var(--border)", borderRadius: 6, color: "var(--text)", fontSize: 11 }} /><Line type="monotone" dataKey="average_percentage" name="Average" stroke="#53d6c6" strokeWidth={2.5} dot={{ r: 3, fill: "#53d6c6" }} activeDot={{ r: 5 }} /></LineChart></ResponsiveContainer> : <div className="chart-empty">{analytics ? "No entered exam results yet." : "Analytics unavailable for this role."}</div>}
      </ChartPanel>
      <ChartPanel title="Subject averages" detail="Percent of configured maximum marks">
        {subjectData.length ? <ResponsiveContainer width="100%" height="100%"><BarChart data={subjectData} margin={{ top: 10, right: 8, bottom: 0, left: -18 }}><CartesianGrid stroke="var(--border)" strokeDasharray="3 5" vertical={false} /><XAxis dataKey="subject_code" tick={{ fill: "var(--text-muted)", fontSize: 10 }} axisLine={false} tickLine={false} /><YAxis domain={[0, 100]} tick={{ fill: "var(--text-muted)", fontSize: 10 }} axisLine={false} tickLine={false} /><Tooltip contentStyle={{ background: "var(--surface-raised)", border: "1px solid var(--border)", borderRadius: 6, color: "var(--text)", fontSize: 11 }} /><Bar dataKey="average_percentage" name="Average %" radius={[4, 4, 0, 0]}>{subjectData.map((entry, index) => <Cell key={entry.subject_code} fill={chartColors[index % chartColors.length]} />)}</Bar></BarChart></ResponsiveContainer> : <div className="chart-empty">No subject results to chart.</div>}
      </ChartPanel>
    </section>
    <section className="dashboard-bottom">
      <ChartPanel title="Grade distribution" detail="Based on configured percentage thresholds">
        {gradeData.length ? <ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={gradeData} dataKey="count" nameKey="grade" cx="50%" cy="50%" innerRadius={56} outerRadius={88} paddingAngle={3}>{gradeData.map((item, index) => <Cell key={item.grade} fill={chartColors[index % chartColors.length]} />)}</Pie><Tooltip contentStyle={{ background: "var(--surface-raised)", border: "1px solid var(--border)", borderRadius: 6, color: "var(--text)", fontSize: 11 }} /></PieChart></ResponsiveContainer> : <div className="chart-empty">No entered marks yet.</div>}
      </ChartPanel>
      <Card className="chart-card"><CardHeader className="chart-header"><div><h2>Operations</h2><p>Current live workload</p></div><ListTodo className="size-4 text-muted" /></CardHeader><CardContent><div className="operation-row"><span>Pending employee tasks</span><strong>{overview.pending_tasks}</strong></div><div className="operation-row"><span>Attendance rate</span><strong>{percent(overview.attendance_percentage)}</strong></div><div className="operation-row"><span>Entered marks analyzed</span><strong>{analytics?.entered_mark_count ?? 0}</strong></div><div className="operation-row"><span>Pending / absent marks excluded</span><strong>{analytics?.excluded_pending_or_absent ?? 0}</strong></div>{!analytics && <EmptyState title="Analytics restricted" detail="Your role cannot view academic summaries." />}</CardContent></Card>
    </section>
  </div>;
}