from flask import Flask, render_template, request, redirect, url_for, make_response
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('clinic.db')
    conn.row_factory = sqlite3.Row
    return conn

# دالة لتهيئة قاعدة البيانات بالعواميد الجديدة (status)
def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS bookings 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  name TEXT, phone TEXT, specialty TEXT, type TEXT, 
                  date TEXT, status TEXT DEFAULT 'pending')''')
    conn.execute('''CREATE TABLE IF NOT EXISTS content 
                 (id INTEGER PRIMARY KEY, hero_title TEXT, hero_desc TEXT, price INTEGER)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    # 1. التعرف على المستخدم القديم عبر الـ Cookies (رقم الموبايل)
    user_phone = request.cookies.get('user_phone')
    user_booking = None
    
    conn = get_db_connection()
    content = conn.execute('SELECT * FROM content WHERE id = 1').fetchone()
    
    if user_phone:
        user_booking = conn.execute('SELECT * FROM bookings WHERE phone = ? ORDER BY id DESC', (user_phone,)).fetchone()
    
    conn.close()
    return render_template('index.html', content=content, last_booking=user_booking)

@app.route('/book', methods=['POST'])
def book():
    name = request.form.get('name')
    phone = request.form.get('phone')
    specialty = request.form.get('specialty')
    booking_type = request.form.get('type')
    date = request.form.get('date')

    conn = get_db_connection()
    conn.execute('''INSERT INTO bookings (name, phone, specialty, type, date) 
                    VALUES (?, ?, ?, ?, ?)''', (name, phone, specialty, booking_type, date))
    conn.commit()
    conn.close()

    # 2. حفظ رقم الموبايل في الكوكيز لمدة 30 يوم عشان يفتكر حجزك
    resp = make_response(render_template('success.html'))
    resp.set_cookie('user_phone', phone, max_age=60*60*24*30)
    return resp

@app.route('/admin')
def admin():
    # 3. منطق البحث بالاسم أو الرقم
    search_query = request.args.get('search')
    conn = get_db_connection()
    
    if search_query:
        query = "SELECT * FROM bookings WHERE name LIKE ? OR phone LIKE ? ORDER BY id DESC"
        bookings = conn.execute(query, ('%'+search_query+'%', '%'+search_query+'%')).fetchall()
    else:
        bookings = conn.execute('SELECT * FROM bookings ORDER BY id DESC').fetchall()
        
    content = conn.execute('SELECT * FROM content WHERE id = 1').fetchone()
    conn.close()
    return render_template('admin.html', bookings=bookings, content=content)

# 4. مسار تأكيد الحجز (علامة الصح)
@app.route('/confirm_booking/<int:id>')
def confirm_booking(id):
    conn = get_db_connection()
    conn.execute("UPDATE bookings SET status = 'confirmed' WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

# 5. مسار حذف الحجز (علامة السلة)
@app.route('/delete_booking/<int:id>')
def delete_booking(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM bookings WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/admin/update_content', methods=['POST'])
def update_content():
    new_title = request.form.get('hero_title')
    new_desc = request.form.get('hero_desc')
    new_price = request.form.get('price')
    conn = get_db_connection()
    conn.execute('UPDATE content SET hero_title = ?, hero_desc = ?, price = ? WHERE id = 1',
                (new_title, new_desc, new_price))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)