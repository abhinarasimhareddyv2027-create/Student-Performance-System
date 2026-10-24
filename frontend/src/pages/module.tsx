import { useEffect, useState, type FormEvent } from "react";
import { Check, Download, Plus, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader } from "../components/ui/card";
import { Dialog } from "../components/ui/dialog";
import { Input } from "../components/ui/input";
import { EmptyState, ErrorState, LoadingState } from "../components/ui/state";
import { useAuth } from "../services/auth";
import { api, ApiError } from "../services/api";
import type { Employee, Mark, StudentAttendance, EmployeeAttendance, Task } from "../types/api";

type ModuleKind = "academics" | "attendance" | "leaves" | "activities" | "tasks" | "analytics" | "reports" | "users" | "settings";
type Row = Record<string, unknown>;
interface Section { title: string; description?: string; rows: Row[] }
interface FieldSpec { name: string; label: string; type?: string; required?: boolean; options?: string[] }
interface FormAction { title: string; fields: FieldSpec[]; submit: (values: Record<string, string>) => Promise<unknown> }

const names: Record<ModuleKind, { title: string; eyebrow: string; description: string }> = {
  academics: { title: "Academics", eyebrow: "ACADEMIC RECORDS", description: "Departments, courses, subjects, examinations, and marks." },
  attendance: { title: "Attendance", eyebrow: "PRESENCE & PARTICIPATION", description: "Student and employee attendance recorded by date and session." },
  leaves: { title: "Leave management", eyebrow: "REQUESTS & APPROVALS", description: "Review leave requests without conflating leave with absence." },
  activities: { title: "Student activities", eyebrow: "PARTICIPATION & ACHIEVEMENTS", description: "Record activities against real student profiles." },
  tasks: { title: "Tasks & reviews", eyebrow: "EMPLOYEE WORK & FEEDBACK", description: "Track assigned tasks and documented review criteria." },
  analytics: { title: "Performance analytics", eyebrow: "MEASURED PERFORMANCE", description: "Calculated from stored marks, attendance, tasks, and reviews." },
  reports: { title: "Reports", eyebrow: "EXPORTS", description: "Download CSV reports generated from current database records." },
  users: { title: "Users & roles", eyebrow: "ACCESS CONTROL", description: "Create staff accounts and disable access when required." },
  settings: { title: "Settings & profile", eyebrow: "ACCOUNT & SYSTEM", description: "Review your session and check backend connectivity." },
};

export function ModulePage({ kind }: { kind: ModuleKind }) {
  const { user } = useAuth();
  const [sections, setSections] = useState<Section[]>([]);
  const [actions, setActions] = useState<FormAction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeAction, setActiveAction] = useState<FormAction | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const page = names[kind];

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const result = await loadModule(kind, user?.role);
      setSections(result.sections);
      setActions(result.actions);
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : "Could not load this module.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void load(); }, [kind, user?.role]);

  const refresh = async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  };

  const exportCsv = async (type: "students" | "employees") => {
    try { await api.downloadCsv(type); toast.success(`${type} report downloaded.`); }
    catch (reason) { toast.error(reason instanceof Error ? reason.message : "Export failed."); }
  };

  return <div>
    <div className="page-heading"><div><p className="eyebrow">{page.eyebrow}</p><h1>{page.title}</h1><p>{page.description}</p></div><div className="page-actions">
      {kind === "reports" && <><Button variant="secondary" onClick={() => void exportCsv("students")}><Download className="size-4" />Students CSV</Button>{user?.role === "admin" && <Button variant="secondary" onClick={() => void exportCsv("employees")}><Download className="size-4" />Employees CSV</Button>}</>}
      {actions.length > 0 && <select className="select-control" aria-label="Choose record type" onChange={(event) => { const action = actions.find((item) => item.title === event.target.value); if (action) setActiveAction(action); event.target.value = ""; }} value=""><option value="" disabled><Plus className="inline size-3" /> Add record</option>{actions.map((action) => <option key={action.title} value={action.title}>{action.title}</option>)}</select>}
      <Button variant="ghost" size="icon" aria-label="Refresh module" title="Refresh" onClick={() => void refresh()} disabled={refreshing}><RefreshCw className={`size-4 ${refreshing ? "animate-spin" : ""}`} /></Button>
    </div></div>
    {loading ? <LoadingState label={`Loading ${page.title.toLowerCase()}`} /> : error ? <ErrorState message={error} onRetry={() => void load()} /> : sections.length === 0 ? <EmptyState title="No data available" detail="This module has no records yet, or your role has limited access." /> : <div className="module-sections">{sections.map((section) => <ResourceSection key={section.title} section={section} kind={kind} onRefresh={load} role={user?.role} />)}</div>}
    <FormDialog action={activeAction} onClose={() => setActiveAction(null)} onSaved={load} />
  </div>;
}

