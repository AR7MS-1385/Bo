import sqlite3
import jdatetime

class Store:
    def __init__(self):
        self.products = []
        self.total_sales = 0
        self.init_db()
        self.load_products_from_db()

    def init_db(self):
        conn = sqlite3.connect('products.db')
        cur = conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS products 
                       (id INTEGER PRIMARY KEY, name TEXT UNIQUE, price INTEGER, number INTEGER)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS sales 
                       (id INTEGER PRIMARY KEY, product_name TEXT, number INTEGER, total_price INTEGER, date TEXT)""")
        conn.commit()
        conn.close()

    def load_products_from_db(self):
        conn = sqlite3.connect('products.db')
        cur = conn.cursor()
        cur.execute("SELECT * FROM products")
        self.products = cur.fetchall()
        conn.close()

    def add_product(self, name, price, number):
        for product in self.products:
            if product[1] == name:
                return False
        conn = sqlite3.connect('products.db')
        cur = conn.cursor()
        cur.execute("INSERT INTO products (name, price, number) VALUES (?, ?, ?)",
                    (name, int(price), int(number)))
        conn.commit()
        conn.close()
        self.load_products_from_db()
        return True

    def sell_product(self, name, number):
        self.load_products_from_db()
        for product in self.products:
            if product[1] == name:
                if product[3] < number:
                    return "❌ تعداد محصول کافی نیست."
                total_price = int(number * int(product[2]))
                new_number = product[3] - number
                self.update_product_number(product[0], new_number)
                self.load_products_from_db()

                # تاریخ شمسی با فرمت dd-mm-yyyy
                today_jalali = jdatetime.date.today().strftime("%d-%m-%Y")

                conn = sqlite3.connect('products.db')
                cur = conn.cursor()
                cur.execute("INSERT INTO sales (product_name, number, total_price, date) VALUES (?, ?, ?, ?)",
                            (name, number, total_price, today_jalali))
                conn.commit()
                conn.close()
                return f"✅ مبلغ کل: {total_price} تومان"
        return "❌ محصول یافت نشد."

    def update_product_number(self, product_id, new_number):
        conn = sqlite3.connect('products.db')
        cur = conn.cursor()
        cur.execute("UPDATE products SET number=? WHERE id=?", (new_number, product_id))
        conn.commit()
        conn.close()

    def delete_product(self, name):
        self.load_products_from_db()
        for product in self.products:
            if product[1] == name:
                conn = sqlite3.connect('products.db')
                cur = conn.cursor()
                cur.execute("DELETE FROM products WHERE id=?", (product[0],))
                conn.commit()
                conn.close()
                self.load_products_from_db()
                return True
        return False

    def delete_all_products(self):
        conn = sqlite3.connect('products.db')
        cur = conn.cursor()
        cur.execute("DELETE FROM products")
        conn.commit()
        conn.close()
        self.load_products_from_db()

    def search_products_partial(self, keyword):
        self.load_products_from_db()
        result = []
        keyword_lower = keyword.lower()
        for p in self.products:
            if keyword_lower in p[1].lower():
                result.append(p)
        return result

    def get_low_stock(self):
        self.load_products_from_db()
        return [p for p in self.products if p[3] <= 1]

    def edit_product(self, old_name, field, new_value):
        self.load_products_from_db()
        for product in self.products:
            if product[1] == old_name:
                conn = sqlite3.connect('products.db')
                cur = conn.cursor()
                if field == "name":
                    cur.execute("UPDATE products SET name=? WHERE id=?", (new_value, product[0]))
                elif field == "price":
                    cur.execute("UPDATE products SET price=? WHERE id=?", (int(new_value), product[0]))
                elif field == "number":
                    cur.execute("UPDATE products SET number=? WHERE id=?", (int(new_value), product[0]))
                conn.commit()
                conn.close()
                self.load_products_from_db()
                return True
        return False

    def get_sales_report(self, start_date, end_date):
        conn = sqlite3.connect('products.db')
        cur = conn.cursor()
        cur.execute("SELECT * FROM sales WHERE date BETWEEN ? AND ?", (start_date, end_date))
        sales = cur.fetchall()
        conn.close()
        return sales
