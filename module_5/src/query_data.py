"""
Module contains functions to query PostgreSQL for graduate school application insights.

This module implements Step 2 SQL Injection Defenses by using psycopg SQL composition,
separating query construction from execution, and enforcing strict result limits
based on environment configuration (Step 3).
"""
from psycopg import sql
from config import get_db_connection, Config  # Updated to use centralized Config

# Module 5 Requirement: Enforce a maximum allowed limit from environment
MAX_ALLOWED_LIMIT = Config.MAX_ALLOWED_LIMIT


def clamp_limit(requested_limit):
    """
    Enforces a maximum allowed limit (1-100) for any database query.
    This prevents potential Denial of Service (DoS) by requesting excessive rows.

    :param requested_limit: The limit provided by the user or logic.
    :type requested_limit: int or str
    :return: Clamped integer between 1 and 100.
    :rtype: int
    """
    try:
        val = int(requested_limit)
        return max(1, min(val, MAX_ALLOWED_LIMIT))
    except (ValueError, TypeError):
        return MAX_ALLOWED_LIMIT


def get_fall_2026_apps_count():
    """
    Returns the count of applicants who applied for Fall 2026.

    This function utilizes SQL identifiers and literals to prevent SQL injection
    while adhering to the clamped result limit.

    :return: Number of applicants for Fall 2026.
    :rtype: int
    :raises psycopg.DatabaseError: If a database error occurs.
    """
    connection = get_db_connection()
    with connection.cursor() as cur:
        # SQL statement construction with SQL composition (Step 2)
        stmt = sql.SQL("""
            SELECT COUNT(term) 
            FROM {table}
            WHERE term = %s
            LIMIT {lim};
        """).format(
            table=sql.Identifier('applicantdata'),
            lim=sql.Literal(clamp_limit(MAX_ALLOWED_LIMIT))
        )
        # Execution with parameters to prevent injection
        cur.execute(stmt, ('Fall 2026',))
        result = cur.fetchone()
        count = result[0] if result else 0
    connection.close()
    return count


def get_percent_international():
    """
    Returns the percentage of entries from international students.

    The query calculates a ratio and rounds the numeric result to two decimal places.

    :return: Percentage of international applicants rounded to two decimals.
    :rtype: float
    :raises psycopg.DatabaseError: If a database error occurs.
    """
    connection = get_db_connection()
    with connection.cursor() as cur:
        stmt = sql.SQL("""
            SELECT
                ROUND(
                    (100.0 * SUM(CASE WHEN us_or_international = %s 
                    THEN 1 ELSE 0 END)::FLOAT / COUNT(*))::NUMERIC,
                    2
                ) AS percent_international
            FROM {table}
            LIMIT {lim};
        """).format(
            table=sql.Identifier('applicantdata'),
            lim=sql.Literal(clamp_limit(MAX_ALLOWED_LIMIT))
        )
        cur.execute(stmt, ('International',))
        result = cur.fetchone()
        percentage = result[0] if result else 0.0
    connection.close()
    return percentage


def get_averages():
    """
    Returns average GPA, GRE, and GRE Analytical Writing scores for all applicants.

    Averages are rounded to two decimal places.

    :return: Tuple containing (avg_gpa, avg_gre, avg_gre_v, avg_gre_aw)
    :rtype: tuple
    :raises psycopg.DatabaseError: If a database error occurs.
    """
    connection = get_db_connection()
    with connection.cursor() as cur:
        stmt = sql.SQL("""
            SELECT
                ROUND(AVG(gpa)::numeric, 2) AS avg_gpa,
                ROUND(AVG(gre)::numeric, 2) AS avg_gre,
                ROUND(AVG(gre_v)::numeric, 2) AS avg_gre_v,
                ROUND(AVG(gre_aw)::numeric, 2) AS avg_gre_aw
            FROM {table}
            LIMIT {lim};
        """).format(
            table=sql.Identifier('applicantdata'),
            lim=sql.Literal(clamp_limit(MAX_ALLOWED_LIMIT))
        )
        cur.execute(stmt)
        averages = cur.fetchone()
    connection.close()
    return averages


def get_avg_gpa_american_fall_2026():
    """
    Returns the average GPA of American applicants for Fall 2026.

    :return: Average GPA of American students for Fall 2026.
    :rtype: float
    :raises psycopg.DatabaseError: If a database error occurs.
    """
    connection = get_db_connection()
    with connection.cursor() as cur:
        stmt = sql.SQL("""
            SELECT ROUND(AVG(gpa)::numeric, 2) AS avg_gpa_american_fall_2026
            FROM {table}
            WHERE us_or_international = %s
                    AND term = %s
            LIMIT {lim};
        """).format(
            table=sql.Identifier('applicantdata'),
            lim=sql.Literal(clamp_limit(MAX_ALLOWED_LIMIT))
        )
        cur.execute(stmt, ('American', 'Fall 2026'))
        result = cur.fetchone()
        avg_gpa = result[0] if result else 0.0
    connection.close()
    return avg_gpa


