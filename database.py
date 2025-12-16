"""
=====================================================
DATABASE.PY - Modul Database untuk Inventory Dashboard
=====================================================

File ini berisi semua fungsi yang berhubungan dengan database SQLite.
Termasuk: koneksi database, pembuatan tabel, CRUD operations, dan
generator data dummy.

Author: [Nama Anda]
Portfolio Project: Sales & Inventory Intelligence Dashboard
=====================================================
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import random

# =====================================================
# KONFIGURASI DATABASE
# =====================================================

# Nama file database SQLite yang akan digunakan
DATABASE_NAME = "inventory.db"


def get_connection():
    """
    Membuat koneksi ke database SQLite.

    SQLite adalah database ringan yang menyimpan data dalam satu file.
    Cocok untuk aplikasi kecil-menengah dan prototipe.

    Returns:
        sqlite3.Connection: Object koneksi ke database

    Contoh penggunaan:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products")
    """
    # Membuat koneksi ke file database
    # Jika file belum ada, SQLite akan otomatis membuatnya
    conn = sqlite3.connect(DATABASE_NAME)
    return conn


def create_tables():
    """
    Membuat tabel-tabel yang dibutuhkan jika belum ada.

    Tabel yang dibuat:
    1. products - Menyimpan data produk/barang
    2. transactions - Menyimpan data transaksi penjualan

    Menggunakan 'IF NOT EXISTS' agar tidak error jika tabel sudah ada.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # =========================================
    # TABEL PRODUCTS (Produk/Barang)
    # =========================================
    # - id: Primary key, auto increment
    # - name: Nama produk
    # - category: Kategori produk (Elektronik, Makanan, dll)
    # - price: Harga jual ke customer
    # - cost: Harga modal/beli dari supplier
    # - stock: Jumlah stok tersedia
    # - created_at: Waktu produk ditambahkan
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            cost REAL NOT NULL,
            stock INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # =========================================
    # TABEL TRANSACTIONS (Transaksi Penjualan)
    # =========================================
    # - id: Primary key, auto increment
    # - product_id: Foreign key ke tabel products
    # - quantity: Jumlah barang yang dijual
    # - total_price: Total harga penjualan (price x quantity)
    # - profit: Keuntungan ((price - cost) x quantity)
    # - transaction_date: Waktu transaksi
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            total_price REAL NOT NULL,
            profit REAL NOT NULL,
            transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    # Commit perubahan dan tutup koneksi
    conn.commit()
    conn.close()


# =====================================================
# CRUD OPERATIONS - PRODUCTS
# =====================================================


def add_product(name, category, price, cost, stock):
    """
    Menambahkan produk baru ke database.

    Args:
        name (str): Nama produk
        category (str): Kategori produk
        price (float): Harga jual
        cost (float): Harga modal
        stock (int): Jumlah stok awal

    Returns:
        int: ID produk yang baru ditambahkan

    Contoh:
        product_id = add_product("Laptop Asus", "Elektronik", 8000000, 7000000, 10)
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Menggunakan parameterized query (?) untuk mencegah SQL Injection
    # SQL Injection adalah teknik hacking yang memasukkan kode SQL berbahaya
    cursor.execute(
        """
        INSERT INTO products (name, category, price, cost, stock)
        VALUES (?, ?, ?, ?, ?)
    """,
        (name, category, price, cost, stock),
    )

    # Mendapatkan ID dari row yang baru diinsert
    product_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return product_id


def get_products():
    """
    Mengambil semua produk dari database.

    Menggunakan pandas read_sql_query untuk langsung mengkonversi
    hasil query ke DataFrame, memudahkan manipulasi data.

    Returns:
        pandas.DataFrame: DataFrame berisi semua produk
    """
    conn = get_connection()

    # pd.read_sql_query langsung mengembalikan DataFrame
    # Lebih praktis daripada fetch manual
    df = pd.read_sql_query("SELECT * FROM products ORDER BY id", conn)

    conn.close()
    return df


def update_stock(product_id, quantity_sold):
    """
    Mengurangi stok produk setelah penjualan.

    Args:
        product_id (int): ID produk yang stoknya akan dikurangi
        quantity_sold (int): Jumlah barang yang terjual

    Returns:
        bool: True jika berhasil, False jika stok tidak mencukupi
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Cek stok saat ini
    cursor.execute("SELECT stock FROM products WHERE id = ?", (product_id,))
    result = cursor.fetchone()

    if result is None:
        conn.close()
        return False

    current_stock = result[0]

    # Validasi: pastikan stok mencukupi
    if current_stock < quantity_sold:
        conn.close()
        return False

    # Update stok (kurangi dengan jumlah yang terjual)
    new_stock = current_stock - quantity_sold
    cursor.execute(
        """
        UPDATE products SET stock = ? WHERE id = ?
    """,
        (new_stock, product_id),
    )

    conn.commit()
    conn.close()

    return True


