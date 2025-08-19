from supabase import create_client

# Replace with your details
url = "https://kvbekcdyfhnpktlmcdvj.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt2YmVrY2R5ZmhucGt0bG1jZHZqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ4OTgxNjgsImV4cCI6MjA3MDQ3NDE2OH0.mKTKbxHCuNtfzd2GI3kVpqbHnwc_rleywJ2yM8NKLHM"

supabase = create_client(url, key)

import pandas as pd

# Fetch data from Supabase
response = supabase.table("College-Placements-Data").select("*").execute()

# Create DataFrame
data = pd.DataFrame(response.data)

# # Sort by College Name and Year
# data.sort_values(by=["College Name", "Year"], ascending=[True, True], inplace=True)

# Drop _id column if it exists
if "_id" in data.columns:
    data.drop("_id", axis=1, inplace=True)


constant_cols = data.groupby('College Name').nunique().max() == 1
constant_cols = constant_cols[constant_cols].index.tolist()

data['Year'] = data['Year'].astype(str).str.strip().str.split('-').str[-1] 

import pandas as pd
from collections import defaultdict

# Allowed courses
courses = ['CSE', 'ECE', 'ME', 'EEE']

# Clean salary value
def clean_salary(salary):
    try:
        salary = str(salary).replace(' LPA', '').replace('LPA', '').strip()
        return float(salary)
    except (ValueError, TypeError):
        return 0.0

# Extract recruiter list
def get_recruiters(recruiters):
    try:
        return set(str(recruiters).split(','))
    except:
        return set()

# Main processor
def process_college_data(data, location, course, top_n=5):
    overall = course.lower() == 'overall'

    if not overall and course not in courses:
        raise ValueError(f"Invalid course. Choose from: {', '.join(courses)} or 'overall'")

    data_records = data.to_dict('records')

    # Filter by location
    if location:
        location = location.lower()
        data_records = [
            record for record in data_records
            if (record.get('City', '').lower() == location or record.get('State', '').lower() == location)
        ]
        if not data_records:
            raise ValueError(f"No colleges found in location: {location}")

    # Store relevant info per college
    college_data = defaultdict(lambda: {
        'placement_pcts': [],
        'placement_trend': [],
        'salaries': [],
        'highest_packages': [],
        'recruiters': set(),
        'nirf_rank': float('inf')
    })

    for record in data_records:
        try:
            college = record['College Name']
            year = str(record['Year'])  # Year already processed as single year (e.g., '2019')
        except KeyError:
            continue

        # Compute placement percentage based on department or overall
        try:
            if overall:
                eligible = float(record.get('Total Students Eligible', 0))
                placed = float(record.get('Total Students Placed', 0))
            else:
                eligible = float(record.get(f'{course}(Eligible)', 0))
                placed = float(record.get(f'{course}(Placed)', 0))
            placement_pct = (placed / eligible) * 100 if eligible > 0 else 0
        except (ValueError, TypeError):
            placement_pct = 0

        # Add the placement percentage and trend to the college data
        college_data[college]['placement_pcts'].append(placement_pct)
        college_data[college]['placement_trend'].append((year, placement_pct))

        # Collect salary, highest package, and recruiters
        college_data[college]['salaries'].append(clean_salary(record.get('Median Salary (LPA)', 0)))
        college_data[college]['highest_packages'].append(clean_salary(record.get('Highest Package', 0)))
        college_data[college]['recruiters'].update(get_recruiters(record.get('Top Recruiters', '')))
        college_data[college]['nirf_rank'] = min(college_data[college]['nirf_rank'], float(record.get('NIRF Rank', float('inf'))))

    # Compile results
    results = []
    for college, info in college_data.items():
        avg_placement = sum(info['placement_pcts']) / len(info['placement_pcts']) if info['placement_pcts'] else 0
        avg_salary = sum(info['salaries']) / len(info['salaries']) if info['salaries'] else 0
        max_package = max(info['highest_packages']) if info['highest_packages'] else 0
        placement_trend = sorted(info['placement_trend'], key=lambda x: x[0])  # Sort by year
        recruiters = ', '.join(sorted(info['recruiters'] - {''}))[:100]

        results.append({
            'College': college,
            'Average Placement (%)': round(avg_placement, 2),
            'NIRF Rank': info['nirf_rank'],
            'Average Salary (LPA)': round(avg_salary, 2),
            'Highest Package (LPA)': round(max_package, 2),
            'Placement Trend': placement_trend,
            'Top Recruiters': recruiters
        })

    # Sort by Average Placement and NIRF Rank (lower NIRF Rank is better)
    results = sorted(results, key=lambda x: (x['Average Placement (%)'], -x['NIRF Rank']), reverse=True)
    return results[:top_n]

# Main entry function
def main():
    print("🔎 Enter preferred location (City or State, leave blank for all):")
    location = input().strip()

    print("🎓 Enter preferred course (CSE, ECE, ME, EEE or overall):")
    course = input().strip().upper()

    print("📊 How many top colleges do you want to see? (Press Enter for default 5):")
    try:
        top_n_input = input().strip()
        top_n = int(top_n_input) if top_n_input else 5
    except ValueError:
        print("❌ Invalid number, using default 5.")
        top_n = 5

    try:
        results = process_college_data(data, location, course, top_n)

        label = "Overall Placement" if course.lower() == "overall" else f"{course} Placement"
        print(f"\n🏆 Top {min(top_n, len(results))} Colleges for {label} in {location or 'All Locations'}:")
        print("-" * 85)
        print(f"{'Rank':<6} {'College':<35} {'NIRF':<6} {'Avg Placement':<15} {'Avg Salary':<12} {'Max Package':<12}")
        print("-" * 85)

        for i, college in enumerate(results, 1):
            print(f"{i:<6} {college['College'][:34]:<35} {college['NIRF Rank']:<6.0f} "
                  f"{college['Average Placement (%)']:<15.2f} {college['Average Salary (LPA)']:<12.2f} "
                  f"{college['Highest Package (LPA)']:<12.2f}")
        print("-" * 85)

        for i, college in enumerate(results, 1):
            print(f"\n📌 Details for Rank {i}: {college['College']}")
            print("📈 Placement Trend (Year → %):")
            for year, pct in college['Placement Trend']:
                print(f"  {year}: {pct:.2f}%")
            print(f"🏢 Top Recruiters: {college['Top Recruiters']}")

    except ValueError as ve:
        print(f"⚠️ {ve}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

# Run
main()