def get_percent_accepted_fall_2025():
    """
    Returns the percentage of applicants accepted for Fall 2025.

    :return: Percentage of accepted applicants for Fall 2025.
    :rtype: float
    :raises psycopg.DatabaseError: If a database error occurs.
    """
    connection = get_db_connection()
    with connection.cursor() as cur:
        stmt = sql.SQL("""
            SELECT ROUND(
                (100 * SUM(CASE WHEN status = %s THEN 1 ELSE 0 END)::FLOAT / COUNT(*))::NUMERIC,
                2
            ) AS percent_accepted
            FROM {table}
            WHERE term = %s
            LIMIT {lim};
        """).format(
            table=sql.Identifier('applicantdata'),
            lim=sql.Literal(clamp_limit(MAX_ALLOWED_LIMIT))
        )
        cur.execute(stmt, ('Accepted', 'Fall 2025'))
        result = cur.fetchone()
        percentage = result[0] if result else 0.0
    connection.close()
    return percentage


def get_avg_gpa_fall_2026_acceptances():
    """
    Returns the average GPA of applicants accepted for Fall 2026.

    :return: Average GPA of Fall 2026 accepted applicants.
    :rtype: float
    :raises psycopg.DatabaseError: If a database error occurs.
    """
    connection = get_db_connection()
    with connection.cursor() as cur:
        stmt = sql.SQL("""
            SELECT ROUND(AVG(gpa)::numeric, 2) AS avg_gpa_fall_2026_acceptances
            FROM {table}
            WHERE term = %s
                AND status = %s
            LIMIT {lim};
        """).format(
            table=sql.Identifier('applicantdata'),
            lim=sql.Literal(clamp_limit(MAX_ALLOWED_LIMIT))
        )
        cur.execute(stmt, ('Fall 2026', 'Accepted'))
        result = cur.fetchone()
        avg_gpa = result[0] if result else 0.0
    connection.close()
    return avg_gpa


def get_jhu_cs_masters_count():
    """
    Returns the count of applicants who applied to JHU for a master's in CS.

    :return: Number of JHU CS master's applicants.
    :rtype: int
    :raises psycopg.DatabaseError: If a database error occurs.
    """
    connection = get_db_connection()
    with connection.cursor() as cur:
        stmt = sql.SQL("""
            SELECT COUNT(*)
            FROM {table}
            WHERE program ILIKE %s
                AND degree ILIKE %s
                AND program ILIKE %s
            LIMIT {lim};
        """).format(
            table=sql.Identifier('applicantdata'),
            lim=sql.Literal(clamp_limit(MAX_ALLOWED_LIMIT))
        )
        cur.execute(stmt, ('%Johns Hopkins%', '%masters%', '%computer Science%'))
        result = cur.fetchone()
        count = result[0] if result else 0
    connection.close()
    return count


def get_num_entries_phd_cs_specified_schools():
    """
    Returns count of 2026 PhD CS acceptances from Georgetown, MIT, Stanford, or CMU.

    :return: Number of matching entries.
    :rtype: int
    :raises psycopg.DatabaseError: If a database error occurs.
    """
    connection = get_db_connection()
    with connection.cursor() as cur:
        stmt = sql.SQL("""
            SELECT COUNT(*) AS num_entries
                FROM {table}
                WHERE EXTRACT(YEAR FROM date_added) = 2026
                    AND status = %s
                    AND degree ILIKE %s
                    AND program ILIKE %s
                    AND (
                        program ILIKE %s
                        OR program ILIKE %s
                        OR program ILIKE %s
                        OR program ILIKE %s
                    )
            LIMIT {lim};
        """).format(
            table=sql.Identifier('applicantdata'),
            lim=sql.Literal(clamp_limit(MAX_ALLOWED_LIMIT))
        )
        params = (
            'Accepted', '%phd%', '%Computer Science%', '%Georgetown%',
            '%Mit%', '%Stanford%', '%Carnegie Mellon%'
        )
        cur.execute(stmt, params)
        result = cur.fetchone()
        count = result[0] if result else 0
    connection.close()
    return count


