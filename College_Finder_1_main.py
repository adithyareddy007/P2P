from supabase import create_client

# Replace with your details
url = "https://kvbekcdyfhnpktlmcdvj.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt2YmVrY2R5ZmhucGt0bG1jZHZqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ4OTgxNjgsImV4cCI6MjA3MDQ3NDE2OH0.mKTKbxHCuNtfzd2GI3kVpqbHnwc_rleywJ2yM8NKLHM"

supabase = create_client(url, key)

import pandas as pd

# Fetch data from Supabase
response = supabase.table("College_Placements_Data").select("*").execute()

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

# 🔍 Ask user for college name
college_name = input("Enter College Name: ").strip()

# 🔎 Filter for the selected college
college_data = data[data['College Name'].str.lower() == college_name.lower()]

if college_data.empty:
    print("\n❌ College not found in the dataset.")
else:
    print(f"\n✅ College Found: {college_name}\n")

    # 📊 Year-wise Placement Percentage
    print("📊 Year-wise Placement Percentage:")
    for _, row in college_data.iterrows():
        print(f"  {row['Year']} : {row['Placement Percentage']}%")

    # 📊 Average Placement Across All Years
    average_placement_all_years = college_data['Placement Percentage'].mean()
    print(f"📊 Average Placement Percentage (2019–2023): {round(average_placement_all_years, 2)}%")

    # 💰 Salary Trends (Highest vs. Median)
    print("\n💰 Salary Trends (Highest vs Median Salary LPA):")
    for _, row in college_data.iterrows():
        print(f"  {row['Year']} : Highest - {row['Highest Package']} LPA, Median - {row['Median Salary (LPA)']} LPA")

    # 🏆 Top Recruiters (latest year)
    print("\n🏆 Top Recruiters:")
    latest_row = college_data[college_data['Year'] == college_data['Year'].max()]
    top_recruiters = latest_row['Top Recruiters'].values[0]
    if isinstance(top_recruiters, str):
        recruiters_list = top_recruiters.split(',')
        for recruiter in recruiters_list:
            print(f"  - {recruiter.strip()}")
    else:
        print("  No recruiters data available.")