async function loadModule(kind: ModuleKind, role?: string): Promise<{ sections: Section[]; actions: FormAction[] }> {
  if (kind === "academics") {
    const [departments, courses, subjects, exams, marks] = await Promise.all([api.departments(), api.courses(), api.subjects(), api.exams(), api.marks()]);
    const actions: FormAction[] = role === "admin" ? [
      { title: "Add department", fields: [{ name: "code", label: "Department code", required: true }, { name: "name", label: "Department name", required: true }], submit: (v) => api.createDepartment({ code: v.code, name: v.name }) },
      { title: "Add course", fields: [{ name: "department_id", label: "Department ID", type: "number", required: true }, { name: "code", label: "Course code", required: true }, { name: "name", label: "Course name", required: true }], submit: (v) => api.createCourse({ department_id: Number(v.department_id), code: v.code, name: v.name }) },
      { title: "Add subject", fields: [{ name: "course_id", label: "Course ID", type: "number", required: true }, { name: "code", label: "Subject code", required: true }, { name: "name", label: "Subject name", required: true }], submit: (v) => api.createSubject({ course_id: Number(v.course_id), code: v.code, name: v.name }) },
      { title: "Add examination", fields: [{ name: "subject_id", label: "Subject ID", type: "number", required: true }, { name: "name", label: "Exam name", required: true }, { name: "academic_year", label: "Academic year", required: true }, { name: "semester", label: "Semester", required: true }, { name: "maximum_marks", label: "Maximum marks", type: "number", required: true }, { name: "pass_marks", label: "Pass marks", type: "number", required: true }], submit: (v) => api.createExam({ subject_id: Number(v.subject_id), name: v.name, academic_year: v.academic_year, semester: v.semester, exam_date: null, maximum_marks: Number(v.maximum_marks), pass_marks: Number(v.pass_marks) }) },
      ...markActions(),
    ] : role === "teacher" ? markActions() : [];
    return {
      actions,
      sections: [
        { title: "Departments", rows: asRows(departments) },
        { title: "Courses", rows: asRows(courses) },
        { title: "Subjects", rows: asRows(subjects) },
        { title: "Examinations", rows: asRows(exams) },
        { title: "Marks", rows: asRows(marks) },
      ],
    };
  }
  if (kind === "attendance") {
    const studentRequest = role === "admin" || role === "teacher" ? api.studentAttendance() : Promise.resolve([] as StudentAttendance[]);
    const employeeRequest = role === "admin" || role === "employee" ? api.employeeAttendance() : Promise.resolve([] as EmployeeAttendance[]);
    const [studentRows, employeeRows] = await Promise.all([studentRequest, employeeRequest]);
    const actions: FormAction[] = role === "admin" || role === "teacher" ? [{ title: "Record student attendance", fields: [{ name: "student_id", label: "Student ID", type: "number", required: true }, { name: "attendance_date", label: "Date", type: "date", required: true }, { name: "session", label: "Session", required: true }, { name: "status", label: "Status", options: ["present", "absent", "excused"], required: true }], submit: (v) => api.createStudentAttendance({ student_id: Number(v.student_id), attendance_date: v.attendance_date, session: v.session || "day", status: v.status as StudentAttendance["status"], note: null }) }] : [];
    if (role === "admin") actions.push({ title: "Record employee attendance", fields: [{ name: "employee_id", label: "Employee ID", type: "number", required: true }, { name: "attendance_date", label: "Date", type: "date", required: true }, { name: "shift", label: "Shift", required: true }, { name: "status", label: "Status", options: ["present", "absent", "leave"], required: true }], submit: (v) => api.createEmployeeAttendance({ employee_id: Number(v.employee_id), attendance_date: v.attendance_date, shift: v.shift || "day", status: v.status as EmployeeAttendance["status"], check_in: null, check_out: null }) });
    return { actions, sections: [...(role !== "employee" ? [{ title: "Student attendance", rows: asRows(studentRows) }] : []), ...(role === "admin" || role === "employee" ? [{ title: role === "employee" ? "My attendance" : "Employee attendance", rows: asRows(employeeRows) }] : [])] };
  }
  if (kind === "leaves") {
    const rows = await api.leaves();
    return { sections: [{ title: "Leave requests", rows: asRows(rows) }], actions: [{ title: "Request leave", fields: [{ name: "student_id", label: "Student ID (if student leave)", type: "number" }, { name: "employee_id", label: "Employee ID (if employee leave)", type: "number" }, { name: "start_date", label: "Start date", type: "date", required: true }, { name: "end_date", label: "End date", type: "date", required: true }, { name: "reason", label: "Reason", required: true }], submit: (v) => api.createLeave({ student_id: v.student_id ? Number(v.student_id) : null, employee_id: v.employee_id ? Number(v.employee_id) : null, start_date: v.start_date, end_date: v.end_date, reason: v.reason, status: "pending" }) }] };
  }
  if (kind === "activities") {
    const [activities, students] = await Promise.all([api.activities(), api.students()]);
    return { sections: [{ title: "Student activities", rows: asRows(activities) }], actions: [{ title: "Add activity", fields: [{ name: "student_id", label: "Student", type: "select", options: students.map((student) => `${student.id} · ${student.register_number} · ${student.full_name}`), required: true }, { name: "title", label: "Activity title", required: true }, { name: "category", label: "Category", required: true }, { name: "participation_date", label: "Participation date", type: "date", required: true }, { name: "description", label: "Description" }], submit: (v) => api.createActivity({ student_id: Number(v.student_id.split(" · ")[0]), title: v.title, category: v.category, participation_date: v.participation_date, description: v.description || null }) }] };
  }
  if (kind === "tasks") {
    const [tasks, reviews, employees] = await Promise.all([api.tasks(), api.reviews(), role === "admin" || role === "teacher" ? api.employees() : Promise.resolve([] as Employee[])]);
    const actions: FormAction[] = role === "admin" || role === "teacher" ? [
      { title: "Assign task", fields: [{ name: "employee_id", label: "Employee", type: "select", options: employees.map((employee) => `${employee.id} · ${employee.full_name}`), required: true }, { name: "title", label: "Task title", required: true }, { name: "project", label: "Project" }, { name: "assigned_date", label: "Assigned date", type: "date", required: true }, { name: "deadline", label: "Deadline", type: "date" }], submit: (v) => api.createTask({ employee_id: Number(v.employee_id.split(" · ")[0]), title: v.title, description: null, project: v.project || null, assigned_date: v.assigned_date, deadline: v.deadline || null, status: "todo", completion_notes: null }) },
      { title: "Add performance review", fields: [{ name: "employee_id", label: "Employee", type: "select", options: employees.map((employee) => `${employee.id} · ${employee.full_name}`), required: true }, { name: "period_start", label: "Period start", type: "date", required: true }, { name: "period_end", label: "Period end", type: "date", required: true }, { name: "criteria", label: "Job-relevant criteria", required: true }, { name: "score", label: "Score (optional, 0–100)", type: "number" }, { name: "feedback", label: "Manager feedback", required: true }], submit: (v) => api.createReview({ employee_id: Number(v.employee_id.split(" · ")[0]), period_start: v.period_start, period_end: v.period_end, criteria: v.criteria, score: v.score ? Number(v.score) : null, feedback: v.feedback }) },
    ] : [];
    return { sections: [{ title: "Employee tasks", rows: asRows(tasks) }, { title: "Documented performance reviews", rows: asRows(reviews) }], actions };
  }
  if (kind === "analytics") {
    if (role === "employee") {
      const summary = await api.overview();
      const tasks = await api.tasks();
      return { actions: [], sections: [{ title: "My summary", rows: [{ pending_tasks: summary.pending_tasks, assigned_tasks: tasks.length }] }] };
    }
    const [academic, attendance, employee] = await Promise.all([api.academicAnalytics(), api.attendanceAnalytics(), api.employeeAnalytics()]);
    return { actions: [], sections: [
      { title: "Subject averages", description: `${academic.entered_mark_count} entered results; ${academic.excluded_pending_or_absent} pending/absent excluded.`, rows: asRows(academic.subject_averages) },
      { title: "Academic trends", rows: asRows(academic.performance_trends) },
      { title: "Grade distribution", rows: asRows(academic.grade_distribution) },
      { title: "Class summaries", rows: asRows(academic.class_summaries) },
      { title: "Student attendance trend", description: attendance.denominator, rows: asRows(attendance.student_trend) },
      { title: "Employee task completion", description: employee.note, rows: asRows(employee.task_completion) },
      { title: "Performance review summaries", rows: asRows(employee.review_summaries) },
    ] };
  }
  if (kind === "users") {
    const users = await api.users();
    return { sections: [{ title: "Application users", rows: asRows(users) }], actions: [{ title: "Create user", fields: [{ name: "username", label: "Username", required: true }, { name: "password", label: "Temporary password (min 12 chars)", type: "password", required: true }, { name: "role", label: "Role", type: "select", options: ["admin", "teacher", "employee"], required: true }, { name: "employee_id", label: "Employee ID (for employee role)", type: "number" }], submit: (v) => api.createUser({ username: v.username, password: v.password, role: v.role, ...(v.employee_id ? { employee_id: Number(v.employee_id) } : {}) }) }] };
  }
  if (kind === "settings") {
    const [health, current] = await Promise.all([api.health(), api.me()]);
    return { actions: [], sections: [{ title: "Current session", rows: [{ username: current.username, role: current.role, employee_id: current.employee_id ?? "—" }] }, { title: "Backend status", rows: [{ api: health.status, session: "Authenticated cookie" }] }] };
  }
  return { actions: [], sections: [] };
}

