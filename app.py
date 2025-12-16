"""
=====================================================
APP.PY - Sales & Inventory Intelligence Dashboard
=====================================================

Aplikasi web dashboard untuk manajemen penjualan dan inventori
menggunakan Streamlit sebagai frontend.

Fitur:
1. Dashboard Harian - Metrics dan grafik penjualan
2. Manajemen Stok - Tabel produk dengan stok real-time
3. Input Transaksi - Form untuk mencatat penjualan baru
4. Prediksi AI - Rekomendasi kebutuhan stok

Tech Stack:
- Streamlit: Web UI framework
- Pandas: Data manipulation
- Plotly: Interactive charts
- SQLite: Database

Author: [Nama Anda]
Portfolio Project: Sales & Inventory Intelligence Dashboard
=====================================================
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Import modul database yang kita buat
import database as db

# =====================================================
# KONFIGURASI HALAMAN STREAMLIT
# =====================================================

# st.set_page_config HARUS dipanggil pertama kali
# sebelum command Streamlit lainnya
st.set_page_config(
    page_title="Sales & Inventory Dashboard",  # Judul di tab browser
    page_icon="📊",  # Icon di tab browser
    layout="wide",  # Menggunakan full width
    initial_sidebar_state="expanded",  # Sidebar terbuka by default
)


# =====================================================
# CUSTOM CSS STYLING
# =====================================================


def apply_custom_css():
    """
    Menerapkan custom CSS untuk mempercantik tampilan.

    Streamlit memungkinkan injection CSS menggunakan st.markdown
    dengan parameter unsafe_allow_html=True.
    """
    st.markdown(
        """
        <style>
        /* ===== MAIN CONTAINER ===== */
        .main {
            padding: 1rem 2rem;
        }
        
        /* ===== METRIC CARDS ===== */
        /* Styling untuk tampilan metrics yang lebih menarik */
        [data-testid="metric-container"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem;
            border-radius: 10px;
            color: white;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        [data-testid="metric-container"] label {
            color: rgba(255, 255, 255, 0.8) !important;
        }
        
        [data-testid="metric-container"] [data-testid="stMetricValue"] {
            color: white !important;
        }
        
        /* ===== HEADERS ===== */
        h1 {
            color: #1e3a8a;
            padding-bottom: 0.5rem;
            border-bottom: 3px solid #667eea;
        }
        
        h2, h3 {
            color: #374151;
        }
        
        /* ===== SIDEBAR ===== */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%);
        }
        
        /* ===== SUCCESS/INFO BOXES ===== */
        .stSuccess, .stInfo {
            border-radius: 10px;
        }
        
        /* ===== DATAFRAME ===== */
        .stDataFrame {
            border-radius: 10px;
            overflow: hidden;
        }
        </style>
    """,
        unsafe_allow_html=True,
    )


# =====================================================
# SIDEBAR - FORM INPUT TRANSAKSI
# =====================================================


def render_sidebar():
    """
    Menampilkan sidebar dengan form input transaksi baru.

    Sidebar adalah tempat ideal untuk form input karena:
    1. Tidak mengganggu tampilan utama dashboard
    2. Selalu visible dan mudah diakses
    3. Membuat layout lebih rapi

    PENTING: Dropdown produk diletakkan DI LUAR st.form agar
    harga bisa langsung berubah saat user mengganti pilihan produk.
    st.form hanya untuk input yang perlu di-batch (quantity + submit).
    """
    with st.sidebar:
        # Header sidebar
        st.markdown("## 🛒 Input Transaksi Baru")
        st.markdown("---")

        # Ambil daftar produk untuk dropdown
        products_df = db.get_products()

        # Cek apakah ada produk
        if products_df.empty:
            st.warning("⚠️ Belum ada produk dalam database.")
            return

        # =========================================
        # PILIH PRODUK (DI LUAR FORM)
        # =========================================
        # Selectbox di luar form agar harga langsung update
        # saat user mengganti pilihan produk
        st.markdown("### 📝 Detail Transaksi")

        # Dropdown pilih produk
        # Membuat dictionary untuk mapping nama -> id
        product_options = dict(
            zip(
                products_df["name"]
                + " (Stok: "
                + products_df["stock"].astype(str)
                + ")",
                products_df["id"],
            )
        )

        selected_product_name = st.selectbox(
            "Pilih Produk:",
            options=list(product_options.keys()),
            help="Pilih produk yang akan dijual",
            key="product_selector",  # Unique key untuk state management
        )

        if selected_product_name:
            selected_product_id = product_options[selected_product_name]
            product = db.get_product_by_id(selected_product_id)

            if product:
                # =========================================
                # INFO HARGA (DI LUAR FORM - REAL-TIME UPDATE)
                # =========================================
                # Tampilkan info harga - ini akan langsung berubah
                # saat user memilih produk berbeda
                st.info(f"💰 Harga: Rp {product['price']:,.0f}")
                st.caption(
                    f"Modal: Rp {product['cost']:,.0f} | Profit/item: Rp {product['price'] - product['cost']:,.0f}"
                )

                # =========================================
                # FORM INPUT QUANTITY & SUBMIT
                # =========================================
                # Hanya quantity dan tombol submit yang di dalam form
                with st.form(key="transaction_form", clear_on_submit=True):
                    # Input quantity
                    max_qty = product["stock"]

                    if max_qty <= 0:
                        st.error("❌ Stok habis!")
                        quantity = 0
                    else:
                        quantity = st.number_input(
                            "Jumlah:",
                            min_value=1,
                            max_value=max_qty,
                            value=1,
                            step=1,
                            help=f"Stok tersedia: {max_qty}",
                        )

                    # Kalkulasi total (akan dihitung ulang saat submit)
                    if quantity > 0:
                        total_price = product["price"] * quantity
                        profit = (product["price"] - product["cost"]) * quantity

                        st.markdown("---")
                        st.markdown(f"**Total: Rp {total_price:,.0f}**")
                        st.markdown(f"*Profit: Rp {profit:,.0f}*")

                    # Tombol submit
                    submitted = st.form_submit_button(
                        "✅ Catat Transaksi",
                        use_container_width=True,
                        disabled=(max_qty <= 0),  # Disable jika stok habis
                    )

                    if submitted and quantity > 0:
                        # Ambil data produk terbaru untuk memastikan stok masih ada
                        current_product = db.get_product_by_id(selected_product_id)

                        if current_product["stock"] < quantity:
                            st.error("❌ Stok tidak mencukupi!")
                        else:
                            # Hitung ulang total dan profit dengan data terbaru
                            final_total = current_product["price"] * quantity
                            final_profit = (
                                current_product["price"] - current_product["cost"]
                            ) * quantity

                            # Simpan transaksi
                            db.add_transaction(
                                selected_product_id, quantity, final_total, final_profit
                            )
                            # Update stok
                            db.update_stock(selected_product_id, quantity)

                            st.success("✅ Transaksi berhasil dicatat!")
                            # Rerun untuk refresh data
                            st.rerun()

        # =========================================
        # INFO TAMBAHAN DI SIDEBAR
        # =========================================
        st.markdown("---")
        st.markdown("### 📅 Informasi")
        st.markdown(f"**Tanggal:** {datetime.now().strftime('%d %B %Y')}")
        st.markdown(f"**Waktu:** {datetime.now().strftime('%H:%M:%S')}")

        # Tombol refresh
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()


# =====================================================
# METRICS DASHBOARD
# =====================================================


def render_metrics():
    """
    Menampilkan metrics utama dashboard.

    Metrics memberikan gambaran cepat tentang performa hari ini.
    Menggunakan st.metric yang sudah built-in di Streamlit.
    """
    st.markdown("## 📈 Dashboard Harian")

    # Ambil ringkasan hari ini
    summary = db.get_today_summary()

    # Ambil data untuk perbandingan dengan kemarin
    # Untuk menampilkan delta (perubahan)
    daily_sales = db.get_daily_sales(2)

    yesterday_sales = 0
    yesterday_profit = 0

    if len(daily_sales) >= 2:
        yesterday_data = daily_sales.iloc[-2]
        yesterday_sales = yesterday_data["total_sales"]
        yesterday_profit = yesterday_data["total_profit"]

    # Hitung delta (perubahan dari kemarin)
    delta_sales = summary["total_sales"] - yesterday_sales
    delta_profit = summary["total_profit"] - yesterday_profit

    # =========================================
    # TAMPILKAN METRICS DALAM KOLOM
    # =========================================
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="💰 Total Penjualan Hari Ini",
            value=f"Rp {summary['total_sales']:,.0f}",
            delta=f"Rp {delta_sales:,.0f}" if delta_sales != 0 else None,
            delta_color="normal",  # hijau jika naik, merah jika turun
        )

    with col2:
        st.metric(
            label="📊 Total Profit Hari Ini",
            value=f"Rp {summary['total_profit']:,.0f}",
            delta=f"Rp {delta_profit:,.0f}" if delta_profit != 0 else None,
            delta_color="normal",
        )

    with col3:
        st.metric(
            label="📦 Item Terjual Hari Ini", value=f"{summary['total_items']:.0f} item"
        )

    with col4:
        # Hitung rata-rata profit per transaksi
        avg_profit = (
            summary["total_profit"] / summary["total_items"]
            if summary["total_items"] > 0
            else 0
        )
        st.metric(label="💎 Rata-rata Profit/Item", value=f"Rp {avg_profit:,.0f}")


# =====================================================
# GRAFIK TREN PENJUALAN
# =====================================================


def render_sales_chart():
    """
    Menampilkan grafik line chart tren penjualan 7 hari terakhir.

    Menggunakan Plotly untuk visualisasi interaktif.
    Plotly lebih powerful dibanding matplotlib untuk web apps karena:
    1. Interaktif (zoom, hover, pan)
    2. Responsive
    3. Tampilan modern
    """
    st.markdown("## 📊 Tren Penjualan 7 Hari Terakhir")

    # Ambil data penjualan harian
    daily_sales = db.get_daily_sales(7)

    if daily_sales.empty:
        st.info("📭 Belum ada data penjualan.")
        return

    # =========================================
    # BUAT LINE CHART DENGAN PLOTLY
    # =========================================

    # Membuat figure dengan 2 y-axis (dual axis)
    # untuk menampilkan sales dan profit bersamaan
    fig = go.Figure()

    # Line 1: Total Penjualan (warna biru)
    fig.add_trace(
        go.Scatter(
            x=daily_sales["date"],
            y=daily_sales["total_sales"],
            name="Total Penjualan",
            mode="lines+markers",  # Garis dengan titik marker
            line=dict(color="#667eea", width=3),
            marker=dict(size=8),
            hovertemplate="<b>%{x}</b><br>" + "Penjualan: Rp %{y:,.0f}<extra></extra>",
        )
    )

    # Line 2: Total Profit (warna hijau)
    fig.add_trace(
        go.Scatter(
            x=daily_sales["date"],
            y=daily_sales["total_profit"],
            name="Total Profit",
            mode="lines+markers",
            line=dict(color="#10b981", width=3),
            marker=dict(size=8),
            hovertemplate="<b>%{x}</b><br>" + "Profit: Rp %{y:,.0f}<extra></extra>",
        )
    )

    # Konfigurasi layout
    fig.update_layout(
        title=dict(text="Tren Penjualan & Profit Harian", font=dict(size=20)),
        xaxis_title="Tanggal",
        yaxis_title="Jumlah (Rp)",
        hovermode="x unified",  # Menampilkan semua data di satu waktu
        legend=dict(
            orientation="h",  # Horizontal legend
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        plot_bgcolor="rgba(0,0,0,0)",  # Transparent background
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial", size=12),
    )

    # Styling grid
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="rgba(0,0,0,0.1)")
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgba(0,0,0,0.1)")

    # Tampilkan chart di Streamlit
    st.plotly_chart(fig, use_container_width=True)

    # =========================================
    # TAMBAHAN: BAR CHART ITEMS TERJUAL
    # =========================================
    col1, col2 = st.columns(2)

    with col1:
        # Bar chart untuk items terjual per hari
        fig_bar = px.bar(
            daily_sales,
            x="date",
            y="total_items",
            title="📦 Jumlah Item Terjual per Hari",
            color="total_items",
            color_continuous_scale="Viridis",
        )
        fig_bar.update_layout(
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:
        # Pie chart kategori penjualan
        transactions = db.get_transactions(7)
        if not transactions.empty:
            # Group by product
            product_sales = (
                transactions.groupby("product_name")["total_price"].sum().reset_index()
            )
            product_sales = product_sales.nlargest(5, "total_price")  # Top 5

            fig_pie = px.pie(
                product_sales,
                values="total_price",
                names="product_name",
                title="🏆 Top 5 Produk Terlaris",
                hole=0.4,  # Donut chart
            )
            fig_pie.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_pie, use_container_width=True)


# =====================================================
# TABEL MANAJEMEN STOK
# =====================================================


def render_stock_table():
    """
    Menampilkan tabel interaktif untuk manajemen stok.

    Fitur:
    - Tabel stok dengan sorting dan filtering
    - Form restock produk existing
    - Form tambah produk baru

    Menggunakan st.dataframe yang sudah mendukung:
    - Sorting (klik header kolom)
    - Search/Filter
    - Resize kolom
    - Scrolling
    """
    st.markdown("## 📦 Manajemen Stok Barang")

    # Ambil data produk
    products_df = db.get_products()

    # =========================================
    # AKSI GUDANG: RESTOCK & TAMBAH BARANG
    # =========================================
    col_action1, col_action2 = st.columns(2)

    with col_action1:
        # =========================================
        # FORM RESTOCK PRODUK
        # =========================================
        with st.expander("📥 Restock Produk", expanded=False):
            st.markdown("**Tambah stok untuk produk yang sudah ada**")

            if products_df.empty:
                st.warning("⚠️ Belum ada produk untuk di-restock.")
            else:
                # Dropdown pilih produk untuk restock
                restock_product_options = dict(
                    zip(
                        products_df["name"]
                        + " (Stok: "
                        + products_df["stock"].astype(str)
                        + ")",
                        products_df["id"],
                    )
                )

                selected_restock_product = st.selectbox(
                    "Pilih Produk:",
                    options=list(restock_product_options.keys()),
                    key="restock_product_select",
                )

                if selected_restock_product:
                    restock_product_id = restock_product_options[
                        selected_restock_product
                    ]
                    product_info = db.get_product_by_id(restock_product_id)

                    if product_info:
                        st.caption(f"Stok saat ini: **{product_info['stock']}** unit")

                        # Form restock
                        with st.form(key="restock_form"):
                            restock_qty = st.number_input(
                                "Jumlah Restock:",
                                min_value=1,
                                max_value=1000,
                                value=10,
                                step=1,
                                help="Masukkan jumlah stok yang akan ditambahkan",
                            )

                            new_total = product_info["stock"] + restock_qty
                            st.info(f"📊 Stok setelah restock: **{new_total}** unit")

                            restock_submitted = st.form_submit_button(
                                "✅ Konfirmasi Restock", use_container_width=True
                            )

                            if restock_submitted:
                                success = db.restock_product(
                                    restock_product_id, restock_qty
                                )
                                if success:
                                    st.success(
                                        f"✅ Berhasil menambah {restock_qty} unit ke {product_info['name']}!"
                                    )
                                    st.rerun()
                                else:
                                    st.error("❌ Gagal melakukan restock.")

    with col_action2:
        # =========================================
        # FORM TAMBAH PRODUK BARU
        # =========================================
        with st.expander("➕ Tambah Produk Baru", expanded=False):
            st.markdown("**Daftarkan produk baru ke inventory**")

            with st.form(key="add_product_form"):
                # Input nama produk
                new_product_name = st.text_input(
                    "Nama Produk:",
                    placeholder="Contoh: Laptop Dell XPS 15",
                    help="Masukkan nama produk yang unik",
                )

                # Input kategori - bisa pilih existing atau buat baru
                existing_categories = (
                    db.get_categories() if not products_df.empty else []
                )

                category_option = st.radio(
                    "Kategori:",
                    options=["Pilih dari yang ada", "Buat kategori baru"],
                    horizontal=True,
                    key="category_option",
                )

                if category_option == "Pilih dari yang ada" and existing_categories:
                    new_product_category = st.selectbox(
                        "Pilih Kategori:",
                        options=existing_categories,
                        key="existing_category",
                    )
                else:
                    new_product_category = st.text_input(
                        "Nama Kategori Baru:",
                        placeholder="Contoh: Elektronik",
                        key="new_category",
                    )

                # Input harga
                col_price1, col_price2 = st.columns(2)
                with col_price1:
                    new_product_cost = st.number_input(
                        "Harga Modal (Rp):",
                        min_value=0,
                        value=100000,
                        step=10000,
                        help="Harga beli dari supplier",
                    )
                with col_price2:
                    new_product_price = st.number_input(
                        "Harga Jual (Rp):",
                        min_value=0,
                        value=150000,
                        step=10000,
                        help="Harga jual ke customer",
                    )

                # Input stok awal
                new_product_stock = st.number_input(
                    "Stok Awal:", min_value=0, value=10, step=1, help="Jumlah stok awal"
                )

                # Tampilkan profit margin
                if new_product_cost > 0:
                    profit_per_item = new_product_price - new_product_cost
                    margin = (profit_per_item / new_product_cost) * 100
                    st.caption(
                        f"💰 Profit/item: Rp {profit_per_item:,.0f} | Margin: {margin:.1f}%"
                    )

                add_product_submitted = st.form_submit_button(
                    "➕ Tambah Produk", use_container_width=True
                )

                if add_product_submitted:
                    # Validasi input
                    if not new_product_name.strip():
                        st.error("❌ Nama produk tidak boleh kosong!")
                    elif not new_product_category.strip():
                        st.error("❌ Kategori tidak boleh kosong!")
                    elif new_product_price <= new_product_cost:
                        st.warning(
                            "⚠️ Harga jual sebaiknya lebih besar dari harga modal!"
                        )
                    else:
                        # Tambah produk baru
                        new_id = db.add_product(
                            new_product_name.strip(),
                            new_product_category.strip(),
                            new_product_price,
                            new_product_cost,
                            new_product_stock,
                        )
                        st.success(
                            f"✅ Produk '{new_product_name}' berhasil ditambahkan! (ID: {new_id})"
                        )
                        st.rerun()

    st.markdown("---")

    # =========================================
    # TABEL STOK
    # =========================================
    if products_df.empty:
        st.info(
            "📭 Belum ada produk dalam database. Silakan tambah produk baru di atas."
        )
        return

    # =========================================
    # FILTER DAN SEARCH
    # =========================================
    col1, col2 = st.columns([2, 1])

    with col1:
        # Search bar
        search = st.text_input(
            "🔍 Cari produk:", placeholder="Ketik nama produk...", key="stock_search"
        )

    with col2:
        # Filter kategori
        categories = ["Semua"] + products_df["category"].unique().tolist()
        selected_category = st.selectbox(
            "📁 Kategori:", categories, key="stock_category_filter"
        )

    # Apply filters
    filtered_df = products_df.copy()

    if search:
        # Case-insensitive search
        filtered_df = filtered_df[
            filtered_df["name"].str.lower().str.contains(search.lower())
        ]

    if selected_category != "Semua":
        filtered_df = filtered_df[filtered_df["category"] == selected_category]

    # =========================================
    # TAMPILKAN TABEL DENGAN STYLING
    # =========================================

    # Rename kolom untuk display yang lebih baik
    display_df = filtered_df[
        ["id", "name", "category", "price", "cost", "stock"]
    ].copy()
    display_df.columns = [
        "ID",
        "Nama Produk",
        "Kategori",
        "Harga Jual",
        "Harga Modal",
        "Stok",
    ]

    # Tambah kolom profit margin
    display_df["Profit/Item"] = display_df["Harga Jual"] - display_df["Harga Modal"]
    display_df["Margin (%)"] = (
        (display_df["Harga Jual"] - display_df["Harga Modal"])
        / display_df["Harga Modal"]
        * 100
    ).round(1)

    # Tambah status stok dengan emoji
    def get_stock_status(stock):
        if stock <= 5:
            return "🔴 Kritis"
        elif stock <= 15:
            return "🟡 Rendah"
        else:
            return "🟢 Aman"

    display_df["Status"] = display_df["Stok"].apply(get_stock_status)

    # Format angka sebagai currency
    st.dataframe(
        display_df.style.format(
            {
                "Harga Jual": "Rp {:,.0f}",
                "Harga Modal": "Rp {:,.0f}",
                "Profit/Item": "Rp {:,.0f}",
                "Margin (%)": "{:.1f}%",
            }
        ),
        use_container_width=True,
        height=400,
    )

    # =========================================
    # SUMMARY STOK
    # =========================================
    col1, col2, col3 = st.columns(3)

    with col1:
        total_products = len(filtered_df)
        st.info(f"📦 **Total Produk:** {total_products}")

    with col2:
        total_stock = filtered_df["stock"].sum()
        st.info(f"📊 **Total Unit Stok:** {total_stock:,}")

    with col3:
        total_value = (filtered_df["price"] * filtered_df["stock"]).sum()
        st.info(f"💰 **Nilai Inventory:** Rp {total_value:,.0f}")

    st.markdown("---")

    # =========================================
    # EDIT & DELETE PRODUK
    # =========================================
    st.markdown("### ⚙️ Kelola Produk")

    col_edit, col_delete = st.columns(2)

    with col_edit:
        # =========================================
        # FORM EDIT/UPDATE PRODUK
        # =========================================
        with st.expander("✏️ Edit Produk", expanded=False):
            st.markdown("**Update informasi produk yang sudah ada**")

            # Dropdown pilih produk untuk edit
            edit_product_options = dict(
                zip(
                    products_df["name"]
                    + " (ID: "
                    + products_df["id"].astype(str)
                    + ")",
                    products_df["id"],
                )
            )

            selected_edit_product = st.selectbox(
                "Pilih Produk untuk Diedit:",
                options=list(edit_product_options.keys()),
                key="edit_product_select",
            )

            if selected_edit_product:
                edit_product_id = edit_product_options[selected_edit_product]
                edit_product_info = db.get_product_by_id(edit_product_id)

                if edit_product_info:
                    st.caption(
                        f"**Data Saat Ini:** Stok: {edit_product_info['stock']} | Harga: Rp {edit_product_info['price']:,.0f}"
                    )

                    with st.form(key="edit_product_form"):
                        # Input nama produk
                        edit_name = st.text_input(
                            "Nama Produk:",
                            value=edit_product_info["name"],
                            key="edit_name",
                        )

                        # Input kategori
                        existing_cats = db.get_categories()
                        if edit_product_info["category"] in existing_cats:
                            default_cat_idx = existing_cats.index(
                                edit_product_info["category"]
                            )
                        else:
                            default_cat_idx = 0

                        edit_category = st.selectbox(
                            "Kategori:",
                            options=existing_cats,
                            index=default_cat_idx,
                            key="edit_category",
                        )

                        # Input harga
                        col_ep1, col_ep2 = st.columns(2)
                        with col_ep1:
                            edit_cost = st.number_input(
                                "Harga Modal (Rp):",
                                min_value=0,
                                value=int(edit_product_info["cost"]),
                                step=10000,
                                key="edit_cost",
                            )
                        with col_ep2:
                            edit_price = st.number_input(
                                "Harga Jual (Rp):",
                                min_value=0,
                                value=int(edit_product_info["price"]),
                                step=10000,
                                key="edit_price",
                            )

                        # Input stok
                        edit_stock = st.number_input(
                            "Stok:",
                            min_value=0,
                            value=int(edit_product_info["stock"]),
                            step=1,
                            key="edit_stock",
                            help="Ubah jumlah stok secara langsung",
                        )

                        # Preview perubahan
                        if edit_cost > 0:
                            new_profit = edit_price - edit_cost
                            new_margin = (new_profit / edit_cost) * 100
                            st.caption(
                                f"💰 Profit/item: Rp {new_profit:,.0f} | Margin: {new_margin:.1f}%"
                            )

                        edit_submitted = st.form_submit_button(
                            "💾 Simpan Perubahan", use_container_width=True
                        )

                        if edit_submitted:
                            success = db.update_product(
                                edit_product_id,
                                name=edit_name.strip(),
                                category=edit_category,
                                price=edit_price,
                                cost=edit_cost,
                                stock=edit_stock,
                            )
                            if success:
                                st.success(
                                    f"✅ Produk '{edit_name}' berhasil diupdate!"
                                )
                                st.rerun()
                            else:
                                st.error("❌ Gagal mengupdate produk.")

    with col_delete:
        # =========================================
        # FORM DELETE PRODUK
        # =========================================
        with st.expander("🗑️ Hapus Produk", expanded=False):
            st.markdown("**Hapus produk dari inventory**")
            st.warning(
                "⚠️ **Perhatian:** Menghapus produk juga akan menghapus semua riwayat transaksi terkait!"
            )

            # Dropdown pilih produk untuk delete
            delete_product_options = dict(
                zip(
                    products_df["name"]
                    + " (ID: "
                    + products_df["id"].astype(str)
                    + ", Stok: "
                    + products_df["stock"].astype(str)
                    + ")",
                    products_df["id"],
                )
            )

            selected_delete_product = st.selectbox(
                "Pilih Produk untuk Dihapus:",
                options=list(delete_product_options.keys()),
                key="delete_product_select",
            )

            if selected_delete_product:
                delete_product_id = delete_product_options[selected_delete_product]
                delete_product_info = db.get_product_by_id(delete_product_id)

                if delete_product_info:
                    st.error(f"🗑️ **Produk yang akan dihapus:**")
                    st.markdown(f"""
                    - **Nama:** {delete_product_info["name"]}
                    - **Kategori:** {delete_product_info["category"]}
                    - **Stok:** {delete_product_info["stock"]} unit
                    - **Harga Jual:** Rp {delete_product_info["price"]:,.0f}
                    """)

                    # Konfirmasi dengan checkbox
                    confirm_delete = st.checkbox(
                        "✅ Saya yakin ingin menghapus produk ini", key="confirm_delete"
                    )

                    # Tombol hapus
                    if st.button(
                        "🗑️ Hapus Produk",
                        use_container_width=True,
                        disabled=not confirm_delete,
                        type="primary" if confirm_delete else "secondary",
                    ):
                        success = db.delete_product(delete_product_id)
                        if success:
                            st.success(
                                f"✅ Produk '{delete_product_info['name']}' berhasil dihapus!"
                            )
                            st.rerun()
                        else:
                            st.error("❌ Gagal menghapus produk.")


# =====================================================
# PREDIKSI AI SEDERHANA
# =====================================================


def render_ai_prediction():
    """
    Menampilkan prediksi kebutuhan stok menggunakan Simple AI.

    Metode: Moving Average 3 Hari
    - Menghitung rata-rata penjualan 3 hari terakhir
    - Menambahkan buffer 20% sebagai safety stock
    - Memberikan rekomendasi restock

    Ini adalah contoh sederhana "AI/ML" yang mudah dijelaskan
    saat wawancara. Meskipun sederhana, moving average adalah
    teknik yang benar-benar digunakan di industri untuk forecasting.
    """
    st.markdown("## 🤖 Prediksi Kebutuhan Stok (Simple AI)")

    # Penjelasan metode
    with st.expander("ℹ️ Tentang Metode Prediksi"):
        st.markdown("""
        **Metode:** Moving Average 3 Hari + Buffer 20%
        
        **Cara Kerja:**
        1. Menghitung rata-rata penjualan per produk dalam 3 hari terakhir
        2. Menambahkan buffer 20% untuk mengantisipasi fluktuasi
        3. Membandingkan dengan stok saat ini untuk rekomendasi
        
        **Formula:**
        ```
        Predicted Demand = Rata-rata Penjualan 3 Hari × 1.2
        ```
        
        **Status Stok:**
        - ⚠️ Perlu Restock: Jika stok < 2× predicted demand
        - ✅ Aman: Jika stok >= 2× predicted demand
        """)

    # Ambil data prediksi
    prediction_df = db.get_sales_prediction()

    if prediction_df.empty:
        st.info("📭 Belum ada data untuk prediksi.")
        return

    # =========================================
    # TAMPILKAN TABEL PREDIKSI
    # =========================================

    # Pilih dan rename kolom
    display_df = prediction_df[
        [
            "product_name",
            "current_stock",
            "total_sold_3days",
            "avg_daily_sales",
            "predicted_demand",
            "stock_status",
        ]
    ].copy()

    display_df.columns = [
        "Produk",
        "Stok Saat Ini",
        "Terjual (3 Hari)",
        "Rata-rata/Hari",
        "Prediksi Kebutuhan",
        "Status",
    ]

    # Tampilkan tabel
    st.dataframe(
        display_df.style.format(
            {"Rata-rata/Hari": "{:.1f}", "Prediksi Kebutuhan": "{:.0f}"}
        ),
        use_container_width=True,
        height=400,
    )

    # =========================================
    # HIGHLIGHT PRODUK YANG PERLU RESTOCK
    # =========================================
    needs_restock = prediction_df[
        prediction_df["stock_status"].str.contains("Perlu Restock")
    ]

    if not needs_restock.empty:
        st.warning(f"⚠️ **{len(needs_restock)} produk memerlukan restock!**")

        for _, row in needs_restock.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 2])
                with col1:
                    st.markdown(f"**{row['product_name']}**")
                with col2:
                    st.markdown(f"Stok: **{row['current_stock']}**")
                with col3:
                    restock_qty = max(
                        0, (row["predicted_demand"] * 3) - row["current_stock"]
                    )
                    st.markdown(f"Rekomendasi tambah: **{restock_qty:.0f} unit**")
    else:
        st.success("✅ Semua produk memiliki stok yang cukup!")

    # =========================================
    # GRAFIK VISUALISASI PREDIKSI
    # =========================================
    st.markdown("### 📊 Visualisasi Stok vs Prediksi Kebutuhan")

    # Filter produk dengan penjualan > 0
    viz_df = prediction_df[prediction_df["avg_daily_sales"] > 0].head(10)

    if not viz_df.empty:
        fig = go.Figure()

        # Bar: Current Stock
        fig.add_trace(
            go.Bar(
                name="Stok Saat Ini",
                x=viz_df["product_name"],
                y=viz_df["current_stock"],
                marker_color="#667eea",
            )
        )

        # Bar: Predicted Demand (x2 untuk safety stock)
        fig.add_trace(
            go.Bar(
                name="Safety Stock Level (2× Predicted)",
                x=viz_df["product_name"],
                y=viz_df["predicted_demand"] * 2,
                marker_color="#f59e0b",
            )
        )

        fig.update_layout(
            barmode="group",
            title="Perbandingan Stok Aktual vs Safety Stock Level",
            xaxis_title="Produk",
            yaxis_title="Jumlah Unit",
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(fig, use_container_width=True)


# =====================================================
# RIWAYAT TRANSAKSI
# =====================================================


def render_transaction_history():
    """
    Menampilkan riwayat transaksi dengan filter dan export.

    Fitur:
    - Filter periode: 7 hari, 1 minggu, 1 bulan, custom
    - Export ke Excel/CSV
    - Summary total penjualan dan profit
    """
    st.markdown("## 📋 Riwayat Transaksi")

    # =========================================
    # FILTER PERIODE
    # =========================================
    st.markdown("### 🔍 Filter Periode")

    col_filter1, col_filter2, col_filter3 = st.columns([1, 1, 2])

    with col_filter1:
        # Pilihan periode preset
        period_options = {
            "1 Minggu Terakhir": 7,
            "2 Minggu Terakhir": 14,
            "1 Bulan Terakhir": 30,
            "3 Bulan Terakhir": 90,
            "6 Bulan Terakhir": 180,
            "1 Tahun Terakhir": 365,
            "Custom (Pilih Tanggal)": -1,  # -1 = custom
        }

        selected_period = st.selectbox(
            "Periode:",
            options=list(period_options.keys()),
            index=0,
            key="transaction_period",
        )

        days = period_options[selected_period]

    with col_filter2:
        # Jika custom, tampilkan date picker
        if days == -1:
            start_date = st.date_input(
                "Dari Tanggal:",
                value=datetime.now() - timedelta(days=30),
                key="start_date",
            )
        else:
            start_date = datetime.now() - timedelta(days=days)

    with col_filter3:
        if days == -1:
            end_date = st.date_input(
                "Sampai Tanggal:", value=datetime.now(), key="end_date"
            )
        else:
            end_date = datetime.now()

    # Hitung jumlah hari untuk query
    if days == -1:
        # Custom date range
        query_days = (datetime.now().date() - start_date).days + 1
    else:
        query_days = days

    # Ambil transaksi berdasarkan filter
    transactions_df = db.get_transactions(query_days)

    # Filter tambahan untuk custom date (karena get_transactions hanya pakai days)
    if days == -1 and not transactions_df.empty:
        transactions_df["transaction_date"] = pd.to_datetime(
            transactions_df["transaction_date"], format="mixed"
        )
        start_datetime = pd.to_datetime(start_date)
        end_datetime = pd.to_datetime(end_date) + timedelta(days=1)  # Include end date
        transactions_df = transactions_df[
            (transactions_df["transaction_date"] >= start_datetime)
            & (transactions_df["transaction_date"] < end_datetime)
        ]

    if transactions_df.empty:
        st.info("📭 Tidak ada transaksi dalam periode yang dipilih.")
        return

    # Format tanggal jika belum
    if transactions_df["transaction_date"].dtype == "object":
        transactions_df["transaction_date"] = pd.to_datetime(
            transactions_df["transaction_date"], format="mixed"
        )

    transactions_df["Tanggal"] = transactions_df["transaction_date"].dt.strftime(
        "%d/%m/%Y %H:%M"
    )

    # =========================================
    # SUMMARY TRANSAKSI
    # =========================================
    st.markdown("### 📊 Ringkasan Periode")

    col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)

    with col_sum1:
        total_transactions = len(transactions_df)
        st.metric("📝 Total Transaksi", f"{total_transactions}")

    with col_sum2:
        total_items = transactions_df["quantity"].sum()
        st.metric("📦 Total Item Terjual", f"{total_items:,.0f}")

    with col_sum3:
        total_sales = transactions_df["total_price"].sum()
        st.metric("💰 Total Penjualan", f"Rp {total_sales:,.0f}")

    with col_sum4:
        total_profit = transactions_df["profit"].sum()
        st.metric("📈 Total Profit", f"Rp {total_profit:,.0f}")

    st.markdown("---")

    # =========================================
    # TABEL TRANSAKSI
    # =========================================
    # Pilih kolom untuk display
    display_df = transactions_df[
        ["Tanggal", "product_name", "quantity", "total_price", "profit"]
    ].copy()
    display_df.columns = ["Tanggal", "Produk", "Qty", "Total Penjualan", "Profit"]

    st.markdown("### 📋 Detail Transaksi")

    # Tampilkan tabel
    st.dataframe(
        display_df.style.format(
            {"Total Penjualan": "Rp {:,.0f}", "Profit": "Rp {:,.0f}"}
        ),
        use_container_width=True,
        height=400,
    )

    # =========================================
    # EXPORT DATA
    # =========================================
    st.markdown("### 📥 Export Data")

    col_export1, col_export2, col_export3 = st.columns([1, 1, 2])

    # Siapkan data untuk export (tanpa formatting Rp)
    export_df = transactions_df[
        ["transaction_date", "product_name", "quantity", "total_price", "profit"]
    ].copy()
    export_df.columns = ["Tanggal", "Produk", "Jumlah", "Total Penjualan", "Profit"]
    export_df["Tanggal"] = export_df["Tanggal"].dt.strftime("%Y-%m-%d %H:%M:%S")

    with col_export1:
        # Export ke CSV
        csv_data = export_df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="📄 Download CSV",
            data=csv_data,
            file_name=f"transaksi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col_export2:
        # Export ke Excel
        # Menggunakan BytesIO untuk membuat file Excel di memory
        from io import BytesIO

        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            export_df.to_excel(writer, index=False, sheet_name="Transaksi")

            # Tambah sheet summary
            summary_data = {
                "Metric": [
                    "Total Transaksi",
                    "Total Item Terjual",
                    "Total Penjualan",
                    "Total Profit",
                ],
                "Nilai": [total_transactions, total_items, total_sales, total_profit],
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, index=False, sheet_name="Summary")

        excel_data = excel_buffer.getvalue()

        st.download_button(
            label="📊 Download Excel",
            data=excel_data,
            file_name=f"transaksi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with col_export3:
        st.caption(
            f"📅 Data periode: {selected_period} | Total {total_transactions} transaksi"
        )


# =====================================================
# MAIN APPLICATION
# =====================================================


def main():
    """
    Fungsi utama yang menjalankan aplikasi.

    Flow:
    1. Initialize database (buat tabel + dummy data jika perlu)
    2. Apply styling
    3. Render semua komponen
    """

    # =========================================
    # INISIALISASI
    # =========================================

    # Initialize database
    is_first_run = db.initialize_database()

    # Apply custom CSS
    apply_custom_css()

    # =========================================
    # HEADER
    # =========================================
    st.markdown("# 📊 Sales & Inventory Intelligence Dashboard")
    st.markdown("*Real-time analytics untuk manajemen penjualan dan inventori*")

    # Tampilkan notifikasi jika pertama kali
    if is_first_run:
        st.success("🎉 Database telah diinisialisasi dengan 50 data dummy transaksi!")

    st.markdown("---")

    # =========================================
    # RENDER SIDEBAR
    # =========================================
    render_sidebar()

    # =========================================
    # RENDER MAIN CONTENT
    # =========================================

    # Tab navigation untuk mengorganisir konten
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📈 Dashboard", "📦 Manajemen Stok", "🤖 Prediksi AI", "📋 Riwayat Transaksi"]
    )

    with tab1:
        render_metrics()
        st.markdown("---")
        render_sales_chart()

    with tab2:
        render_stock_table()

    with tab3:
        render_ai_prediction()

    with tab4:
        render_transaction_history()

    # =========================================
    # FOOTER
    # =========================================
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; padding: 1rem;'>
            <p>📊 Sales & Inventory Intelligence Dashboard</p>
            <p>Built with ❤️ using Streamlit, Pandas, SQLite & Plotly</p>
            <p><small>Portfolio Project - [Abdurrahman AP] | 2025</small></p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =====================================================
# ENTRY POINT
# =====================================================
# Kode di bawah ini hanya dijalankan jika file ini
# dieksekusi langsung (bukan di-import)

if __name__ == "__main__":
    main()
