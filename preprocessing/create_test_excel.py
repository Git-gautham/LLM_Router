from openpyxl import Workbook


workbook = Workbook()

worksheet = workbook.active
worksheet.title = "Employees"

worksheet.append([
    "Name",
    "Department",
    "Role",
    "Salary"
])

worksheet.append([
    "Arun Kumar",
    "Engineering",
    "Software Engineer",
    85000
])

worksheet.append([
    "Priya Nair",
    "Finance",
    "Analyst",
    72000
])

worksheet.append([
    "Rahul Menon",
    "Engineering",
    "Senior Engineer",
    95000
])

file_path = "preprocessing/test_employee_data.xlsx"

workbook.save(file_path)

print(f"Created: {file_path}")