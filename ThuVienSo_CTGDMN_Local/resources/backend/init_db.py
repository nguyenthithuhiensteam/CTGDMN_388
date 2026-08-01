from backend.db import init_database as _init_database

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
    "schools",
    "users",
    "children",
    "observations",
    "assessments",
    "portfolio",
    "school_settings",
    "licenses",
]


def init_database() -> None:
    _init_database()


if __name__ == "__main__":
    init_database()
    from backend.db import get_database_url

    print(f"Initialized database: {get_database_url()}")
