export type Role = "admin" | "teacher" | "employee";

export interface User {
  id: number;
  username: string;
  role: Role;
  employee_id: number | null;
}

export interface Student {
  id: number;
  register_number: string;
  admission_number: string | null;
  full_name: string;
  course: string | null;
  department: string | null;
  branch: string | null;
  academic_year: string | null;
  current_semester: string | null;
  section: string | null;
  email: string | null;
  phone: string | null;
  date_of_birth: string | null;
  address: string | null;
  guardian_name: string | null;
  guardian_contact: string | null;
  admission_date: string | null;
  enrollment_status: string | null;
  archived: boolean;
}

export interface Employee {
  id: number;
  employee_code: string;
  full_name: string;
  department: string;
  designation: string;
  work_email: string | null;
  work_phone: string | null;
  joining_date: string | null;
  employment_status: string | null;
  reporting_manager: string | null;
  emergency_contact: string | null;
  skills: string | null;
  certifications: string | null;
  active: boolean;
}

export interface Overview {
  total_students: number | null;
  total_employees: number | null;
  pending_tasks: number;
  average_marks_percentage: number | null;
  pass_percentage: number | null;
  attendance_percentage: number | null;
}

export interface AcademicAnalytics {
  subject_averages: Array<{ subject_code: string; subject_name: string; average_percentage: number; entered_marks: number }>;
  performance_trends: Array<{ year: string; semester: string; average_percentage: number; pass_percentage: number; mark_count: number }>;
  grade_distribution: Array<{ grade: string; count: number }>;
  class_summaries: Array<{ year: string; semester: string; average_percentage: number; pass_percentage: number; student_results: number }>;
  grade_thresholds: Record<string, number>;
  entered_mark_count: number;
  excluded_pending_or_absent: number;
}

export interface Department {
  id: number;
  code: string;
  name: string;
  archived: boolean;
}

export interface Course {
  id: number;
  department_id: number;
  code: string;
  name: string;
  archived: boolean;
}

export interface Subject {
  id: number;
  course_id: number;
  code: string;
  name: string;
  archived: boolean;
}

export interface Examination {
  id: number;
  subject_id: number;
  name: string;
  academic_year: string;
  semester: string;
  exam_date: string | null;
  maximum_marks: number;
  pass_marks: number;
}

export interface Mark {
  id: number;
  examination_id: number;
  student_id: number;
  status: "pending" | "absent" | "entered";
  score: number | null;
}

export interface StudentAttendance {
  id: number;
  student_id: number;
  attendance_date: string;
  session: string;
  status: "present" | "absent" | "excused";
  note: string | null;
}

export interface EmployeeAttendance {
  id: number;
  employee_id: number;
  attendance_date: string;
  shift: string;
  status: "present" | "absent" | "leave";
  check_in: string | null;
  check_out: string | null;
}

export interface LeaveRecord {
  id: number;
  student_id: number | null;
  employee_id: number | null;
  start_date: string;
  end_date: string;
  reason: string;
  status: "pending" | "approved" | "rejected";
}

export interface Activity {
  id: number;
  student_id: number;
  title: string;
  category: string;
  participation_date: string;
  description: string | null;
}

export interface Task {
  id: number;
  employee_id: number;
  title: string;
  description: string | null;
  project: string | null;
  assigned_date: string;
  deadline: string | null;
  status: "todo" | "in_progress" | "completed" | "blocked";
  completion_notes: string | null;
}

export interface Review {
  id: number;
  employee_id: number;
  reviewer_id: number | null;
  period_start: string;
  period_end: string;
  criteria: string;
  score: number | null;
  feedback: string;
}