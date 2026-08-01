from backend.db import get_connection, DATABASE_PATH

TABLES = [
    "age_groups",
    "domains",
    "competencies",
    "qualities",
    "yccd",
    "milestones",
    "activities",
    "rubrics",
    "year_plans",
    "month_plans",
    "week_plans",
    "day_plans",
    "children",
    "observations",
    "assessments",
    "portfolio",
    "school_settings",
    "licenses",
]

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS age_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    sort_order INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS domains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    sort_order INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS competencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    domain_id INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (domain_id) REFERENCES domains(id)
);

CREATE TABLE IF NOT EXISTS qualities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS yccd (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    content TEXT NOT NULL,
    age_group_id INTEGER,
    domain_id INTEGER,
    competency_id INTEGER,
    quality_id INTEGER,
    source_note TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (age_group_id) REFERENCES age_groups(id),
    FOREIGN KEY (domain_id) REFERENCES domains(id),
    FOREIGN KEY (competency_id) REFERENCES competencies(id),
    FOREIGN KEY (quality_id) REFERENCES qualities(id)
);

CREATE TABLE IF NOT EXISTS milestones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    age_group_id INTEGER,
    domain_id INTEGER,
    title TEXT NOT NULL,
    description TEXT,
    evidence_hint TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (age_group_id) REFERENCES age_groups(id),
    FOREIGN KEY (domain_id) REFERENCES domains(id)
);

CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE,
    title TEXT NOT NULL,
    age_group_id INTEGER,
    domain_id INTEGER,
    yccd_id INTEGER,
    objective TEXT,
    materials TEXT,
    steps TEXT,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (age_group_id) REFERENCES age_groups(id),
    FOREIGN KEY (domain_id) REFERENCES domains(id),
    FOREIGN KEY (yccd_id) REFERENCES yccd(id)
);

CREATE TABLE IF NOT EXISTS rubrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    yccd_id INTEGER,
    title TEXT NOT NULL,
    criteria TEXT,
    evidence_hint TEXT,
    support_next TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (yccd_id) REFERENCES yccd(id)
);

CREATE TABLE IF NOT EXISTS year_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    school_year TEXT NOT NULL,
    age_group_id INTEGER,
    title TEXT,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (age_group_id) REFERENCES age_groups(id)
);

CREATE TABLE IF NOT EXISTS month_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year_plan_id INTEGER,
    month_number INTEGER,
    theme_context TEXT,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (year_plan_id) REFERENCES year_plans(id)
);

CREATE TABLE IF NOT EXISTS week_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month_plan_id INTEGER,
    week_number INTEGER,
    title TEXT,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (month_plan_id) REFERENCES month_plans(id)
);

CREATE TABLE IF NOT EXISTS day_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_plan_id INTEGER,
    plan_date TEXT,
    title TEXT,
    care_nurture_notes TEXT,
    education_notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (week_plan_id) REFERENCES week_plans(id)
);

CREATE TABLE IF NOT EXISTS children (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    child_code TEXT UNIQUE,
    full_name TEXT NOT NULL,
    date_of_birth TEXT,
    gender TEXT,
    class_name TEXT,
    age_group_id INTEGER,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (age_group_id) REFERENCES age_groups(id)
);

CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    child_id INTEGER,
    observed_at TEXT DEFAULT CURRENT_TIMESTAMP,
    context TEXT,
    note TEXT NOT NULL,
    evidence TEXT,
    support_next TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (child_id) REFERENCES children(id)
);

CREATE TABLE IF NOT EXISTS assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    child_id INTEGER,
    yccd_id INTEGER,
    assessment_date TEXT DEFAULT CURRENT_TIMESTAMP,
    evidence TEXT,
    progress_note TEXT,
    support_next TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (child_id) REFERENCES children(id),
    FOREIGN KEY (yccd_id) REFERENCES yccd(id)
);

CREATE TABLE IF NOT EXISTS portfolio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    child_id INTEGER,
    title TEXT NOT NULL,
    artifact_type TEXT,
    artifact_path TEXT,
    note TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (child_id) REFERENCES children(id)
);

CREATE TABLE IF NOT EXISTS school_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    school_name TEXT,
    school_year TEXT,
    city TEXT,
    principal_name TEXT,
    contact_info TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS licenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    license_key TEXT,
    machine_code TEXT,
    status TEXT DEFAULT 'not_configured',
    note TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


def init_database() -> None:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()


if __name__ == "__main__":
    init_database()
    print(f"Initialized database: {DATABASE_PATH}")
