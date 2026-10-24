import type { AcademicAnalytics, Overview, Student, Employee, Department, Course, Subject, Examination, Mark, StudentAttendance, EmployeeAttendance, LeaveRecord, Activity, Task, Review, User } from "../types/api";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "/api").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...options.headers,
    },
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null) as { detail?: string } | null;
    throw new ApiError(payload?.detail || `Request failed (${response.status}).`, response.status);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

const json = (method: string, body?: unknown): RequestInit => ({
  method,
  ...(body === undefined ? {} : { body: JSON.stringify(body) }),
});

export const api = {
  health: () => request<{ status: string }>("/health"),
  login: (username: string, password: string) => request<User>("/auth/login", json("POST", { username, password })),
  logout: () => request<void>("/auth/logout", json("POST")),
  me: () => request<User>("/auth/me"),
  overview: () => request<Overview>("/analytics/overview"),
  academicAnalytics: () => request<AcademicAnalytics>("/analytics/academic"),
  attendanceAnalytics: () => request<{ student_trend: Array<Record<string, unknown>>; employee_trend: Array<Record<string, unknown>>; denominator: string }>("/analytics/attendance"),
  employeeAnalytics: () => request<{ task_completion: Array<Record<string, unknown>>; review_summaries: Array<Record<string, unknown>>; note: string }>("/analytics/employees"),
  students: (params = "") => request<Student[]>(`/students${params ? `?${params}` : ""}`),
  student: (id: number) => request<Student>(`/students/${id}`),
  createStudent: (body: Partial<Student>) => request<Student>("/students", json("POST", body)),
  updateStudent: (id: number, body: Partial<Student>) => request<Student>(`/students/${id}`, json("PUT", body)),
  archiveStudent: (id: number) => request<Student>(`/students/${id}/archive`, json("POST")),
  employees: (params = "") => request<Employee[]>(`/employees${params ? `?${params}` : ""}`),
  employee: (id: number) => request<Employee>(`/employees/${id}`),
  myEmployee: () => request<Employee>("/employees/me"),
  createEmployee: (body: Partial<Employee>) => request<Employee>("/employees", json("POST", body)),
  updateEmployee: (id: number, body: Partial<Employee>) => request<Employee>(`/employees/${id}`, json("PUT", body)),
  archiveEmployee: (id: number) => request<Employee>(`/employees/${id}/archive`, json("POST")),
  departments: () => request<Department[]>("/departments"),
  createDepartment: (body: Pick<Department, "code" | "name">) => request<Department>("/departments", json("POST", body)),
  archiveDepartment: (id: number) => request<Department>(`/departments/${id}/archive`, json("PATCH")),
  courses: (departmentId?: number) => request<Course[]>(`/courses${departmentId ? `?department_id=${departmentId}` : ""}`),
  createCourse: (body: Pick<Course, "department_id" | "code" | "name">) => request<Course>("/courses", json("POST", body)),
  subjects: (courseId?: number) => request<Subject[]>(`/subjects${courseId ? `?course_id=${courseId}` : ""}`),
  createSubject: (body: Pick<Subject, "course_id" | "code" | "name">) => request<Subject>("/subjects", json("POST", body)),
  exams: () => request<Examination[]>("/examinations"),
  createExam: (body: Omit<Examination, "id">) => request<Examination>("/examinations", json("POST", body)),
  marks: (examId?: number) => request<Mark[]>(`/marks${examId ? `?examination_id=${examId}` : ""}`),
  createMark: (body: Omit<Mark, "id">) => request<Mark>("/marks", json("POST", body)),
  studentAttendance: () => request<StudentAttendance[]>("/attendance/students"),
  createStudentAttendance: (body: Omit<StudentAttendance, "id">) => request<StudentAttendance>("/attendance/students", json("POST", body)),
  employeeAttendance: () => request<EmployeeAttendance[]>("/attendance/employees"),
  createEmployeeAttendance: (body: Omit<EmployeeAttendance, "id">) => request<EmployeeAttendance>("/attendance/employees", json("POST", body)),
  leaves: () => request<LeaveRecord[]>("/leaves"),
  createLeave: (body: Omit<LeaveRecord, "id">) => request<LeaveRecord>("/leaves", json("POST", body)),
  decideLeave: (id: number, decision: "approved" | "rejected") => request<LeaveRecord>(`/leaves/${id}/decision?decision=${decision}`, json("PATCH")),
  activities: () => request<Activity[]>("/activities"),
  createActivity: (body: Omit<Activity, "id">) => request<Activity>("/activities", json("POST", body)),
  tasks: () => request<Task[]>("/tasks"),
  createTask: (body: Omit<Task, "id">) => request<Task>("/tasks", json("POST", body)),
  updateTask: (id: number, status: Task["status"]) => request<Task>(`/tasks/${id}/status?task_status=${status}`, json("PATCH")),
  reviews: () => request<Review[]>("/reviews"),
  createReview: (body: Omit<Review, "id" | "reviewer_id">) => request<Review>("/reviews", json("POST", body)),
  users: () => request<User[]>("/users"),
  createUser: (body: { username: string; password: string; role: string; employee_id?: number }) => request<User>("/users", json("POST", body)),
  setUserActive: (id: number, active: boolean) => request<User>(`/users/${id}/active?active=${active}`, json("PATCH")),
  downloadCsv: async (kind: "students" | "employees") => {
    const response = await fetch(`${API_BASE}/reports/${kind}.csv`, { credentials: "include" });
    if (!response.ok) throw new ApiError("Could not export report.", response.status);
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${kind}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  },
};