function markActions(): FormAction[] {
  return [{ title: "Enter mark", fields: [{ name: "examination_id", label: "Examination ID", type: "number", required: true }, { name: "student_id", label: "Student ID", type: "number", required: true }, { name: "status", label: "Mark status", type: "select", options: ["pending", "absent", "entered"], required: true }, { name: "score", label: "Score (enter zero as 0; leave blank for absent/pending)", type: "number" }], submit: (v) => {
    if (v.status === "entered" && !v.score?.trim()) throw new Error("Enter a numeric score. Use 0 for an actual zero mark.");
    return api.createMark({ examination_id: Number(v.examination_id), student_id: Number(v.student_id), status: v.status as Mark["status"], score: v.status === "entered" ? Number(v.score) : null });
  } }];
}

function asRows<T>(values: T[]): Row[] {
  return values as Row[];
}

function ResourceSection({ section, kind, onRefresh, role }: { section: Section; kind: ModuleKind; onRefresh: () => Promise<void>; role?: string }) {
  const [busyId, setBusyId] = useState<number | null>(null);
  const [taskId, setTaskId] = useState("");
  const [newStatus, setNewStatus] = useState("");
  const columns = section.rows[0] ? Object.keys(section.rows[0]).filter((key) => key !== "id").slice(0, 7) : [];
  const decide = async (id: number, decision: "approved" | "rejected") => {
    setBusyId(id);
    try { await api.decideLeave(id, decision); toast.success(`Request ${decision}.`); await onRefresh(); }
    catch (error) { toast.error(error instanceof Error ? error.message : "Decision failed."); }
    finally { setBusyId(null); }
  };
  const updateTask = async () => {
    if (!taskId || !newStatus) return;
    try { await api.updateTask(Number(taskId), newStatus as Task["status"]); toast.success("Task status updated."); setTaskId(""); setNewStatus(""); await onRefresh(); }
    catch (error) { toast.error(error instanceof Error ? error.message : "Task update failed."); }
  };
  return <Card className="resource-card"><CardHeader className="chart-header"><div><h2>{section.title}</h2>{section.description && <p>{section.description}</p>}</div>
    {kind === "leaves" && role === "admin" && <span className="inline-actions"><Button variant="secondary" size="sm" disabled={busyId !== null} onClick={() => { const item = section.rows.find((row) => row.status === "pending"); if (item?.id) void decide(Number(item.id), "approved"); }}>Approve next</Button><Button variant="ghost" size="sm" disabled={busyId !== null} onClick={() => { const item = section.rows.find((row) => row.status === "pending"); if (item?.id) void decide(Number(item.id), "rejected"); }}>Reject next</Button></span>}
    {kind === "tasks" && section.title === "Employee tasks" && role === "employee" && section.rows.length > 0 && <div className="task-update"><label><span>Task</span><select className="select-control" value={taskId} onChange={(event) => setTaskId(event.target.value)}><option value="">Choose task</option>{section.rows.map((row) => <option key={String(row.id)} value={String(row.id)}>{String(row.title)} · {String(row.status)}</option>)}</select></label><label><span>New status</span><select className="select-control" value={newStatus} onChange={(event) => setNewStatus(event.target.value)}><option value="">Choose status</option><option value="todo">To do</option><option value="in_progress">In progress</option><option value="completed">Completed</option><option value="blocked">Blocked</option></select></label><Button variant="secondary" size="sm" onClick={() => void updateTask()}><Check className="size-3.5" />Save</Button></div>}
  </CardHeader>
    {section.rows.length === 0 ? <CardContent><EmptyState title="No records yet" detail="Records will appear here after they are added through the connected API." /></CardContent> : <div className="table-wrap"><table className="data-table"><thead><tr>{columns.map((column) => <th key={column}>{column.replaceAll("_", " ").toUpperCase()}</th>)}{kind === "leaves" && role === "admin" && <th>ACTIONS</th>}</tr></thead><tbody>{section.rows.map((row, index) => <tr key={String(row.id ?? index)}>{columns.map((column) => <td key={column}>{formatCell(row[column])}</td>)}{kind === "leaves" && role === "admin" && <td><span className="inline-actions"><Button size="sm" variant="ghost" disabled={row.status !== "pending" || busyId === Number(row.id)} aria-label="Approve leave" onClick={() => void decide(Number(row.id), "approved")}><Check className="size-4 text-teal" /></Button><Button size="sm" variant="ghost" disabled={row.status !== "pending" || busyId === Number(row.id)} aria-label="Reject leave" onClick={() => void decide(Number(row.id), "rejected")}><span className="text-rose-400">×</span></Button></span></td>}</tr>)}</tbody></table></div>}
  </Card>;
}

