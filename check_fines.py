import sqlite3

db_path = 'development/data/library.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Transactions with fines:")
cursor.execute("SELECT id, patron_id, book_id, status, fine_amount, fine_paid FROM transactions WHERE fine_amount > 0")
fines = cursor.fetchall()

for fine in fines:
    print(f"ID: {fine[0]}, Patron: {fine[1]}, Book: {fine[2]}, Status: {fine[3]}, Fine: {fine[4]}, Paid: {fine[5]}")

print(f"\nTotal fines: {len(fines)}")

conn.close()
