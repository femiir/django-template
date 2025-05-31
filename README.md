# Base Django Project

This repository provides a robust Django starter project with a custom user model, role-based user management, JWT authentication, and object-level permissions using django-guardian.

## Features

- **Custom User Model:**  
  Email-based authentication with support for user roles (`Admin`, `Vendor`, `Customer`).

- **Role Proxy Models:**  
  Easily manage and query users by role using Django proxy models.

- **Profile Models:**  
  Separate profile models for each user type, extendable for custom fields.

- **JWT Authentication:**  
  Secure authentication using JSON Web Tokens (JWT), with configurable token lifetimes.

- **Object-Level Permissions:**  
  Integrated with [django-guardian](https://django-guardian.readthedocs.io/) for fine-grained access control.

- **Soft Delete & Timestamps:**  
  All models inherit from a base model providing `created_at`, `updated_at`, and soft delete functionality.

- **Admin Customization:**  
  Django admin is configured for all user types and profiles, with search and filter options.

## Project Structure

```
src/
  accounts/         # User models, managers, admin, and API endpoints
  common/           # Shared base models and custom managers
  config/           # Django settings and configuration
```

## Setup

1. **Clone the repository:**
   ```sh
   git clone <repo-url>
   cd base_django
   ```

2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   - Copy `.env.example` to `.env` and fill in your database and JWT settings.

4. **Apply migrations:**
   ```sh
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create a superuser:**
   ```sh
   python manage.py createsuperuser
   ```

6. **Run the development server:**
   ```sh
   python manage.py runserver
   ```

## Usage

- Access the Django admin at `/admin/` to manage users and profiles.
- Use the provided API endpoints for authentication and user registration.
- Extend profile models to add custom fields for each user type.

## Environment Variables

- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`
- `JWT_REFRESH_TOKEN_LIFETIME`, `JWT_ACCESS_TOKEN_LIFETIME`

## License

MIT

---

**This project is designed as a solid foundation for Django applications requiring custom user management and advanced permissions.**