def get_product_by_id(product_id):
    """
    Mengambil detail produk berdasarkan ID.

    Args:
        product_id (int): ID produk yang dicari

    Returns:
        dict: Dictionary berisi detail produk, atau None jika tidak ditemukan
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    result = cursor.fetchone()

    conn.close()

    if result:
        # Mengkonversi tuple ke dictionary untuk kemudahan akses
        return {
            "id": result[0],
            "name": result[1],
            "category": result[2],
            "price": result[3],
            "cost": result[4],
            "stock": result[5],
            "created_at": result[6],
        }
    return None


def restock_product(product_id, quantity_to_add):
    """
    Menambah stok produk (restock/restocking).

    Berbeda dengan update_stock yang mengurangi stok,
    fungsi ini untuk menambah stok dari supplier.

    Args:
        product_id (int): ID produk yang akan di-restock
        quantity_to_add (int): Jumlah stok yang ditambahkan

    Returns:
        bool: True jika berhasil, False jika produk tidak ditemukan

    Contoh:
        restock_product(1, 50)  # Tambah 50 unit ke produk ID 1
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Cek apakah produk ada
    cursor.execute("SELECT stock FROM products WHERE id = ?", (product_id,))
    result = cursor.fetchone()

    if result is None:
        conn.close()
        return False

    current_stock = result[0]

    # Tambah stok baru
    new_stock = current_stock + quantity_to_add
    cursor.execute(
        """
        UPDATE products SET stock = ? WHERE id = ?
    """,
        (new_stock, product_id),
    )

    conn.commit()
    conn.close()

    return True


def get_categories():
    """
    Mengambil daftar semua kategori yang ada di database.

    Returns:
        list: List berisi nama-nama kategori unik
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT category FROM products ORDER BY category")
    results = cursor.fetchall()

    conn.close()

    # Konversi list of tuples ke list of strings
    return [row[0] for row in results]


def update_product(
    product_id, name=None, category=None, price=None, cost=None, stock=None
):
    """
    Mengupdate informasi produk.

    Args:
        product_id (int): ID produk yang akan diupdate
        name (str, optional): Nama produk baru
        category (str, optional): Kategori baru
        price (float, optional): Harga jual baru
        cost (float, optional): Harga modal baru
        stock (int, optional): Stok baru

    Returns:
        bool: True jika berhasil
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Ambil data produk saat ini
    product = get_product_by_id(product_id)
    if not product:
        conn.close()
        return False

    # Gunakan nilai baru atau nilai lama jika tidak diupdate
    new_name = name if name is not None else product["name"]
    new_category = category if category is not None else product["category"]
    new_price = price if price is not None else product["price"]
    new_cost = cost if cost is not None else product["cost"]
    new_stock = stock if stock is not None else product["stock"]

    cursor.execute(
        """
        UPDATE products 
        SET name = ?, category = ?, price = ?, cost = ?, stock = ?
        WHERE id = ?
    """,
        (new_name, new_category, new_price, new_cost, new_stock, product_id),
    )

    conn.commit()
    conn.close()

    return True


