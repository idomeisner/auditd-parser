## Auditd Parser


### Files
- `main.py` - The main file of the project. This file contains all the logic.
- `models.py` - This file contains the table models of the database.
- `database.py` - This file contains the database model.
- `config.py` - The file contain constants and configurations.
- `requirements.txt` - The file contain the required Python packages to run the project.
<br><br>

### Run the project

**First, create a virtual environment**

**mac**
1. `cd` to the project directory.
2. Create a virtual environment by running: `python3 -m venv venv`
3. Activate the by running: `source venv/bin/activate`
4. Install the required packages listed in requirements.txt by running: `pip3 install -r requirements.txt`

**windows**
1. `cd` to the project directory.
2. Create a virtual environment by running: `python -m venv venv`
3. Activate the by running: `venv\Scripts\activate.bat`
4. Install the required packages listed in requirements.txt by running: `pip install -r requirements.txt`

**Run the project**
1. Run the with: `python src/main.py`
<br><br>

### Note
The project won't run without a log file input.