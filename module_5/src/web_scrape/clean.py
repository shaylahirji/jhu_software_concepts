"""
This module contains functions to clean and structure raw applicant data from web scraping.

This module prepares data for secure database insertion. While it does not perform 
SQL queries directly, it ensures data integrity and type safety before the loading 
phase. By enforcing strict regex patterns, it acts as a primary sanitization layer 
to prevent malformed data from reaching the database composition layer (Step 2).
"""
import json
import re

# add regex helper functions here


def extract_decision_and_date(decision):
    """
    Extract the applicant decision status and date from a decision string.

    :param decision: The raw decision text containing decision status and date.
    :type decision: str
    :return: A tuple containing the decision status and date.
    :rtype: tuple[str or None, str or None]
    """
    accept = re.search(r"\b(Accepted)\s+on\s+(\d{1,2}\s+[A-Za-z]{3}(?:\s+\d{4})?)", decision)
    reject = re.search(r"\b(Rejected)\s+on\s+(\d{1,2}\s+[A-Za-z]{3}(?:\s+\d{4})?)", decision)
    waitlist = re.search(r"\b(Wait\s?listed)\s+on\s+(\d{1,2}\s+[A-Za-z]{3}(?:\s+\d{4})?)", decision)
    interview = re.search(r"\b(Interview)\s+on\s+(\d{1,2}\s+[A-Za-z]{3}(?:\s+\d{4})?)", decision)
    withdrawn = re.search(r"\b(Withdrawn)\s+on\s+(\d{1,2}\s+[A-Za-z]{3}(?:\s+\d{4})?)", decision)

    if accept:
        return accept.group(1), accept.group(2)
    if reject:
        return reject.group(1), reject.group(2)
    if waitlist:
        return waitlist.group(1), waitlist.group(2)
    if interview:
        return interview.group(1), interview.group(2)
    if withdrawn:
        return withdrawn.group(1), withdrawn.group(2)

    return None, None


def extract_comments(text):
    """
    Extract applicant comments from the text field, removing GPA references.

    :param text: The raw applicant text containing program and comment information.
    :type text: str
    :return: Cleaned comment string if found, otherwise None.
    :rtype: str or None
    """
    pattern = r"(?:Fall|Spring|Summer|Winter)\s\d{4}\s(?:International|American)\s*(.*)"
    comments = re.search(pattern, text, re.DOTALL)
    if comments:
        comment = comments.group(1).strip()
        if comment:
            # Remove GPA from the comment if it exists
            comment = re.sub(r"GPA \d\.\d+", "", comment).strip()
            return comment if comment else None
    return None


def extract_program_start(text):
    """
    Extract the program start term (e.g., Fall 2026) from text.

    :param text: The raw applicant text containing term information.
    :type text: str
    :return: Program start term if found, otherwise None.
    :rtype: str or None
    """
    program_start = re.search(r"(Fall|Spring|Summer|Winter)\s\d{4}", text)
    if program_start:
        return program_start.group(0)

    return None


def extract_citizenship(text):
    """
    Extract the applicant citizenship status (American or International).

    :param text: The raw applicant text containing citizenship information.
    :type text: str
    :return: Citizenship status capitalized if found, otherwise None.
    :rtype: str or None
    """
    citizenship = re.search(r"\b(International|American)\b", text, re.IGNORECASE)
    if citizenship:
        return citizenship.group(1).capitalize()

    return None


def extract_gre_score(text):
    """
    Extract the overall GRE score from text.

    :param text: The raw applicant text containing GRE information.
    :type text: str
    :return: The first GRE score found as an integer, otherwise None.
    :rtype: int or None
    """
    scores = re.findall(r"GRE(?:\s[VQAWR]*)?\s(\d+)", text)
    return int(scores[0]) if scores else None


def extract_gre_v_score(text):
    """
    Extract the GRE Verbal (V) score from text.

    :param text: The raw applicant text containing GRE verbal score information.
    :type text: str
    :return: GRE Verbal score as an integer if found, otherwise None.
    :rtype: int or None
    """
    gre_v = re.search(r"GRE V (\d+)", text)
    if gre_v:
        return int(gre_v.group(1))
    return None


def extract_degree_type(text):
    """
    Extract the degree type (Masters, PhD, MFA, PsyD) from text.

    :param text: The raw applicant text containing degree information.
    :type text: str
    :return: Degree type if found, otherwise None.
    :rtype: str or None
    """
    degree = re.search(r"\b(Masters|PhD|MFA|PsyD)\b", text, re.IGNORECASE)
    if degree:
        return degree.group(1)
    return None


def extract_gpa(text):
    """
    Extract the GPA value from text.

    :param text: The raw applicant text containing GPA information.
    :type text: str
    :return: GPA as a float if found, otherwise None.
    :rtype: float or None
    """
    gpa = re.search(r"GPA (\d\.\d+)", text)
    if gpa:
        return float(gpa.group(1))
    return None


def extract_gre_aw(text):
    """
    Extract the GRE Analytical Writing (AW) score from text.

    :param text: The raw applicant text containing GRE AW information.
    :type text: str
    :return: GRE AW score as a float if found, otherwise None.
    :rtype: float or None
    """
    gre_aw = re.search(r"GRE AW (\d+(\.\d+)?)", text)
    if gre_aw:
        return float(gre_aw.group(1))
    return None


def clean_data(raw_data):
    """
    Clean and structure raw applicant data into a list of dictionaries.

    :param raw_data: Dictionary of raw applicant entries loaded from JSON.
    :type raw_data: dict
    :return: List of cleaned applicant dictionaries.
    :rtype: list[dict]
    """
    cleaned_list = []

    for entry in raw_data.values():
        text = entry.get("text", "")
        decision_text = entry.get("decision", "")

        decision, decision_date = extract_decision_and_date(decision_text)

        cleaned_entry = {
            "Program Name": entry.get("program"),
            "University": entry.get("university"),
            "Comments": extract_comments(text),
            "date_added": entry.get("date_added"),
            "URL": entry.get("url"),
            "Applicant Status": decision,
            "Decision Date": decision_date,
            "Program Start Date": extract_program_start(text),
            "Citizenship": extract_citizenship(text),
            "GRE Score": extract_gre_score(text),
            "GRE V Score": extract_gre_v_score(text),
            "Degree Program": extract_degree_type(text),
            "GPA": extract_gpa(text),
            "GRE AW": extract_gre_aw(text)
        }

        cleaned_list.append(cleaned_entry)
    return cleaned_list


def load_data():
    """
    Load raw JSON data, clean it, and save the structured output.

    This fulfills Step 3 Hardening by ensuring raw scraped data is 
    stored in a structured JSON format before insertion via restricted roles.

    :return: List of cleaned applicant dictionaries.
    :rtype: list[dict]
    """
    with open("raw_data/raw.json", "r", encoding="utf-8") as file:
        raw_data = json.load(file)

    cleaned_results = clean_data(raw_data)

    with open("raw_data/applicant_data.json", "w", encoding="utf-8") as file:
        json.dump(cleaned_results, file, indent=4)

    return cleaned_results