def delete_product(product_id):
    """
    Menghapus produk dari database.

    PERHATIAN: Fungsi ini juga akan menghapus semua transaksi
    yang terkait dengan produk ini untuk menjaga integritas data.

    Args:
        product_id (int): ID produk yang akan dihapus

    Returns:
        bool: True jika berhasil, False jika produk tidak ditemukan

    Contoh:
        delete_product(5)  # Hapus produk dengan ID 5
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Cek apakah produk ada
    cursor.execute("SELECT id FROM products WHERE id = ?", (product_id,))
    result = cursor.fetchone()

    if result is None:
        conn.close()
        return False

    # Hapus transaksi terkait terlebih dahulu (karena foreign key)
    cursor.execute("DELETE FROM transactions WHERE product_id = ?", (product_id,))

    # Hapus produk
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))

    conn.commit()
    conn.close()

    return True


# =====================================================
# CRUD OPERATIONS - TRANSACTIONS
# =====================================================


def add_transaction(product_id, quantity, total_price, profit):
    """
    Mencatat transaksi penjualan baru ke database.

    Args:
        product_id (int): ID produk yang dijual
        quantity (int): Jumlah barang terjual
        total_price (float): Total harga penjualan
        profit (float): Keuntungan dari transaksi

    Returns:
        int: ID transaksi yang baru dibuat
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO transactions (product_id, quantity, total_price, profit)
        VALUES (?, ?, ?, ?)
    """,
        (product_id, quantity, total_price, profit),
    )

    transaction_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return transaction_id


def add_transaction_with_date(
    product_id, quantity, total_price, profit, transaction_date
):
    """
    Mencatat transaksi dengan tanggal custom (untuk dummy data).

    Sama seperti add_transaction, tapi bisa menentukan tanggal sendiri.
    Digunakan untuk generate data historis.

    Args:
        product_id (int): ID produk
        quantity (int): Jumlah terjual
        total_price (float): Total harga
        profit (float): Keuntungan
        transaction_date (datetime): Tanggal transaksi
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO transactions (product_id, quantity, total_price, profit, transaction_date)
        VALUES (?, ?, ?, ?, ?)
    """,
        (product_id, quantity, total_price, profit, transaction_date),
    )

    conn.commit()
    conn.close()


def get_transactions(days=7):
    """
    Mengambil transaksi dalam N hari terakhir.

    Args:
        days (int): Jumlah hari ke belakang (default: 7)

    Returns:
        pandas.DataFrame: DataFrame berisi transaksi dengan join ke products
    """
    conn = get_connection()

    # Menghitung tanggal N hari yang lalu
    start_date = datetime.now() - timedelta(days=days)

    # Query dengan JOIN untuk mendapatkan nama produk
    # JOIN menggabungkan data dari 2 tabel berdasarkan relasi
    query = """
        SELECT 
            t.id,
            t.product_id,
            p.name as product_name,
            t.quantity,
            t.total_price,
            t.profit,
            t.transaction_date
        FROM transactions t
        JOIN products p ON t.product_id = p.id
        WHERE t.transaction_date >= ?
        ORDER BY t.transaction_date DESC
    """

    df = pd.read_sql_query(query, conn, params=(start_date,))

    conn.close()
    return df


def get_daily_sales(days=7):
    """
    Mengambil ringkasan penjualan per hari untuk N hari terakhir.

    Digunakan untuk membuat grafik tren penjualan harian.

    Args:
        days (int): Jumlah hari (default: 7)

    Returns:
        pandas.DataFrame: DataFrame dengan kolom date, total_sales, total_profit
    """
    conn = get_connection()

    start_date = datetime.now() - timedelta(days=days)

    # Menggunakan DATE() untuk mengekstrak tanggal saja dari timestamp
    # GROUP BY untuk mengelompokkan per hari
    # SUM() untuk menjumlahkan total per hari
    query = """
        SELECT 
            DATE(transaction_date) as date,
            SUM(total_price) as total_sales,
            SUM(profit) as total_profit,
            SUM(quantity) as total_items
        FROM transactions
        WHERE transaction_date >= ?
        GROUP BY DATE(transaction_date)
        ORDER BY date
    """

    df = pd.read_sql_query(query, conn, params=(start_date,))

    conn.close()
    return df


def get_today_summary():
    """
    Menghitung ringkasan penjualan hari ini.

    Returns:
        dict: Dictionary berisi total_sales dan total_profit hari ini
    """
    conn = get_connection()
    cursor = conn.cursor()

    # DATE('now') mengambil tanggal hari ini dalam SQLite
    # COALESCE mengembalikan 0 jika hasil NULL (tidak ada transaksi)
    cursor.execute("""
        SELECT 
            COALESCE(SUM(total_price), 0) as total_sales,
            COALESCE(SUM(profit), 0) as total_profit,
            COALESCE(SUM(quantity), 0) as total_items
        FROM transactions
        WHERE DATE(transaction_date) = DATE('now')
    """)

    result = cursor.fetchone()
    conn.close()

    return {
        "total_sales": result[0],
        "total_profit": result[1],
        "total_items": result[2],
    }


def get_sales_prediction():
    """
    Menghitung prediksi kebutuhan stok berdasarkan rata-rata 3 hari terakhir.

    Ini adalah "Simple AI" - menggunakan moving average untuk prediksi.
    Moving average adalah teknik sederhana yang sering digunakan dalam
    forecasting dan analisis time series.

    Returns:
        pandas.DataFrame: DataFrame dengan prediksi per produk
    """
    conn = get_connection()

    # Ambil data penjualan 3 hari terakhir per produk
    start_date = datetime.now() - timedelta(days=3)

    query = """
        SELECT 
            p.id as product_id,
            p.name as product_name,
            p.stock as current_stock,
            COALESCE(SUM(t.quantity), 0) as total_sold_3days,
            COALESCE(AVG(t.quantity), 0) as avg_daily_sales
        FROM products p
        LEFT JOIN transactions t ON p.id = t.product_id 
            AND t.transaction_date >= ?
        GROUP BY p.id, p.name, p.stock
        ORDER BY avg_daily_sales DESC
    """

    df = pd.read_sql_query(query, conn, params=(start_date,))

    conn.close()

    # Hitung prediksi kebutuhan stok besok
    # Rumus: rata-rata penjualan harian x 1.2 (buffer 20%)
    df["predicted_demand"] = (df["avg_daily_sales"] * 1.2).round(0).astype(int)

    # Hitung status stok
    # Jika stok < predicted_demand, perlu restock
    df["stock_status"] = df.apply(
        lambda row: "⚠️ Perlu Restock"
        if row["current_stock"] < row["predicted_demand"] * 2
        else "✅ Aman",
        axis=1,
    )

    return df


# =====================================================
# DUMMY DATA GENERATOR
# =====================================================


def is_database_empty():
    """
    Mengecek apakah database kosong (belum ada data).

    Returns:
        bool: True jika kosong, False jika sudah ada data
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM products")
    count = cursor.fetchone()[0]

    conn.close()
    return count == 0


