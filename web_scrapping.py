import os
from bs4 import BeautifulSoup
import pandas as pd

# Path to your HTML file
html_file_path = 'internshala.html'

# Read the HTML file
try:
    with open(html_file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()
except FileNotFoundError:
    print(f"Error: The file {html_file_path} was not found.")
    exit()
except Exception as e:
    print(f"Error reading the file: {e}")
    exit()

soup = BeautifulSoup(html_content, 'html.parser')

# Find all internship listings
internship_listings = soup.find_all('div', class_='individual_internship')

# Initialize list to store data
internships = []

for listing in internship_listings:
    try:
        # Extract position title
        title = listing.find('a', class_='job-title-href')
        title = title.text.strip() if title else 'N/A'
        
        # Extract company name
        company = listing.find('div', class_='company_name').find('p', class_='company-name')
        company = company.text.strip() if company else 'N/A'
        
        # Extract location
        location_div = listing.find('div', class_='locations')
        location = location_div.find('a').text.strip() if location_div and location_div.find('a') else 'N/A'
        
        # Check work mode (On-site/Hybrid/Remote)
        work_mode = 'On-site'
        if location_div:
            location_text = location_div.text
            if 'Hybrid' in location_text:
                work_mode = 'Hybrid'
            elif 'Work from Home' in location_text or 'Remote' in location_text:
                work_mode ='Remote'
        
        # Extract stipend
        stipend = listing.find('span', class_='stipend')
        stipend = stipend.text.strip() if stipend else 'N/A'
        
        # Extract duration
        duration_items = listing.find_all('div', class_='row-1-item')
        duration = 'N/A'
        for item in duration_items:
            if 'calendar' in str(item):  # Look for the calendar icon
                duration = item.find('span').text.strip() if item.find('span') else 'N/A'
                break
        
        # Extract posted date
        posted = (listing.find('div', class_='status-success') or 
                 listing.find('div', class_='status-inactive') or 
                 listing.find('div', class_='status-info'))
        posted = posted.text.strip() if posted else 'N/A'
        
        # Check if actively hiring
        actively_hiring = bool(listing.find('div', class_='actively-hiring-badge'))
        
        # Check if early applicant
        early_applicant = bool(listing.find('div', class_='early_applicant_wrapper'))
        
        # Check if has job offer
        job_offer = listing.find('div', class_='ppo_status')
        job_offer = job_offer.text.strip() if job_offer else 'No'
        
        # Add to list
        internships.append({
            'Title': title,
            'Company': company,
            'Location': location,
            'Work Mode': work_mode,
            'Stipend': stipend,
            'Duration': duration,
            'Posted': posted,
            'Actively Hiring': actively_hiring,
            'Early Applicant': early_applicant,
            'Job Offer Possible': job_offer
        })
    except Exception as e:
        print(f"Error processing listing: {e}")
        continue

# Create DataFrame
if internships:
    df = pd.DataFrame(internships)
    
    # Save to CSV in the same directory as the HTML file
    output_path = os.path.join(os.path.dirname(html_file_path), 'internshala_internships.csv')
    df.to_csv(output_path, index=False)
    print(f"Data successfully saved to {output_path}")
    
    # Display sample data
    print("\nFirst 5 internships:")
    print(df.head())
else:
    print("No internship listings found in the HTML file.")