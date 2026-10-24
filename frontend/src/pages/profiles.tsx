import { zodResolver } from "@hookform/resolvers/zod";
import { Download, Edit3, Plus, Search, UserRound, UserRoundX, X } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";
import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";
import { Dialog } from "../components/ui/dialog";
import { Input } from "../components/ui/input";
import { EmptyState, ErrorState, LoadingState } from "../components/ui/state";
import { useAuth } from "../services/auth";
import { api, ApiError } from "../services/api";
import type { Employee, Student } from "../types/api";

type Kind = "students" | "employees";
type Profile = Student | Employee;

const studentSchema = z.object({
  register_number: z.string().trim().min(1, "Register number is required.").max(50),
  admission_number: z.string().max(50).optional(),
  full_name: z.string().trim().min(1, "Full name is required.").max(160),
  course: z.string().optional(), department: z.string().optional(), branch: z.string().optional(),
  academic_year: z.string().optional(), current_semester: z.string().optional(), section: z.string().optional(),
  email: z.union([z.literal(""), z.email()]).optional(), phone: z.string().max(40).optional(),
  date_of_birth: z.string().optional(), admission_date: z.string().optional(),
});
const employeeSchema = z.object({
  employee_code: z.string().trim().min(1, "Employee code is required.").max(50),
  full_name: z.string().trim().min(1, "Full name is required.").max(160),
  department: z.string().max(120), designation: z.string().max(120),
  work_email: z.union([z.literal(""), z.email()]).optional(),
  work_phone: z.string().max(40).optional(), joining_date: z.string().optional(),
  employment_status: z.enum(["active", "on_leave", "inactive", "terminated", "archived"]),
  reporting_manager: z.string().optional(), emergency_contact: z.string().optional(),
  skills: z.string().optional(), certifications: z.string().optional(),
});

const studentFields = [
  ["register_number", "Register number *"], ["admission_number", "Admission number"], ["full_name", "Full name *"],
  ["course", "Course"], ["department", "Department"], ["branch", "Branch"], ["academic_year", "Academic year"],
  ["current_semester", "Semester"], ["section", "Section"], ["email", "Email"], ["phone", "Phone"],
  ["date_of_birth", "Date of birth"], ["admission_date", "Admission date"],
] as const;
const employeeFields = [
  ["employee_code", "Employee code *"], ["full_name", "Full name *"], ["department", "Department"],
  ["designation", "Designation"], ["work_email", "Work email"], ["work_phone", "Work phone"],
  ["joining_date", "Joining date"], ["employment_status", "Employment status"], ["reporting_manager", "Reporting manager"],
  ["emergency_contact", "Emergency contact"], ["skills", "Skills"], ["certifications", "Certifications"],
] as const;