def generate_dummy_data():
    """
    Generate data dummy untuk demo aplikasi.

    Membuat:
    - 10 produk dengan berbagai kategori
    - 50 transaksi tersebar dalam 7 hari terakhir

    Data dummy penting untuk:
    1. Demo aplikasi agar grafik tidak kosong
    2. Testing fitur-fitur tanpa input manual
    3. Presentasi yang lebih menarik
    """

    # =========================================
    # DAFTAR PRODUK DUMMY
    # =========================================
    # Format: (nama, kategori, harga_jual, harga_modal, stok)
    products_data = [
        ("Laptop Asus ROG", "Elektronik", 15000000, 13000000, 15),
        ("iPhone 15 Pro", "Elektronik", 20000000, 17500000, 10),
        ("Mouse Logitech G502", "Aksesoris", 850000, 650000, 50),
        ("Keyboard Mechanical RGB", "Aksesoris", 750000, 500000, 40),
        ("Monitor Samsung 27 inch", "Elektronik", 3500000, 2800000, 20),
        ("Headphone Sony WH-1000XM5", "Aksesoris", 4500000, 3500000, 25),
        ("SSD Samsung 1TB", "Komponen", 1500000, 1100000, 35),
        ("RAM DDR5 32GB", "Komponen", 2000000, 1500000, 30),
        ("Webcam Logitech C920", "Aksesoris", 1200000, 900000, 45),
        ("Printer Epson L3250", "Elektronik", 3200000, 2600000, 15),
    ]

    # Insert semua produk ke database
    product_ids = []
    for product in products_data:
        pid = add_product(product[0], product[1], product[2], product[3], product[4])
        product_ids.append(pid)

    print(f"✅ Berhasil menambahkan {len(product_ids)} produk")

    # =========================================
    # GENERATE TRANSAKSI DUMMY
    # =========================================
    # Membuat 50 transaksi random dalam 7 hari terakhir

    transaction_count = 0

    for day_offset in range(7, -1, -1):  # 7 hari lalu sampai hari ini
        # Random jumlah transaksi per hari (5-10 transaksi)
        daily_transactions = random.randint(5, 10)

        for _ in range(daily_transactions):
            # Pilih produk random
            product_id = random.choice(product_ids)
            product = get_product_by_id(product_id)

            if product and product["stock"] > 0:
                # Random quantity (1-3 item)
                quantity = random.randint(1, min(3, product["stock"]))

                # Hitung total dan profit
                total_price = product["price"] * quantity
                profit = (product["price"] - product["cost"]) * quantity

                # Generate tanggal random dalam hari tersebut
                transaction_date = datetime.now() - timedelta(
                    days=day_offset,
                    hours=random.randint(8, 20),  # Jam kerja 08:00 - 20:00
                    minutes=random.randint(0, 59),
                )

                # Simpan transaksi dengan tanggal custom
                add_transaction_with_date(
                    product_id, quantity, total_price, profit, transaction_date
                )

                # Update stok (kurangi)
                update_stock(product_id, quantity)

                transaction_count += 1

                # Batasi total 50 transaksi
                if transaction_count >= 50:
                    break

        if transaction_count >= 50:
            break

    print(f"✅ Berhasil menambahkan {transaction_count} transaksi dummy")
    return True


