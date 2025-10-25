import sqlite3
conn = sqlite3.connect('development/data/library.db')
cursor = conn.cursor()
cursor.execute('''
    SELECT t.id, p.name, b.title, t.due_date
    FROM transactions t
    JOIN patrons p ON t.patron_id = p.id
    JOIN books b ON t.book_id = b.id
    WHERE t.status = ?
''', ('issued',))
result = cursor.fetchall()
print(result)
conn.close()