export function ProfilesPage({ kind }: { kind: Kind }) {
  const { user } = useAuth();
  const [rows, setRows] = useState<Profile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [course, setCourse] = useState("");
  const [department, setDepartment] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Profile | null>(null);
  const selfView = kind === "employees" && user?.role === "employee";
  const isStudent = kind === "students";

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      if (selfView) {
        setRows([await api.myEmployee()]);
      } else if (isStudent) {
        const params = new URLSearchParams();
        if (search) params.set("search", search);
        if (course) params.set("course", course);
        if (department) params.set("department", department);
        setRows(await api.students(params.toString()));
      } else {
        const params = new URLSearchParams();
        if (search) params.set("search", search);
        if (department) params.set("department", department);
        setRows(await api.employees(params.toString()));
      }
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : "Could not load profiles.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void load(); }, [kind, selfView]);

  const openCreate = () => { setEditing(null); setDialogOpen(true); };
  const openEdit = (record: Profile) => { setEditing(record); setDialogOpen(true); };
  const archive = async (record: Profile) => {
    const label = isStudent ? (record as Student).register_number : (record as Employee).employee_code;
    if (!window.confirm(`Archive ${label}? This hides the profile from active lists.`)) return;
    try {
      if (isStudent) await api.archiveStudent(record.id);
      else await api.archiveEmployee(record.id);
      toast.success("Profile archived.");
      await load();
    } catch (reason) {
      toast.error(reason instanceof Error ? reason.message : "Archive failed.");
    }
  };

  const submitSearch = (event: FormEvent) => { event.preventDefault(); void load(); };
  const title = selfView ? "My profile" : isStudent ? "Students" : "Employees";
  if (selfView && error) return <ErrorState message={error} onRetry={() => void load()} />;

  return <div>
    <div className="page-heading"><div><p className="eyebrow">RECORDS / DIRECTORY</p><h1>{title}</h1><p>{selfView ? "Your linked employee profile." : isStudent ? "Search, filter, and maintain student records." : "Manage employee records and access."}</p></div>
      {!selfView && <div className="page-actions"><Button variant="secondary" onClick={() => api.downloadCsv(kind).catch((reason: Error) => toast.error(reason.message))}><Download className="size-4" />Export CSV</Button><Button onClick={openCreate}><Plus className="size-4" />Add {isStudent ? "student" : "employee"}</Button></div>}
    </div>
    {selfView ? loading ? <LoadingState /> : rows[0] ? <SelfProfile record={rows[0] as Employee} /> : <EmptyState title="No employee profile linked" detail="Ask an administrator to link your account to an employee profile." /> : <>
      <form onSubmit={submitSearch} className="profile-toolbar"><div className="search-wrap"><Search className="size-4" /><Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder={`Search ${isStudent ? "name or register number" : "name or employee code"}`} /></div>
        <div className="filter-row">{isStudent && <Input className="filter-input" value={course} onChange={(event) => setCourse(event.target.value)} placeholder="Course filter" />}{<Input className="filter-input" value={department} onChange={(event) => setDepartment(event.target.value)} placeholder="Department filter" />}<Button type="submit" variant="secondary">Apply filters</Button></div>
      </form>
      {loading ? <LoadingState label={`Loading ${kind}`} /> : error ? <ErrorState message={error} onRetry={() => void load()} /> : rows.length === 0 ? <EmptyState title={`No ${kind} found`} detail={search || course || department ? "Adjust your search or filters." : `Add a ${isStudent ? "student" : "employee"} record to begin.`} /> :
        <Card className="directory-card"><div className="table-wrap"><table className="data-table"><thead><tr>{isStudent ? <><th>STUDENT</th><th>REGISTER / ADMISSION</th><th>COURSE</th><th>DEPARTMENT</th><th>YEAR / SEMESTER</th><th>STATUS</th></> : <><th>EMPLOYEE</th><th>CODE</th><th>DEPARTMENT</th><th>DESIGNATION</th><th>CONTACT</th><th>STATUS</th></>}<th><span className="sr-only">Actions</span></th></tr></thead><tbody>
          {rows.map((record) => isStudent ? <StudentRow key={record.id} record={record as Student} onEdit={openEdit} onArchive={archive} /> : <EmployeeRow key={record.id} record={record as Employee} onEdit={openEdit} onArchive={archive} />)}
        </tbody></table></div><div className="table-footer"><span>{rows.length} records</span><span>Live database</span></div></Card>}
    </>}
    <ProfileEditor kind={kind} record={editing} open={dialogOpen} onOpenChange={setDialogOpen} onSaved={load} />
  </div>;
}

function StudentRow({ record, onEdit, onArchive }: { record: Student; onEdit: (record: Profile) => void; onArchive: (record: Profile) => void }) {
  return <tr><td><span className="person-cell"><span className="avatar student-avatar">{record.full_name.slice(0, 1).toUpperCase()}</span><span><strong className="table-primary">{record.full_name}</strong><small>{record.email || "No email"}</small></span></span></td><td><strong>{record.register_number}</strong><div className="table-secondary">{record.admission_number || "No admission no."}</div></td><td>{record.course || "—"}</td><td>{record.department || "—"}</td><td>{record.academic_year || "—"} / {record.current_semester || "—"}</td><td><StatusTag status={record.enrollment_status || "active"} /></td><td><RowActions onEdit={() => onEdit(record)} onArchive={() => onArchive(record)} /></td></tr>;
}