def initialize_database():
    """
    Fungsi utama untuk inisialisasi database.

    Dipanggil saat aplikasi pertama kali dijalankan.
    Akan membuat tabel dan generate dummy data jika database kosong.

    Returns:
        bool: True jika ini pertama kali (data baru digenerate)
    """
    # Step 1: Buat tabel jika belum ada
    create_tables()

    # Step 2: Cek apakah database kosong
    if is_database_empty():
        print("📦 Database kosong, generating dummy data...")
        generate_dummy_data()
        return True

    return False


# =====================================================
# TESTING (Jalankan file ini langsung untuk test)
# =====================================================
if __name__ == "__main__":
    print("🚀 Testing Database Module...")
    print("=" * 50)

    # Initialize database
    is_new = initialize_database()

    if is_new:
        print("\n✅ Database baru telah dibuat dengan dummy data!")
    else:
        print("\n📁 Database sudah ada, menggunakan data yang ada.")

    # Test get products
    print("\n📦 Daftar Produk:")
    products = get_products()
    print(products[["id", "name", "stock"]].to_string())

    # Test get today summary
    print("\n💰 Ringkasan Hari Ini:")
    summary = get_today_summary()
    print(f"   Total Penjualan: Rp {summary['total_sales']:,.0f}")
    print(f"   Total Profit: Rp {summary['total_profit']:,.0f}")

    # Test get daily sales
    print("\n📊 Penjualan 7 Hari Terakhir:")
    daily = get_daily_sales(7)
    print(daily.to_string())

    print("\n" + "=" * 50)
    print("✅ Semua test berhasil!")
