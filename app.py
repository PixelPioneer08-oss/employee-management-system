from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error
import hashlib

app = Flask(__name__)
app.secret_key = "your_secret_key"  # For flashing messages (consider using an environment variable in production)

# MySQL Database Configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'new_table'
}

def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as err:
        flash(f"Error connecting to database: {err}", "error")
        return None

@app.route('/')
def index():
    connection = get_db_connection()
    if connection is None:
        return render_template('index.html', employees=[])

    try:
        cursor = connection.cursor()
        cursor.execute('SELECT name, phone, role, id, dateofjoin, gender FROM employees')
        employees = cursor.fetchall()
        return render_template('index.html', employees=employees)
    except Error as err:
        flash(f"Error fetching data: {err}", "error")
        return render_template('index.html', employees=[])
    finally:
        if connection:
            cursor.close()
            connection.close()

@app.route('/add', methods=['GET', 'POST'])
def add_employee():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        role = request.form['role']
        id = request.form['id']
        dateofjoin = request.form['dateofjoin']
        gender = request.form['gender']

        # Validate inputs
        if not all([name, phone, role, id, dateofjoin, gender]):
            flash("Please fill in all fields", "error")
            return redirect(url_for('add_employee'))

        try:
            connection = get_db_connection()
            if connection is None:
                return redirect(url_for('add_employee'))

            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO employees (name, phone, role, id, dateofjoin, gender)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (name, phone, role, id, dateofjoin, gender))
            connection.commit()
            flash("Employee added successfully!", "success")
            return redirect(url_for('index'))
        except mysql.connector.Error as err:
            flash(f"Error: {err}", "error")
            return redirect(url_for('add_employee'))
        finally:
            if connection:
                cursor.close()
                connection.close()

    return render_template('employee_form.html', action='Add')  # Render the form for adding employee


@app.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete_employee(id):
    connection = get_db_connection()
    if connection is None:
        flash("Error connecting to database", "error")
        return redirect(url_for('index'))

    try:
        cursor = connection.cursor()
        cursor.execute('DELETE FROM employees WHERE id = %s', (id,))
        connection.commit()
        flash("Employee deleted successfully!", "success")
    except mysql.connector.Error as err:
        flash(f"Error: {err}", "error")
    finally:
        if connection:
            cursor.close()
            connection.close()

    return redirect(url_for('index'))

@app.route('/search', methods=['GET', 'POST'])
def search():
    connection = get_db_connection()
    if connection is None:
        return render_template('index.html', employees=[])

    try:
        cursor = connection.cursor()

        # Get search query and search criteria (field)
        search_query = request.form.get('search', '').strip()
        search_criteria = request.form.get('searchCriteria', '').strip()

        # Handle case where no search criteria is selected
        if not search_criteria:
            flash("Please select a search criteria.", "warning")
            return render_template('index.html', employees=[], search_query=search_query, search_criteria=search_criteria)

        # Build the SQL query based on the selected search criteria
        if search_query:
            query = f"""
                SELECT name, phone, role, id, dateofjoin, gender
                FROM employees
                WHERE {search_criteria} LIKE %s
            """
            cursor.execute(query, ('%' + search_query + '%',))
        else:
            cursor.execute('SELECT name, phone, role, id, dateofjoin, gender FROM employees')

        employees = cursor.fetchall()

        # Flash success message if search is successful
        if employees:
            flash(f"Search completed successfully for '{search_query}' in '{search_criteria}'", "success")
        else:
            flash(f"No results found for '{search_query}' in '{search_criteria}'", "warning")
        
        return render_template('index.html', employees=employees, search_query=search_query, search_criteria=search_criteria)
    
    except Error as err:
        flash(f"Error fetching data: {err}", "error")
        return render_template('index.html', employees=[], search_query=search_query, search_criteria=search_criteria)
    
    finally:
        if connection:
            cursor.close()
            connection.close()

@app.route('/show_all')
def show_all():
    # Get all records from the employees table
    connection = get_db_connection()
    if connection is None:
        return render_template('index.html', employees=[])

    try:
        cursor = connection.cursor()
        cursor.execute('SELECT name, phone, role, id, dateofjoin, gender FROM employees')
        employees = cursor.fetchall()

        # Flash a success message indicating the data is fetched successfully
        flash("All records displayed successfully!", "success")
        return render_template('index.html', employees=employees)
    
    except Error as err:
        flash(f"Error fetching data: {err}", "error")
        return render_template('index.html', employees=[])
    
    finally:
        if connection:
            cursor.close()
            connection.close()

@app.route('/update', methods=['GET', 'POST'])
def update_employee():
    connection = get_db_connection()
    if connection is None:
        flash("Error connecting to database", "error")
        return redirect(url_for('index'))

    try:
        if request.method == 'POST':
            id = request.form['id']
            name = request.form['name']
            phone = request.form['phone']
            role = request.form['role']
            dateofjoin = request.form['dateofjoin']
            gender = request.form['gender']

            cursor = connection.cursor()

            # Check if employee exists with the provided ID
            cursor.execute('SELECT * FROM employees WHERE id = %s', (id,))
            employee = cursor.fetchone()

            if not employee:
                flash("Employee not found", "error")
                return redirect(url_for('index'))

            # Update query
            cursor.execute("""
                UPDATE employees
                SET name = %s, phone = %s, role = %s, dateofjoin = %s, gender = %s
                WHERE id = %s
            """, (name, phone, role, dateofjoin, gender, id))
            connection.commit()
            flash("Employee updated successfully!", "success")
            return redirect(url_for('index'))

    except mysql.connector.Error as err:
        flash(f"Error: {err}", "error")
        return redirect(url_for('update_employee'))
    finally:
        if connection:
            cursor.close()
            connection.close()

    return render_template('employee.html', action='Update')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
