To run the web application, run the manage.py file. This can be done by going to the folder that the file is in and run the following cmd: "python manage.py runserver". 

## Setting Up a Python Virtual Environment (.venv)

To develop and run this project, it is recommended to use a Python virtual environment. This keeps dependencies isolated and makes setup easier for all contributors.

### Steps to Set Up .venv:

1. **Open a terminal in the project root directory**  
   (`c:\cs440_WebApp\cs440WebApp`)

2. **Create the virtual environment:**  
   ```
   python -m venv .venv
   or in vscode in search bar look up "Create Virtual Environment"
   ```

3. **Activate the virtual environment:**  
     ```
   - In terminal run:
     ```
     .venv\Scripts\Activate.ps1
     ```

4. **Install project dependencies:**  
   ```
   pip install -r requirements.txt
   ```
**Note:**  
- Always activate `.venv` before running or developing the project.

