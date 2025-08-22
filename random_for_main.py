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
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import numpy as np

# Feature selection
features = ['NIRF Rank', 'Total Students Eligible', 'Total Students Placed',
            'CSE(Eligible)', 'CSE(Placed)', 'ECE(Eligible)', 'ECE(Placed)',
            'ME(Eligible)', 'ME(Placed)', 'EEE(Eligible)', 'EEE(Placed)']

# Target variables
target_placement = 'Placement Percentage'
target_salary = 'Median Salary (LPA)'

# Function to get user input for the college
def get_user_college_data():
    college_name = input("Enter your college name: ")

    # Filter the data for the selected college
    try:
        college_data_filtered = data[data['College Name'] == college_name].copy()
    except NameError:
        print("Error: 'data' DataFrame not defined. Please load your data.")
        return None, None, None, None

    if college_data_filtered.empty:
        print("College not found!")
        return None, None, None, None

    # Convert Year to numeric
    college_data_filtered['Year'] = college_data_filtered['Year'].astype(str).str.strip().str.split('-').str[-1].astype(int)

    # Select features and targets
    X = college_data_filtered[features]
    y_placement = college_data_filtered[target_placement]
    y_salary = college_data_filtered[target_salary].astype(str).str.replace(' LPA', '', regex=False).astype(float)
    return X, y_placement, y_salary, college_name

# Train the model and make predictions
def train_and_predict(college_data, X, y_placement, y_salary, college_name):
    # Split the data into training and testing sets
    X_train, X_test, y_train_placement, y_test_placement = train_test_split(X, y_placement, test_size=0.2, random_state=42)
    X_train_salary, X_test_salary, y_train_salary, y_test_salary = train_test_split(X, y_salary, test_size=0.2, random_state=42)

    # Scaling the data for better performance
    scaler_placement = StandardScaler()
    scaler_salary = StandardScaler()

    # Scale placement data
    X_train = scaler_placement.fit_transform(X_train)
    X_test = scaler_placement.transform(X_test)

    # Scale salary data
    X_train_salary = scaler_salary.fit_transform(X_train_salary)
    X_test_salary = scaler_salary.transform(X_test_salary)

    # Choose a model (RandomForestRegressor for both)
    model_placement = RandomForestRegressor(n_estimators=100, random_state=42)
    model_salary = RandomForestRegressor(n_estimators=100, random_state=42)

    # Train models
    model_placement.fit(X_train, y_train_placement)
    model_salary.fit(X_train_salary, y_train_salary)

    # Predict for 2024 and 2025 using the last year's data
    X_future = X.iloc[[-1]]  # Keep as DataFrame to retain feature names
    X_future_scaled_placement = scaler_placement.transform(X_future)
    X_future_scaled_salary = scaler_salary.transform(X_future)

    predicted_placement_2024 = model_placement.predict(X_future_scaled_placement)[0]
    predicted_salary_2024 = model_salary.predict(X_future_scaled_salary)[0]

    predicted_placement_2025 = predicted_placement_2024 * 1.02  # Assuming a 2% growth for 2025
    predicted_salary_2025 = predicted_salary_2024 * 1.05  # Assuming a 5% growth for 2025
    years = [2024, 2025]
    predicted_placements = [predicted_placement_2024, predicted_placement_2025]
    predicted_salaries = [predicted_salary_2024, predicted_salary_2025]
    plot_predictions(college_name, college_data, predicted_placements, predicted_salaries, years)
    print(f"\nPredicted Placement Percentage for {college_name} (2024): {predicted_placement_2024:.2f}%")
    print(f"Predicted Median Salary for {college_name} (2024): {predicted_salary_2024:.2f} LPA")
    print(f"\nPredicted Placement Percentage for {college_name} (2025): {predicted_placement_2025:.2f}%")
    print(f"Predicted Median Salary for {college_name} (2025): {predicted_salary_2025:.2f} LPA")

def plot_predictions(college_name, college_data, predicted_placements, predicted_salaries, years):
    # Filter data for the selected college
    college_data_filtered = college_data[college_data['College Name'] == college_name].copy()
    if college_data_filtered.empty:
        print(f"No data found for college: {college_name}")
        return

    # Convert Year to numeric
    college_data_filtered['Year'] = college_data_filtered['Year'].astype(str).str.strip().str.split('-').str[-1].astype(int)

    # Clean Median Salary (LPA)
    college_data_filtered['Median Salary (LPA)'] = college_data_filtered['Median Salary (LPA)'].astype(str).str.replace(' LPA', '', regex=False).astype(float)

    # Extract historical data
    historical_years = college_data_filtered['Year']
    historical_placement = college_data_filtered['Placement Percentage']
    historical_salary = college_data_filtered['Median Salary (LPA)']

    # Combine historical and predicted data
    all_years = pd.concat([pd.Series(historical_years), pd.Series(years)], ignore_index=True)
    all_placement_values = pd.concat([pd.Series(historical_placement), pd.Series(predicted_placements)], ignore_index=True)
    all_salary_values = pd.concat([pd.Series(historical_salary), pd.Series(predicted_salaries)], ignore_index=True)

    # Create subplots
    fig, axs = plt.subplots(1, 2, figsize=(15, 5))
    fig.suptitle(f'Placement and Salary Trends for {college_name}', fontsize=16)

    # Plot Placement Percentage Trend
    axs[0].plot(all_years, all_placement_values, marker='o', linestyle='-')
    axs[0].set_title('Placement Percentage Trend')
    axs[0].set_xlabel('Year')
    axs[0].set_ylabel('Placement Percentage (%)')
    axs[0].grid(True)
    axs[0].set_xticks(all_years)  # Ensure all years are on x-axis

    # Plot Median Salary Trend
    axs[1].plot(all_years, all_salary_values, marker='o', linestyle='-', color='orange')
    axs[1].set_title('Median Salary Trend')
    axs[1].set_xlabel('Year')
    axs[1].set_ylabel('Median Salary (LPA)')
    axs[1].grid(True)
    axs[1].set_xticks(all_years)

    # Adjust layout for better spacing
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])  # Make space for the title
    plt.show()

# Run the program
def main():
    X, y_placement, y_salary, college_name = get_user_college_data()
    if X is not None:
        # Train the models and predict
        train_and_predict(data, X, y_placement, y_salary, college_name)

if __name__ == "__main__":
    main()