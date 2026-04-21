import pandas as pd
from apps.recommendations.models import Course

# Load dataset
df = pd.read_csv("Online_Courses.csv")

courses = []

for _, row in df.iterrows():

    title = row.get("Title")
    url = row.get("URL")
    provider = row.get("Site")

    # Skip rows with missing required fields
    if pd.isna(title) or pd.isna(url) or pd.isna(provider):
        continue

    skills_list = []

    # Extract skills column
    skills = row.get("Skills")
    if pd.notna(skills):
        skills_list += [s.strip().lower() for s in str(skills).split(",")]

    # Add category as skill
    category = row.get("Category")
    if pd.notna(category):
        skills_list.append(category.strip().lower())

    # Add sub-category as skill
    sub_category = row.get("Sub-Category")
    if pd.notna(sub_category):
        skills_list.append(sub_category.strip().lower())

    course = Course(
        title=str(title),
        provider=str(provider),
        url=str(url),
        skills_taught=list(set(skills_list))  # remove duplicates
    )

    courses.append(course)

# Insert into database
Course.objects.bulk_create(courses, batch_size=1000)

print(f"{len(courses)} courses imported successfully!")