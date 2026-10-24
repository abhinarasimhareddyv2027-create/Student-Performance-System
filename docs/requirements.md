# Requirements Baseline

## Scope

The core product is a Python desktop application backed by a local SQLite database. It supports authorized staff workflows for student and employee records, academic results, attendance and leave, student activities, employee tasks and goals, analytics, and exports. A REST API and Windows executable are optional extensions, not prerequisites for the desktop system.

The first release should favor correct, auditable records over broad automation. Performance summaries are informational. In particular, attendance and task counts alone must not be used to automatically rate employees.

## Users and access

| Role | Intended access |
| --- | --- |
| Admin | Configure users and reference data; access and maintain all operational records; perform protected backup/restore and administrative actions. |
| Teacher | Manage permitted student academic, attendance, activity, and report workflows. No user administration or unrestricted employee-record access. |
| Employee | View and maintain only explicitly permitted own profile, attendance, assigned tasks, goals, and review information. No access to other employees' or students' private records. |

Authorization must be checked in the service layer, not only by hiding UI controls. Passwords must be stored as adaptive password hashes, never plaintext. Initial admin creation must be an explicit setup flow; no default credentials or real personal records belong in source control.

## Functional requirements

### Profiles

- Create, view, update, archive, and search student and employee records.
- Enforce unique student register numbers, admission numbers where supplied, and employee codes.
- Support filters for student course, department, academic year, semester, and section, and employee department and designation.
- Keep student academic enrollment history rather than overwriting prior course/term placement.
- Track employee manager, skills/training, agreed goals, review period, and manager feedback.
- Treat profile images as optional files; validate and store managed paths rather than arbitrary user-provided paths.

### Academics

- Manage departments, courses, subjects, academic periods, and exams with configured maximum and pass marks.
- Record a mark as pending/unentered, absent, or entered. An entered mark of zero is valid; pending and absent are not silently converted to zero.
- Validate entered marks against the exam's configured range. Calculate totals, averages, percentages, grades, pass rates, and trends using documented rules and denominators.
- Generate individual marksheets and class summaries from database records.

### Attendance and leave

- Keep student and employee attendance in separately linked records with date, session/shift as appropriate, status, and optional check-in/check-out times.
- Make duplicate attendance for the same entity/date/session impossible unless a future documented policy allows multiple sessions.
- Track leave requests and approval separately from attendance; do not treat pending leave as approved absence.
- Calculate attendance percentages over explicitly defined scheduled sessions, excluding sessions that are not eligible under the configured policy. Show the numerator and denominator with summaries.

### Activities, tasks, and goals

- Record student activities, projects, achievements, certificates, category, and participation date.
- Assign employee tasks with dates, status, project, milestones, and completion notes.
- Track employee goals against documented, job-relevant criteria. A progress percentage must have an explicit basis and must not be inferred from attendance alone.

### Analytics and reports

- Use Pandas for cleaning, filtering, grouping, and summaries and NumPy for numerical measures such as mean, median, minimum, maximum, and standard deviation where appropriate.
- Handle missing, invalid, and empty data explicitly; avoid division by zero and identify the population and denominator for each metric.
- Provide dashboard summaries and Matplotlib charts based only on stored records. Any demo dataset must be fictional and clearly labeled.
- Export supported profile, marksheet, attendance, class, task, and review reports to CSV/Excel/PDF. Verify exported values against source records.

### Reliability and operations

- Use transactions for related writes, foreign keys, uniqueness/check constraints, and indexes for common lookups.
- Never delete or overwrite an existing database at startup. Document schema upgrades and preserve data during changes.
- Provide timestamped backups, validate backups before restore, require confirmation for restore/destructive actions, and test restoration against a separate test database.
- Log errors and important changes without writing passwords or unnecessary sensitive personal data to logs.

## Non-functional requirements

- Compatible with Python 3.11 or newer supported by project dependencies.
- Desktop-first, modular Python UI using CustomTkinter and ttk; responsive to ordinary resizing and keyboard operation where practical.
- SQLite is the local storage default; the database location is configurable and excluded from version control.
- Business rules are testable without launching the UI and tests use temporary databases and fictional data.
- UI errors must be actionable and must not expose stack traces or secrets to ordinary users.

## Acceptance gates

1. Duplicate identifiers, invalid marks, and unauthorized operations are rejected at the service/database boundary.
2. Pending, absent, and zero marks remain distinguishable in storage, analytics, and reports.
3. Attendance and pass-rate calculations have documented denominators and defined empty-data behavior.
4. Tests do not require a production database, network access, or real student/employee information.
5. Database initialization never silently replaces existing user data.
6. Features are marked complete only after implementation and focused tests exist.

## Decisions deferred

The initial-admin bootstrap mechanism, database migration tool, exact grade boundaries, attendance session policy, retention rules, and optional API authentication scheme must be finalized during the relevant implementation phase. Defaults must not be invented silently; they should be configurable or documented and approved by the deployment owner.