function EmployeeRow({ record, onEdit, onArchive }: { record: Employee; onEdit: (record: Profile) => void; onArchive: (record: Profile) => void }) {
  return <tr><td><span className="person-cell"><span className="avatar employee-avatar">{record.full_name.slice(0, 1).toUpperCase()}</span><span><strong className="table-primary">{record.full_name}</strong><small>{record.work_email || "No work email"}</small></span></span></td><td>{record.employee_code}</td><td>{record.department || "—"}</td><td>{record.designation || "—"}</td><td>{record.work_phone || "—"}</td><td><StatusTag status={record.employment_status || "active"} /></td><td><RowActions onEdit={() => onEdit(record)} onArchive={() => onArchive(record)} /></td></tr>;
}

function RowActions({ onEdit, onArchive }: { onEdit: () => void; onArchive: () => void }) {
  return <span className="row-actions"><Button variant="ghost" size="icon" title="Edit profile" aria-label="Edit profile" onClick={onEdit}><Edit3 className="size-4" /></Button><Button variant="ghost" size="icon" title="Archive profile" aria-label="Archive profile" onClick={onArchive}><UserRoundX className="size-4" /></Button></span>;
}

function StatusTag({ status }: { status: string }) {
  return <span className={`status-tag status-${status.replaceAll("_", "-")}`}>{status.replaceAll("_", " ")}</span>;
}

function SelfProfile({ record }: { record: Employee }) {
  const data = [["Employee code", record.employee_code], ["Department", record.department], ["Designation", record.designation], ["Work email", record.work_email], ["Work phone", record.work_phone], ["Joining date", record.joining_date], ["Employment status", record.employment_status], ["Reporting manager", record.reporting_manager], ["Skills", record.skills], ["Certifications", record.certifications]];
  return <Card className="self-profile"><header className="self-profile-header"><span className="avatar employee-avatar self-avatar"><UserRound className="size-5" /></span><div><h2>{record.full_name}</h2><p>{record.designation || "Employee"} · {record.department || "Department not set"}</p></div></header><dl className="profile-details">{data.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value || "Not provided"}</dd></div>)}</dl></Card>;
}

function ProfileEditor({ kind, record, open, onOpenChange, onSaved }: { kind: Kind; record: Profile | null; open: boolean; onOpenChange: (open: boolean) => void; onSaved: () => Promise<void> | void }) {
  if (kind === "students") {
    return <StudentEditor record={record && "register_number" in record ? record : null} open={open} onOpenChange={onOpenChange} onSaved={onSaved} />;
  }
  return <EmployeeEditor record={record && "employee_code" in record ? record : null} open={open} onOpenChange={onOpenChange} onSaved={onSaved} />;
}

function StudentEditor({ record, open, onOpenChange, onSaved }: { record: Student | null; open: boolean; onOpenChange: (open: boolean) => void; onSaved: () => Promise<void> | void }) {
  type Values = z.infer<typeof studentSchema>;
  const form = useForm<Values>({ resolver: zodResolver(studentSchema), defaultValues: studentValues(record) });
  useEffect(() => { form.reset(studentValues(record)); }, [record, open]);
  const close = () => onOpenChange(false);
  const submit = form.handleSubmit(async (values) => {
    try {
      if (record) await api.updateStudent(record.id, values);
      else await api.createStudent(values);
      toast.success(record ? "Student updated." : "Student created.");
      close();
      await onSaved();
    } catch (reason) { toast.error(reason instanceof Error ? reason.message : "Could not save student."); }
  });
  const errors = form.formState.errors;
  return <Dialog open={open} onOpenChange={onOpenChange} title={`${record ? "Edit" : "Add"} student`} description="Profile changes are saved directly to the institutional database.">
    <form className="profile-form" onSubmit={submit}><div className="form-grid">
      {studentFields.map(([name, label]) => <label className="form-field" key={name} htmlFor={`student-${name}`}><span>{label}</span><Input id={`student-${name}`} {...form.register(name)} aria-invalid={Boolean(errors[name])} />{errors[name]?.message && <small className="field-error">{errors[name]?.message}</small>}</label>)}
    </div><div className="dialog-actions"><Button type="button" variant="secondary" onClick={close}><X className="size-4" />Cancel</Button><Button type="submit" disabled={form.formState.isSubmitting}>{form.formState.isSubmitting ? "Saving…" : record ? "Save changes" : "Create profile"}</Button></div></form>
  </Dialog>;
}