def get_llm_variance():
    """
    Returns the difference in counts between LLM-generated and standard fields.

    Calculates the variance to verify data integrity between raw scraped strings
    and LLM-parsed university/program entities.

    :return: Difference in counts (standard field - LLM-generated field).
    :rtype: int
    :raises psycopg.DatabaseError: If a database error occurs.
    """
    connection = get_db_connection()
    with connection.cursor() as cur:
        table_id = sql.Identifier('applicantdata')
        lim_lit = sql.Literal(clamp_limit(MAX_ALLOWED_LIMIT))

        # Standard field check construction (Step 2)
        stmt1 = sql.SQL("""
            SELECT COUNT(*) FROM {table}
            WHERE EXTRACT(YEAR FROM date_added) = 2026 AND status = %s
                AND degree ILIKE %s AND program ILIKE %s
                AND (program ILIKE %s OR program ILIKE %s OR 
                     program ILIKE %s OR program ILIKE %s)
            LIMIT {lim};
        """).format(table=table_id, lim=lim_lit)

        params = (
            'Accepted', '%phd%', '%computer science%', '%Georgetown%',
            '%MIT%', '%Stanford%', '%Carnegie Mellon%'
        )
        cur.execute(stmt1, params)
        prog_count = cur.fetchone()[0]

        # LLM field check construction (Step 2)
        stmt2 = sql.SQL("""
            SELECT COUNT(*) FROM {table}
            WHERE EXTRACT(YEAR FROM date_added) = 2026 AND status = %s
                AND degree ILIKE %s AND llm_generated_program ILIKE %s
                AND (llm_generated_university ILIKE %s OR llm_generated_university ILIKE %s OR 
                     llm_generated_university ILIKE %s OR llm_generated_university ILIKE %s)
            LIMIT {lim};
        """).format(table=table_id, lim=lim_lit)

        cur.execute(stmt2, params)
        llm_count = cur.fetchone()[0]

    connection.close()
    return prog_count - llm_count


def get_rejected_missing_gpa():
    """
    Returns the count of rejected applicants who did not provide a GPA.

    :return: Number of rejected applicants missing GPA.
    :rtype: int
    :raises psycopg.DatabaseError: If a database error occurs.
    """
    connection = get_db_connection()
    with connection.cursor() as cur:
        stmt = sql.SQL("""
            SELECT COUNT(*) AS rejected_missing_gpa
            FROM {table}
            WHERE status = %s
                AND gpa IS NULL
            LIMIT {lim};
        """).format(
            table=sql.Identifier('applicantdata'),
            lim=sql.Literal(clamp_limit(MAX_ALLOWED_LIMIT))
        )
        cur.execute(stmt, ('Rejected',))
        result = cur.fetchone()
        count = result[0] if result else 0
    connection.close()
    return count


def get_most_apps():
    """
    Returns the university with the most accepted applicants.

    This function extracts the university name from the raw program string.
    The GROUP BY clause is synchronized with the SELECT SUBSTRING to comply
    with PostgreSQL grouping standards and prevent GroupingErrors.

    :return: Tuple containing (university_name, number_of_acceptances).
    :rtype: tuple
    :raises psycopg.DatabaseError: If a database error occurs.
    """
    connection = get_db_connection()
    with connection.cursor() as cur:
        # SQL composition with proper GROUP BY for PostgreSQL compliance
        stmt = sql.SQL("""
            SELECT 
                SUBSTRING(program FROM 1 FOR POSITION(' - ' IN program) - 1) as university,
                COUNT(*) AS num_acceptances
            FROM {table}
            WHERE status = %s
                AND program LIKE %s
            GROUP BY SUBSTRING(program FROM 1 FOR POSITION(' - ' IN program) - 1)
            ORDER BY num_acceptances DESC
            LIMIT {lim};
        """).format(
            table=sql.Identifier('applicantdata'),
            lim=sql.Literal(1) # Strict inherent limit of 1
        )
        cur.execute(stmt, ('Accepted', '% - %'))
        row = cur.fetchone()
        top_res = (row[0], row[1]) if row else (None, 0)
    connection.close()
    return top_res


def run_queries():
    """
    Runs all defined queries and returns their results in a dictionary.

    This acts as the primary data aggregator for the web application's 
    analysis view.

    :return: Dictionary containing results of all query functions.
    :rtype: dict
    """
    avg_gpa, avg_gre, avg_gre_v, avg_gre_aw = get_averages()
    top_uni, top_c = get_most_apps()
    return {
        "fall_2026_app_count": get_fall_2026_apps_count(),
        "percent_international": get_percent_international(),
        "avg_gpa": avg_gpa,
        "avg_gre": avg_gre,
        "avg_gre_v": avg_gre_v,
        "avg_gre_aw": avg_gre_aw,
        "avg_gpa_american_fall_2026": get_avg_gpa_american_fall_2026(),
        "percent_accepted_fall_2025": get_percent_accepted_fall_2025(),
        "avg_gpa_fall_2026_acceptances": get_avg_gpa_fall_2026_acceptances(),
        "jhu_cs_masters_count": get_jhu_cs_masters_count(),
        "num_entries_phd_cs_specified_schools": get_num_entries_phd_cs_specified_schools(),
        "llm_variance": get_llm_variance(),
        "rejected_missing_gpa": get_rejected_missing_gpa(),
        "top_university": top_uni,
        "top_count": top_c
    }
