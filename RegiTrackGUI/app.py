from flask import Flask, request, render_template, redirect, url_for
import sqlite3
import time

# 创建或连接到数据库
conn = sqlite3.connect('database.db')
cur = conn.cursor()

# 创建 stuff 和 products 表
cur.execute('''
CREATE TABLE IF NOT EXISTS stuff (
    num TEXT PRIMARY KEY,
    name TEXT,
    note TEXT
)
''')

cur.execute('''
CREATE TABLE IF NOT EXISTS products (
    num TEXT PRIMARY KEY,
    name TEXT,
    price REAL
)
''')

cur.execute('''
CREATE TABLE IF NOT EXISTS records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT DEFAULT CURRENT_DATE,
    stuff_num TEXT,
    product_num TEXT,
    quantity INTEGER,
    price REAL,
    total REAL,
    data TEXT
)
''')

conn.commit()

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stuff')
def stuff():
    conn = get_db_connection()
    stuff = conn.execute('SELECT * FROM stuff').fetchall()
    conn.close()
    return render_template('stuff.html', stuff=stuff)

@app.route('/products')
def products():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return render_template('products.html', products=products)

@app.route('/records')
def records():
    conn = get_db_connection()
    records = conn.execute('SELECT * FROM records').fetchall()
    conn.close()
    return render_template('records.html', records=records, get_stuff_name=get_stuff_name, get_product_name=get_product_name)

@app.route('/add_stuff', methods=('GET', 'POST'))
def add_stuff():
    if request.method == 'POST':
        name = request.form['name']
        note = request.form['note']
        num = generate_stuff_number()
        conn = get_db_connection()
        conn.execute('INSERT INTO stuff (num, name, note) VALUES (?, ?, ?)', (num, name, note))
        conn.commit()
        conn.close()
        return redirect(url_for('stuff'))
    return render_template('add_stuff.html')

@app.route('/add_product', methods=('GET', 'POST'))
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        num = generate_product_number()
        conn = get_db_connection()
        conn.execute('INSERT INTO products (num, name, price) VALUES (?, ?, ?)', (num, name, price))
        conn.commit()
        conn.close()
        return redirect(url_for('products'))
    return render_template('add_product.html')

@app.route('/add_record', methods=('GET', 'POST'))
def add_record():
    conn = get_db_connection()
    stuff_list = conn.execute('SELECT * FROM stuff').fetchall()
    product_list = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    
    if request.method == 'POST':
        stuff_num = request.form['stuff_num']
        product_num = request.form['product_num']

        quantity = request.form['quantity']
        date = request.form['date']
        conn = get_db_connection()
        cur = conn.execute('SELECT price FROM products WHERE num = ?', (product_num,))
        price = cur.fetchone()[0]
        total = float(quantity) * price
        conn.execute('INSERT INTO records (stuff_num,product_num, quantity, price, total, date) VALUES (?, ?, ?, ?, ?, ?)', 
                     (stuff_num, product_num ,quantity, price, total, date))
        conn.commit()
        conn.close()
        return redirect(url_for('records'))
    
    today_date = time.strftime("%Y-%m-%d")
    return render_template('add_record.html', stuff_list=stuff_list, product_list=product_list, today_date=today_date)

@app.route('/modify_product_price', methods=('GET', 'POST'))
def modify_product_price():
    if request.method == 'POST':
        product_num = request.form['product_num']
        new_price = request.form['new_price']
        conn = get_db_connection()
        conn.execute('UPDATE products SET price = ? WHERE num = ?', (new_price, product_num))
        conn.commit()
        conn.close()
        return redirect(url_for('products'))
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return render_template('modify_product_price.html', products=products)

@app.route('/delete_stuff', methods=('GET', 'POST'))
def delete_stuff():
    if request.method == 'POST':
        stuff_num = request.form['stuff_num']
        conn = get_db_connection()
        conn.execute('DELETE FROM stuff WHERE num = ?', (stuff_num,))
        conn.commit()
        conn.close()
        return redirect(url_for('stuff'))
    conn = get_db_connection()
    stuff = conn.execute('SELECT * FROM stuff').fetchall()
    conn.close()
    return render_template('delete_stuff.html', stuff=stuff)

@app.route('/delete_product', methods=('GET', 'POST'))
def delete_product():
    if request.method == 'POST':
        product_num = request.form['product_num']
        conn = get_db_connection()
        conn.execute('DELETE FROM products WHERE num = ?', (product_num,))
        conn.commit()
        conn.close()
        return redirect(url_for('products'))
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return render_template('delete_product.html', products=products)


@app.route('/modify_record/<int:record_id>', methods=('GET', 'POST'))
def modify_record(record_id):
    conn = get_db_connection()
    record = conn.execute('SELECT * FROM records WHERE id = ?', (record_id,)).fetchone()
    stuff_list = conn.execute('SELECT * FROM stuff').fetchall()
    product_list = conn.execute('SELECT * FROM products').fetchall()
    conn.close()

    if request.method == 'POST':
        # 获取表单提交的数据
        date = request.form['date']
        quantity = request.form['quantity']
        price = request.form['price']
        stuff_num = request.form['stuff_num']
        product_num = request.form['product_num']

        # 在这里处理修改记录的逻辑，更新数据库中的记录
        conn = get_db_connection()
        conn.execute('''
                     UPDATE records 
                     SET date = ?, quantity = ?, price = ?, stuff_num = ?, product_num = ? 
                     WHERE id = ?
                     ''', (date, quantity, price, stuff_num, product_num, record_id))
        conn.commit()
        conn.close()

        # 重定向到记录页面或其他适当的页面
        return redirect(url_for('records'))

    # 渲染修改记录的页面，并将记录信息和员工、产品列表传递给模板
    return render_template('modify_record.html', record=record, stuff_list=stuff_list, product_list=product_list)


def generate_stuff_number():
    conn = get_db_connection()
    cur = conn.execute("SELECT num FROM stuff ORDER BY CAST(SUBSTR(num, 3) AS INTEGER)")
    existing_nums = [int(row[0][2:]) for row in cur.fetchall()]
    conn.close()
    for i, num in enumerate(existing_nums, 1):
        if i != num:
            return f'ST{str(i).zfill(3)}'
    return f'ST{str(len(existing_nums) + 1).zfill(3)}'

def generate_product_number():
    conn = get_db_connection()
    cur = conn.execute("SELECT num FROM products ORDER BY CAST(SUBSTR(num, 3) AS INTEGER)")
    existing_nums = [int(row[0][2:]) for row in cur.fetchall()]
    conn.close()
    for i, num in enumerate(existing_nums, 1):
        if i != num:
            return f'PR{str(i).zfill(3)}'
    return f'PR{str(len(existing_nums) + 1).zfill(3)}'



def get_stuff_name(stuff_num):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT name FROM stuff WHERE num = ?', (stuff_num,))
    result = cur.fetchone()
    conn.close()
    return result[0] if result else 'N/A'

def get_product_name(product_num):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT name FROM products WHERE num = ?', (product_num,))
    result = cur.fetchone()
    conn.close()
    return result[0] if result else 'N/A'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)