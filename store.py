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
                       (id INTEGER PRIMARY KEY, name TEXT UNIQUE, price REAL, number INTEGER)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS sales 
                       (id INTEGER PRIMARY KEY, product_name TEXT, number INTEGER, total_price REAL, date TEXT)""")
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
                    (name, price, number))
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
                total_price = number * product[2]
                new_number = product[3] - number
                self.update_product_number(product[0], new_number)
                self.load_products_from_db()
                today_jalali = jdatetime.date.today().strftime("%Y-%m-%d")
                conn = sqlite3.connect('products.db')
                cur = conn.cursor()
                cur.execute("INSERT INTO sales (product_name, number, total_price, date) VALUES (?, ?, ?, ?)",
                            (name, number, total_price, today_jalali))
                conn.commit()
                conn.close()
                return f"✅ مبلغ کل: {int(total_price)} تومان"
        return "❌ محصول یافت نشد."

    def update_product_number(self, product_id, new_number):
        conn = sqlite3.connect('products.db')
        cur = conn.cursor()
        cur.execute("UPDATE products SET number=? WHERE id=?", (new_number, product_id))
        conn.commit()
        conn.close()

    # ------------------ متدهای جدید ------------------

    def delete_product(self, name):
        """حذف یک محصول مشخص"""
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
        """حذف همه محصولات"""
        conn = sqlite3.connect('products.db')
        cur = conn.cursor()
        cur.execute("DELETE FROM products")
        conn.commit()
        conn.close()
        self.load_products_from_db()

    def search_products_partial(self, keyword):
        """جستجوی پیشرفته: همه محصولاتی که شامل keyword هستند"""
        self.load_products_from_db()
        result = []
        keyword_lower = keyword.lower()
        for p in self.products:
            if keyword_lower in p[1].lower():
                result.append(p)
        return result
