from flask import Flask, render_template, request, redirect, session, jsonify
from flask_mysqldb import MySQL
import MySQLdb.cursors

app = Flask(__name__)
app.secret_key = 'clave_secreta'

# Configuración de MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'universidad'

mysql = MySQL(app)

@app.route('/', methods=['GET', 'POST'])
def login():
    error = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM usuarios WHERE username = %s AND password = %s', (username, password))
        user = cursor.fetchone()
        if user:
            session['loggedin'] = True
            session['id'] = user['id']
            session['username'] = user['username']
            session['rol'] = user['rol']
            if user['rol'] == 'SECRETARIA':
                return redirect('/secretaria')
            else:
                return redirect('/docente')
        else:
            error = 'Usuario o contraseña incorrectos'
    return render_template('login.html', error=error)

@app.route('/secretaria')
def secretaria():
    if 'loggedin' in session and session['rol'] == 'SECRETARIA':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM aulas')
        aulas = cursor.fetchall()
        return render_template('secretaria.html', aulas=aulas)
    return redirect('/')

@app.route('/docentes')
def obtener_docentes():
    if 'loggedin' not in session or session['rol'] != 'SECRETARIA':
        return redirect('/')
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT id, nombre_completo FROM usuarios WHERE rol = 'DOCENTE'")
    docentes = cursor.fetchall()
    return jsonify(docentes)

@app.route('/docente')
def docente():
    if 'loggedin' in session and session['rol'] == 'DOCENTE':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM horarios WHERE docente_id = %s', (session['id'],))
        horarios = cursor.fetchall()
        return render_template('docente.html', horarios=horarios)
    return redirect('/')


@app.route('/registrar-docente', methods=['POST'])
def registrar_docente():
    if 'loggedin' not in session or session['rol'] != 'SECRETARIA':
        return redirect('/')
    
    id = request.form['id']
    username = request.form['username']
    password = request.form['password']
    nombre = request.form['nombre_completo']

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM usuarios WHERE id = %s OR username = %s', (id, username))
    existente = cursor.fetchone()

    if not existente:
        cursor.execute('INSERT INTO usuarios (id, username, password, nombre_completo, rol) VALUES (%s, %s, %s, %s, %s)',
                       (id, username, password, nombre, 'DOCENTE'))
        mysql.connection.commit()
    return redirect('/secretaria')

@app.route('/registrar-aula', methods=['POST'])
def registrar_aula():
    if 'loggedin' not in session or session['rol'] != 'SECRETARIA':
        return redirect('/')
    
    nombre = request.form['nombre']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM aulas WHERE nombre = %s', (nombre,))
    existente = cursor.fetchone()

    if not existente:
        cursor.execute('INSERT INTO aulas (nombre, disponible) VALUES (%s, %s)', (nombre, True))
        mysql.connection.commit()
    
    return redirect('/secretaria')

@app.route('/ver-aulas')
def ver_aulas():
    if 'loggedin' not in session:
        return redirect('/')
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT id, nombre, disponible FROM aulas')
    aulas = cursor.fetchall()
    return jsonify(aulas)

@app.route('/asignar-aula', methods=['POST'])
def asignar_aula():
    if 'loggedin' not in session or session['rol'] != 'SECRETARIA':
        return redirect('/')

    aula_id = request.form['aula_id']
    docente_id = request.form['docente_id']
    hora_inicio = request.form['hora_inicio']
    hora_fin = request.form['hora_fin']

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        INSERT INTO horarios (docente_id, aula_id, hora_inicio, hora_fin)
        VALUES (%s, %s, %s, %s)
    """, (docente_id, aula_id, hora_inicio, hora_fin))

    cursor.execute("UPDATE aulas SET disponible = 0 WHERE id = %s", (aula_id,))
    mysql.connection.commit()

    return redirect('/secretaria')


@app.route('/liberar-aula', methods=['POST'])
def liberar_aula():
    data = request.get_json()
    aula_id = data.get('aula_id')

    cursor = mysql.connection.cursor()
    cursor.execute('UPDATE aulas SET disponible = 1 WHERE id = %s', (aula_id,))
    mysql.connection.commit()

    return jsonify({'success': True})



@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
