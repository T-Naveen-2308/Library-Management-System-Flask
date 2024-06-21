# Library Management System - Flask

A comprehensive Library Management System built using Flask, a lightweight WSGI web application framework in Python. This system allows librarians to manage books, sections, and user accounts, and provides a platform for users to search, request, and provide feedback on books.

## Features

- User authentication and authorization (librarians and regular users)
- Book management (add, edit, delete, view details)
- Section management (add, edit, delete, view books in section)
- User account management (profile, change password, delete account)
- Search and request books
- Feedback on books
- Statistics and reports for librarians

## Technologies Used

- **Backend**: Flask, SQLite
- **Frontend**: HTML, CSS, Bootstrap
- **Libraries/Extensions**: Flask-WTF (forms), Flask-Login (user session management), Flask-SQLAlchemy (ORM)

## Installation

### Prerequisites

- Python 3.10+

### Steps

1. **Clone the repository:**

    ```sh
    git clone https://github.com/T-Naveen-2308/Library-Management-System-Flask.git
    cd Library-Management-System-Flask
    ```

2. **Create and activate a virtual environment:**

    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install the dependencies:**

    ```sh
    pip install -r requirements.txt
    ```

4. **Set up the environment variables:**

    Create a `.env` file in the root directory and add the following:

    ```env
    FLASK_DEBUG=True
    FLASK_APP=app.py
    SECRET_KEY=your_secret_key
    SQLALCHEMY_DATABASE_URI=your_db_link
    SQLALCHEMY_TRACK_MODIFICATIONS=False
    MAIL_SERVER=gmail_server
    MAIL_PORT=port
    MAIL_USE_TLS=True
    MAIL_USERNAME=your_username
    MAIL_PASSWORD=your_password

5. **Run the application:**

    ```sh
    python run.py
    ```

6. **Access the application:**

    Open your web browser and go to `http://127.0.0.1:5000`

## Project Structure

Library-Management-System-Flask/  
│  
├── instance/  
│ ├── database.sqlite3  
│  
├── library_app/  
│ ├── init.py  
│ ├── config.py  
│ ├── forms.py  
│ ├── models.py  
│ ├── utils.py  
│ ├── errors/  
│ │ ├── init.py  
│ │ ├── handlers.py  
│ │ ├── utils.py  
│ ├── librarian/  
│ │ ├── init.py  
│ │ ├── forms.py  
│ │ ├── routes.py  
│ │ ├── utils.py  
│ ├── main/  
│ │ ├── init.py  
│ │ ├── forms.py  
│ │ ├── routes.py  
│ │ ├── utils.py  
│ ├── user/  
│ │ ├── init.py  
│ │ ├── forms.py  
│ │ ├── routes.py  
│ │ ├── utils.py  
│ ├── static/  
│ │ ├── book/  
│ │ ├── librarian/  
│ │ ├── main/  
│ │ ├── user/  
│ ├── templates/  
│ │ ├── errors/  
│ │ ├── librarian/  
│ │ ├── main/  
│ │ ├── user/  
│  
├── requirements.txt  
├── run.py  
├── README.md  

## Usage

1. **Register a new user** or log in with existing credentials.
2. **Librarian Role**: 
    - Manage books and sections.
    - View and manage user requests.
    - View statistics and generate reports.
3. **User Role**:
    - Search for books.
    - Request books and provide feedback.
    - Manage personal account details.

## Acknowledgements

- Flask documentation: [https://flask.palletsprojects.com/](https://flask.palletsprojects.com/)
- Bootstrap: [https://getbootstrap.com/](https://getbootstrap.com/)
