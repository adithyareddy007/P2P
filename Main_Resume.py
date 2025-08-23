import re
import os
import sys
import PyPDF2
import docx
import spacy
import nltk
from supabase import create_client, Client

# --- ⚠️ IMPORTANT: CONFIGURE YOUR SUPABASE CLIENT HERE ---
# Replace "" with your actual Supabase URL and anon key.
SUPABASE_URL: str = "https://kvbekcdyfhnpktlmcdvj.supabase.co"
SUPABASE_KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt2YmVrY2R5ZmhucGt0bG1jZHZqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ4OTgxNjgsImV4cCI6MjA3MDQ3NDE2OH0.mKTKbxHCuNtfzd2GI3kVpqbHnwc_rleywJ2yM8NKLHM"

# --- Setup and Configuration ---

# Download NLTK stopwords if not already available
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    print("Downloading NLTK stopwords...")
    nltk.download('stopwords')

# Load English language model for spaCy
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("spaCy English model not found. Please run:")
    print("python -m spacy download en_core_web_sm")
    nlp = None

# --- Supabase Function ---

def fetch_job_roles_from_supabase(url: str, key: str):
    """
    Fetches job roles, skills, and course recommendations from the Supabase database.
    """
    if not url or not key:
        print(" Error: Supabase URL and Key are not set. Please edit the script and add them.")
        return None

    try:
        supabase: Client = create_client(url, key)
        # Fetch all necessary columns from the 'job_roles' table
        response = supabase.table('job_roles').select(
            'role_name, skills, course_recommendations'
        ).execute()
        
        if not response.data:
            print(" Error: No data received from the 'job_roles' table. Is it empty?")
            return None

        # Transform the data into the required dictionary format
        job_roles_data = {}
        for item in response.data:
            role_name = item.get('role_name')
            skills = item.get('skills', [])
            courses = item.get('course_recommendations', [])
            
            if role_name and skills:
                # Create a direct mapping from a skill to its recommended course
                # This assumes the 'skills' and 'course_recommendations' arrays are parallel
                skill_to_course_map = {skill: course for skill, course in zip(skills, courses)}

                job_roles_data[role_name] = {
                    "all_skills": skills,
                    "recommendations": skill_to_course_map
                }        
        return job_roles_data

    except Exception as e:
        print(f" Database Error: Could not connect to Supabase or fetch data. Details: {e}")
        return None

# --- Core Functions ---

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error reading PDF file: {e}")
        return None
    return text

def extract_text_from_docx(docx_path):
    """Extract text from a DOCX file."""
    text = ""
    try:
        document = docx.Document(docx_path)
        for para in document.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        print(f"Error reading DOCX file: {e}")
        return None
    return text
    
def extract_text_from_file(file_path):
    """Extract text from PDF or DOCX file based on extension."""
    clean_path = file_path.strip().strip("'\"")
    if not os.path.exists(clean_path):
        print(f"Error: File not found at '{clean_path}'")
        return None
    _, file_extension = os.path.splitext(clean_path)
    if file_extension.lower() == '.pdf':
        return extract_text_from_pdf(clean_path)
    elif file_extension.lower() == '.docx':
        return extract_text_from_docx(clean_path)
    else:
        print(f"Error: Unsupported file type '{file_extension}'. Please use a .pdf or .docx file.")
        return None

def extract_skills(text, job_role, job_roles_data):
    """Extract skills from text using keyword matching and NLP."""
    skills_found = set()
    text_lower = text.lower()
    
    all_possible_skills = job_roles_data[job_role]["all_skills"]
    
    for skill in all_possible_skills:
        if re.search(r'\b' + re.escape(skill.lower()) + r'\b', text_lower):
            skills_found.add(skill)
            
    if nlp:
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ in ["ORG", "PRODUCT"]:
                for skill in all_possible_skills:
                    if skill.lower() in ent.text.lower():
                        skills_found.add(skill)

    return sorted(list(skills_found))

def calculate_score(skills_found, job_role, job_roles_data):
    """Calculate resume score as a simple percentage of matched skills."""
    all_skills_for_role = set(job_roles_data[job_role]["all_skills"])
    found_set = set(skills_found)
    
    matches = len(found_set.intersection(all_skills_for_role))
    total_skills = len(all_skills_for_role)
    
    score = round((matches / total_skills) * 100, 1) if total_skills > 0 else 0
    
    return score, matches, total_skills