function formatCell(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "object") return JSON.stringify(value);
  if (typeof value === "number") return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
  return String(value);
}

function FormDialog({ action, onClose, onSaved }: { action: FormAction | null; onClose: () => void; onSaved: () => Promise<void> }) {
  const [values, setValues] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  useEffect(() => { setValues({}); }, [action]);
  if (!action) return null;
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setSaving(true);
    try { await action.submit(values); toast.success(`${action.title.replace("Add ", "").replace("Create ", "")} saved.`); onClose(); await onSaved(); }
    catch (error) { toast.error(error instanceof Error ? error.message : "Could not save record."); }
    finally { setSaving(false); }
  };
  return <Dialog open title={action.title} description="Validated by the backend and saved to the database." onOpenChange={(open) => { if (!open) onClose(); }}>
    <form className="profile-form" onSubmit={submit}><div className="form-grid">{action.fields.map((field) => <label className="form-field" key={field.name} htmlFor={`action-${field.name}`}><span>{field.label}{field.required ? " *" : ""}</span>{field.options ? <select id={`action-${field.name}`} className="form-select" required={field.required} value={values[field.name] || ""} onChange={(event) => setValues((current) => ({ ...current, [field.name]: event.target.value }))}><option value="">Select…</option>{field.options.map((option) => <option value={option} key={option}>{option}</option>)}</select> : <Input id={`action-${field.name}`} type={field.type || "text"} required={field.required} value={values[field.name] || ""} onChange={(event) => setValues((current) => ({ ...current, [field.name]: event.target.value }))} />}</label>)}</div><div className="dialog-actions"><Button type="button" variant="secondary" onClick={onClose}>Cancel</Button><Button type="submit" disabled={saving}>{saving ? "Saving…" : "Save record"}</Button></div></form>
  </Dialog>;
}