function studentValues(record: Student | null): z.infer<typeof studentSchema> {
  return {
    register_number: record?.register_number || "", admission_number: record?.admission_number || "", full_name: record?.full_name || "",
    course: record?.course || "", department: record?.department || "", branch: record?.branch || "", academic_year: record?.academic_year || "",
    current_semester: record?.current_semester || "", section: record?.section || "", email: record?.email || "", phone: record?.phone || "",
    date_of_birth: record?.date_of_birth || "", admission_date: record?.admission_date || "",
  };
}

function EmployeeEditor({ record, open, onOpenChange, onSaved }: { record: Employee | null; open: boolean; onOpenChange: (open: boolean) => void; onSaved: () => Promise<void> | void }) {
  type Values = z.infer<typeof employeeSchema>;
  const form = useForm<Values>({ resolver: zodResolver(employeeSchema), defaultValues: employeeValues(record) });
  useEffect(() => { form.reset(employeeValues(record)); }, [record, open]);
  const close = () => onOpenChange(false);
  const submit = form.handleSubmit(async (values) => {
    try {
      if (record) await api.updateEmployee(record.id, values);
      else await api.createEmployee(values);
      toast.success(record ? "Employee updated." : "Employee created.");
      close();
      await onSaved();
    } catch (reason) { toast.error(reason instanceof Error ? reason.message : "Could not save employee."); }
  });
  const errors = form.formState.errors;
  return <Dialog open={open} onOpenChange={onOpenChange} title={`${record ? "Edit" : "Add"} employee`} description="Profile changes are saved directly to the institutional database.">
    <form className="profile-form" onSubmit={submit}><div className="form-grid">
      {employeeFields.map(([name, label]) => <label className={`form-field ${name === "skills" || name === "certifications" ? "span-two" : ""}`} key={name} htmlFor={`employee-${name}`}><span>{label}</span>{name === "employment_status" ? <select id={`employee-${name}`} className="form-select" {...form.register("employment_status")}><option value="active">Active</option><option value="on_leave">On leave</option><option value="inactive">Inactive</option><option value="terminated">Terminated</option></select> : <Input id={`employee-${name}`} {...form.register(name)} aria-invalid={Boolean(errors[name])} />}{errors[name]?.message && <small className="field-error">{errors[name]?.message}</small>}</label>)}
    </div><div className="dialog-actions"><Button type="button" variant="secondary" onClick={close}><X className="size-4" />Cancel</Button><Button type="submit" disabled={form.formState.isSubmitting}>{form.formState.isSubmitting ? "Saving…" : record ? "Save changes" : "Create profile"}</Button></div></form>
  </Dialog>;
}

function employeeValues(record: Employee | null): z.infer<typeof employeeSchema> {
  return {
    employee_code: record?.employee_code || "", full_name: record?.full_name || "", department: record?.department || "",
    designation: record?.designation || "", work_email: record?.work_email || "", work_phone: record?.work_phone || "",
    joining_date: record?.joining_date || "", employment_status: (record?.employment_status as z.infer<typeof employeeSchema>["employment_status"]) || "active",
    reporting_manager: record?.reporting_manager || "", emergency_contact: record?.emergency_contact || "", skills: record?.skills || "", certifications: record?.certifications || "",
  };
}