def identify_skill_gaps(skills_found, job_role, job_roles_data):
    """Identify missing skills."""
    all_skills_for_role = set(job_roles_data[job_role]["all_skills"])
    found_set = set(skills_found)
    return sorted(list(all_skills_for_role - found_set))

def recommend_courses(skill_gaps, job_role, job_roles_data):
    """Recommend courses for missing skills from the database data."""
    recommendations_map = job_roles_data[job_role]['recommendations']
    return [
        {"skill": skill, "course": recommendations_map.get(skill)}
        for skill in skill_gaps if recommendations_map.get(skill)
    ]

def analyze_resume(text, job_role, job_roles_data):
    """Main function to orchestrate the resume analysis."""
    skills_found = extract_skills(text, job_role, job_roles_data)
    score, matches, total = calculate_score(skills_found, job_role, job_roles_data)
    skill_gaps = identify_skill_gaps(skills_found, job_role, job_roles_data)
    courses = recommend_courses(skill_gaps, job_role, job_roles_data)
    
    return {
        "score": score,
        "skills_found": skills_found,
        "skill_gaps": skill_gaps,
        "course_recommendations": courses,
        "skill_stats": {
            "matches": matches, 
            "total_skills": total,
        },
        "job_role": job_role.replace("_", " ").title()
    }

def display_results(results):
    """Prints the analysis results in a readable format."""
    print("\n" + "="*50)
    print("        RESUME ANALYSIS REPORT ")
    print("="*50)
    
    print(f"\nAnalyzed for Job Role: {results['job_role']}")
    print(f" Overall Match Score: {results['score']}%")
    
    print("\n--- Skill Summary ---")
    stats = results['skill_stats']
    print(f"Skills Found: {stats['matches']} / {stats['total_skills']}")
    
    print("\n--- Skills Found in Your Resume ---")
    if results['skills_found']:
        print(", ".join(results['skills_found']))
    else:
        print("No relevant skills found for this role.")
        
    print("\n---  Skill Gaps ---")
    if results['skill_gaps']:
        for skill in results['skill_gaps']:
            print(f"- {skill}")
    else:
        print(" Great job! No skill gaps found.")

    print("\n---  Course Recommendations to Fill Gaps ---")
    if results['course_recommendations']:
        for rec in results['course_recommendations']:
            print(f"- To learn {rec['skill']}:")
            print(f"   {rec['course']}")
    elif not results['skill_gaps']:
         print("You've covered all the required skills!")
    else:
        print("No specific course recommendations available for the identified gaps.")
        
    print("\n" + "="*50 + "\n")


# --- Main Execution Block ---

def main():
    """Gets user input interactively and runs the analysis."""
    if nlp is None:
        sys.exit(1)

    # --- 1. Fetch Job Roles from Supabase ---
    job_roles_data = fetch_job_roles_from_supabase(SUPABASE_URL, SUPABASE_KEY)
    if not job_roles_data:
        print("Aborting analysis due to database issues.")
        sys.exit(1)

    # --- 2. Get Resume Path from User ---
    resume_path = input(" Please enter the full path to your resume file (PDF or DOCX): ").strip()

    # --- 3. Get Job Role from User ---
    print("\nAvailable job roles" \
    ":")
    available_roles = list(job_roles_data.keys())
    for i, role in enumerate(available_roles, 1):
        print(f"  {i}. {role.replace('_', ' ').title()}")

    job_role = ""
    while not job_role:
        choice = input(f"\n Choose a job role (enter the number or name): ").strip()
        
        if choice.isdigit() and 1 <= int(choice) <= len(available_roles):
            job_role = available_roles[int(choice) - 1]
        elif choice.lower().replace(" ", "_") in available_roles:
            job_role = choice.lower().replace(" ", "_")
        else:
            print(f" Invalid choice. Please enter a number from the list or a valid role name.")

    # --- 4. Run the Analysis ---
    print(f"\nAnalyzing resume '{os.path.basename(resume_path)}' for the '{job_role}' role...")
    
    resume_text = extract_text_from_file(resume_path)
    
    if not resume_text:
        print("Could not extract text. Aborting analysis.")
        sys.exit(1)
        
    analysis_results = analyze_resume(resume_text, job_role, job_roles_data)
    display_results(analysis_results)


if __name__ == "__main__":
    main()
