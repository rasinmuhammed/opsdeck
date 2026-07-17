# Test Application for OpsDeck

A simple test application to verify the package functionality.

## Models

- **Company**: Companies with name, industry, active status
- **Employee**: Employees with name, email, salary, linked to companies
- **Admin Users**: User management (readonly)

## Running the App

```bash
# From the test_app directory
python app.py
```

Or:

```bash
uvicorn app:app --reload --port 8001
```

## Access

- **URL**: http://localhost:8001/admin
- **Credentials**: `admin` / `admin123`

## Test Data

The app seeds with:
- 2 Companies (TechCorp, FinanceHub)
- 3 Employees
- 1 Admin user

## Features to Test

1. **List Views**: Check Companies and Employees pages
2. **Search**: Try searching employees by name/email
3. **Filters**: Filter by active status, industry, company
4. **Relationships**: Click on company in employee list (should link)
5. **Create**: Add a new company or employee
6. **Edit**: Modify existing records
7. **Delete**: Remove a record
8. **Dashboard**: View system metrics

## Cleanup

To reset the database:
```bash
rm test_app.db
```
