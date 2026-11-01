from flask import Flask, request, redirect, url_for, session, render_template_string, jsonify, Response, send_file
import sqlite3
import json
import io
import csv
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'kunci_rahasia_wedding_planner_pro_indonesia'
app.jinja_env.globals.update(abs=abs)

def init_db():
    conn = sqlite3.connect('nikah.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE, password TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS settings (
                    user_id INTEGER UNIQUE, groom TEXT, bride TEXT, 
                    wedding_date TEXT, budget INTEGER, theme TEXT DEFAULT 'pink',
                    wali_nikah TEXT, saksi1 TEXT, saksi2 TEXT, mahar_desc TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS vendors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
                    name TEXT, category TEXT, budget_cost INTEGER DEFAULT 0, actual_cost INTEGER DEFAULT 0, 
                    paid INTEGER DEFAULT 0, pay_status TEXT DEFAULT 'DP', bank_info TEXT, 
                    contact TEXT, due_date TEXT, notes TEXT, is_done INTEGER DEFAULT 0)''')

    c.execute('''CREATE TABLE IF NOT EXISTS seserahan (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
                    name TEXT, link TEXT, contact TEXT, budget_cost INTEGER DEFAULT 0, actual_cost INTEGER DEFAULT 0, 
                    paid INTEGER DEFAULT 0, pay_status TEXT DEFAULT 'Lunas', is_bought INTEGER DEFAULT 0)''')

    c.execute('''CREATE TABLE IF NOT EXISTS guests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
                    name TEXT, phone TEXT, side TEXT DEFAULT 'Pihak Pria', invite_status TEXT DEFAULT 'Belum Terkirim',
                    address TEXT, rsvp TEXT DEFAULT 'Menunggu', notes TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS timeline (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
                    time TEXT, activity TEXT, pic TEXT, notes TEXT, is_done INTEGER DEFAULT 0)''')

    c.execute('''CREATE TABLE IF NOT EXISTS checklist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
                    item TEXT, budget_cost INTEGER DEFAULT 0, actual_cost INTEGER DEFAULT 0,
                    paid INTEGER DEFAULT 0, pay_status TEXT DEFAULT 'Lunas', pic TEXT, is_done INTEGER DEFAULT 0)''')

    c.execute('''CREATE TABLE IF NOT EXISTS amplop (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
                    giver_name TEXT, gift_type TEXT DEFAULT 'Uang', amount INTEGER DEFAULT 0, 
                    gift_item TEXT, notes TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS kua_docs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
                    doc_name TEXT, pic TEXT, notes TEXT, is_done INTEGER DEFAULT 0)''')

    c.execute('''CREATE TABLE IF NOT EXISTS seragam (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
                    receiver_name TEXT, side TEXT DEFAULT 'Keluarga Pria', fabric_meter TEXT, status TEXT DEFAULT 'Belum Diberi', notes TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS music_playlist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
                    moment TEXT, song_title TEXT, notes TEXT, is_ready INTEGER DEFAULT 0)''')

    c.execute('''CREATE TABLE IF NOT EXISTS roadmap (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
                    period TEXT DEFAULT 'H-6 Bulan', task TEXT, pic TEXT, notes TEXT, is_done INTEGER DEFAULT 0)''')

    c.execute('''CREATE TABLE IF NOT EXISTS panitia_contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
                    role_name TEXT, person_name TEXT, phone TEXT, notes TEXT)''')

    migrations = [
        ("vendors", "due_date TEXT"),
        ("vendors", "notes TEXT"),
        ("seserahan", "contact TEXT"),
        ("settings", "wali_nikah TEXT"),
        ("settings", "saksi1 TEXT"),
        ("settings", "saksi2 TEXT"),
        ("settings", "mahar_desc TEXT")
    ]
    for table, col in migrations:
        try: c.execute(f"ALTER TABLE {table} ADD COLUMN {col}")
        except: pass

    conn.commit()
    conn.close()

def seed_user_defaults(uid):
    conn = sqlite3.connect('nikah.db')
    c = conn.cursor()
    
    # 1. Vendor & Anggaran Default
    v_count = c.execute("SELECT COUNT(*) FROM vendors WHERE user_id = ?", (uid,)).fetchone()[0]
    if v_count == 0:
        vendor_seeds = [
            ("Venue & Catering", "Sewa Gedung / Venue Utama", 0, 0, 0, "DP", "", "", "", "Kapasitas & AC"),
            ("Venue & Catering", "Paket Katering (Buffet & Gubukan)", 0, 0, 0, "DP", "", "", "", "Menu utama & stall"),
            ("Dekorasi & Tenda", "Dekorasi Pelaminan, Tenda & Lighting", 0, 0, 0, "DP", "", "", "", "Tema warna pastel"),
            ("Busana & Make Up", "MUA Pengantin, Orang Tua & Bridesmaid", 0, 0, 0, "DP", "", "", "", "Termasuk retouch Hari-H"),
            ("Busana & Make Up", "Sewa / Jahit Busana Akad & Resepsi", 0, 0, 0, "DP", "", "", "", "Pengantin & beskap ayah"),
            ("Dokumentasi", "Foto & Video Cinematic Hari-H", 0, 0, 0, "DP", "", "", "", "Album kolase & teaser IG"),
            ("Undangan & Souvenir", "Cetak Souvenir Tamu & Packaging", 0, 0, 0, "Lunas", "", "", "", "Perkiraan jumlah tamu"),
            ("Undangan & Souvenir", "Undangan Digital & Fisik", 0, 0, 0, "Lunas", "", "", "", "Cetak label nama"),
            ("Acara & MC", "Master of Ceremony (MC) & Sound System", 0, 0, 0, "DP", "", "", "", "Akad & Resepsi"),
            ("Lain-lain", "Operasional, Keamanan & Biaya KUA", 0, 0, 0, "Lunas", "", "", "", "Biaya nikah resmi KUA")
        ]
        c.executemany("INSERT INTO vendors (user_id, category, name, budget_cost, actual_cost, paid, pay_status, bank_info, contact, due_date, notes, is_done) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)",
                      [(uid, *v) for v in vendor_seeds])

    # 2. Seserahan Default
    s_count = c.execute("SELECT COUNT(*) FROM seserahan WHERE user_id = ?", (uid,)).fetchone()[0]
    if s_count == 0:
        seserahan_seeds = [
            ("Seperangkat Alat Ibadah (Mukena, Sajadah & Al-Qur'an)", "", "", 0, 0, 0, "Lunas", 0),
            ("Setelan Pakaian Bepergian (Baju, Tas & Sepatu)", "", "", 0, 0, 0, "Lunas", 0),
            ("Baju Tidur & Pakaian Dalam", "", "", 0, 0, 0, "Lunas", 0),
            ("Set Skincare, Bodycare & Make Up Favorit", "", "", 0, 0, 0, "Lunas", 0),
            ("Makanan Tradisional / Kue Kering / Buah Segar", "", "", 0, 0, 0, "Lunas", 0),
            ("Perhiasan / Logam Mulia Tambahan", "", "", 0, 0, 0, "Lunas", 0)
        ]
        c.executemany("INSERT INTO seserahan (user_id, name, link, contact, budget_cost, actual_cost, paid, pay_status, is_bought) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                      [(uid, *s) for s in seserahan_seeds])

    # 3. Berkas KUA Default
    k_count = c.execute("SELECT COUNT(*) FROM kua_docs WHERE user_id = ?", (uid,)).fetchone()[0]
    if k_count == 0:
        kua_seeds = [
            ("Surat Pengantar RT/RW & Kelurahan (Model N1, N2, N4)", "Keluarga", "Minta ke kantor kelurahan asal"),
            ("Sertifikat Vaksin & Cek Kesehatan Puskesmas (Suntik TT)", "Calon Mempelai", "Wajib periksa darah & TT di Puskesmas"),
            ("Pas Foto Background Biru (Ukuran 2x3 & 4x6)", "Mempelai Pria/Wanita", "Bawa foto cetak fisik kemeja rapi"),
            ("Fotokopi KTP, KK, Akta Lahir & Ijazah Terakhir", "Calon Mempelai", "Lampirkan rangkap 2"),
            ("Pendaftaran Online di Web Simkah / KUA Setempat", "Mempelai Pria", "Daftar H-30 hari sebelum akad")
        ]
        c.executemany("INSERT INTO kua_docs (user_id, doc_name, pic, notes, is_done) VALUES (?, ?, ?, ?, 0)",
                      [(uid, *k) for k in kua_seeds])

    # 4. Playlist Lagu Default
    m_count = c.execute("SELECT COUNT(*) FROM music_playlist WHERE user_id = ?", (uid,)).fetchone()[0]
    if m_count == 0:
        music_seeds = [
            ("Grand Entrance (Masuk Pelaminan)", "A Thousand Years / Sampai Jadi Debu", "Musik megah & romantis"),
            ("Sungkeman Orang Tua", "Bunda / Doa Pengantin / Instrumen Biola Haru", "Suasana hening dan khidmat"),
            ("Lempar Bunga / Wedding Kiss", "Marry You - Bruno Mars / Happy", "Suasana ceria bersama teman"),
            ("Santap Makan & Foto Bersama", "Accoustic Pop Romance Playlist", "Volume ramah obrolan tamu")
        ]
        c.executemany("INSERT INTO music_playlist (user_id, moment, song_title, notes, is_ready) VALUES (?, ?, ?, ?, 0)",
                      [(uid, *m) for m in music_seeds])

    # 5. Checklist Darurat Default
    c_count = c.execute("SELECT COUNT(*) FROM checklist WHERE user_id = ?", (uid,)).fetchone()[0]
    if c_count == 0:
        chk_seeds = [
            ("Jarum Pentul, Peniti & Double Tape", "WO / Bridesmaid"),
            ("Kotak P3K, Minyak Angin & Obat Maag/Pusing", "Keluarga Inti"),
            ("Sandal / Sepatu Cadangan Nyaman (Tanpa Hak)", "Pengantin Wanita"),
            ("Permen Pelega Tenggorokan & Tisu Basah/Kering", "Bridesmaid"),
            ("Powerbank & Charger HP", "PIC Dokumentasi")
        ]
        c.executemany("INSERT INTO checklist (user_id, item, budget_cost, actual_cost, paid, pay_status, pic, is_done) VALUES (?, ?, 0, 0, 0, 'Lunas', ?, 0)",
                      [(uid, *c) for c in chk_seeds])

    # 6. Roadmap Bulanan Default (BARU!)
    r_count = c.execute("SELECT COUNT(*) FROM roadmap WHERE user_id = ?", (uid,)).fetchone()[0]
    if r_count == 0:
        roadmap_seeds = [
            ("H-6 Bulan", "Booking Venue Gedung & Tentukan Tanggal Akad", "Kedua Keluarga", "Kunci tanggal sebelum penuh"),
            ("H-6 Bulan", "Pilih Vendor Katering & Lakukan Test Food", "Pengantin", "Pilih menu prasmanan & gubukan"),
            ("H-3 Bulan", "Pengurusan Surat N1-N4 ke Kelurahan & KUA", "Mempelai Pria/Wanita", "Urus berkas & suntik TT"),
            ("H-3 Bulan", "Finalisasi Desain Undangan & Souvenir Tamu", "Pengantin", "Cetak fisik & siapkan undangan web"),
            ("H-1 Bulan", "Fitting Busana Terakhir Pengantin & Orang Tua", "Pengantin", "Pastikan tidak sempit/kebesaran"),
            ("H-1 Bulan", "Technical Meeting (TM) Seluruh Vendor & Panitia", "WO / Ketua Panitia", "Bahas detail rundown acara"),
            ("H-2 Minggu", "Konfirmasi Ulang Semua Vendor & Pelunasan", "Pengantin", "Gedung, katering, MUA, dekorasi"),
            ("H-1 Minggu", "Serah Terima Barang Seserahan & Cincin Kawin", "Keluarga Inti", "Cek kelengkapan jangan tertinggal"),
            ("H-1 Hari", "Gladi Bersih Akad & Istirahat Total", "Kedua Pengantin", "Jaga stamina dan jangan begadang")
        ]
        c.executemany("INSERT INTO roadmap (user_id, period, task, pic, notes, is_done) VALUES (?, ?, ?, ?, ?, 0)",
                      [(uid, *r) for r in roadmap_seeds])

    # 7. Kontak Cepat Panitia Inti Default (BARU!)
    p_count = c.execute("SELECT COUNT(*) FROM panitia_contacts WHERE user_id = ?", (uid,)).fetchone()[0]
    if p_count == 0:
        panitia_seeds = [
            ("Ketua Panitia / Koordinator WO", "Pak Budi / Mas Dimas", "081234567890", "Penanggung jawab seluruh lapangan"),
            ("Pembawa Cincin & Mahar", "Adik / Saudara Kandung", "081234567891", "Wajib standby dekat meja ijab qabul"),
            ("PIC Makanan & Katering Keluarga", "Tante / Paman", "081234567892", "Pantau stok makanan buffet & gubukan"),
            ("Sopir Mobil Pengantin", "Pak Joko", "081234567893", "Standby H-2 jam sebelum acara dimulai"),
            ("PIC Keamanan & Kotak Amplop", "Om Hendra", "081234567894", "Pegang kunci gembok kotak angpao"),
            ("Penghulu / Petugas KUA", "Kantor KUA Setempat", "081234567895", "Konfirmasi kehadiran H-1 & jam akad")
        ]
        c.executemany("INSERT INTO panitia_contacts (user_id, role_name, person_name, phone, notes) VALUES (?, ?, ?, ?, ?)",
                      [(uid, *p) for p in panitia_seeds])

    conn.commit()
    conn.close()

init_db()

APP_HTML = '''
<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Wedding Planner Pro - Dashboard Lengkap</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    @media print {
      body * { visibility: hidden; }
      #printable-area, #printable-area *, #printable-panitia, #printable-panitia * { visibility: visible; }
      #printable-area, #printable-panitia { position: absolute; left: 0; top: 0; width: 100%; }
      .no-print { display: none !important; }
    }
  </style>
</head>

{% set is_pink = (s[5] == 'pink') %}
{% set bg_main = 'bg-rose-50/80 text-rose-950' if is_pink else 'bg-sky-50/80 text-slate-900' %}
{% set card_box = 'bg-rose-100/60 border border-rose-200/80 shadow-sm' if is_pink else 'bg-sky-100/60 border border-sky-200/80 shadow-sm' %}
{% set thead_style = 'bg-rose-200/70 text-rose-900 border-rose-200' if is_pink else 'bg-sky-200/70 text-sky-900 border-sky-200' %}
{% set input_style = 'bg-rose-50/90 border border-rose-200 text-rose-950 focus:bg-white focus:outline-none focus:ring-1 focus:ring-rose-400' if is_pink else 'bg-sky-50/90 border border-sky-200 text-slate-900 focus:bg-white focus:outline-none focus:ring-1 focus:ring-sky-400' %}
{% set btn_inactive_tab = 'bg-rose-200/60 text-rose-800 hover:bg-rose-300/60' if is_pink else 'bg-sky-200/60 text-sky-800 hover:bg-sky-300/60' %}
{% set btn_primary = 'bg-rose-400 hover:bg-rose-500 text-white font-bold shadow-sm' if is_pink else 'bg-sky-500 hover:bg-sky-600 text-white font-bold shadow-sm' %}

<body class="{{ bg_main }} min-h-screen pb-28 font-sans">

  <div id="toast" class="fixed bottom-6 right-6 {{ 'bg-rose-600' if is_pink else 'bg-sky-600' }} text-white text-xs px-4 py-3 rounded-2xl shadow-xl flex items-center gap-2 transform transition-all duration-300 translate-y-20 opacity-0 z-50">
    <i class="fa-solid fa-circle-check text-base"></i>
    <span id="toast-msg" class="font-bold">Tersimpan!</span>
  </div>

  <div class="no-print {{ 'bg-gradient-to-r from-rose-300 via-pink-300 to-rose-400 text-rose-950' if is_pink else 'bg-gradient-to-r from-sky-300 via-blue-300 to-sky-400 text-slate-900' }} p-6 shadow-sm rounded-b-3xl max-w-6xl mx-auto text-center relative border-b {{ 'border-rose-300' if is_pink else 'border-sky-300' }}">
    <div class="flex justify-between items-center text-xs font-semibold mb-2">
      <span class="bg-white/40 px-3 py-1 rounded-full"><i class="fa-solid fa-heart mr-1"></i> {{ username }}</span>
      <a href="/logout" class="bg-white/40 hover:bg-white/60 px-3 py-1 rounded-full transition"><i class="fa-solid fa-right-from-bracket"></i> Keluar</a>
    </div>
    <h1 class="text-3xl font-extrabold tracking-wide font-serif">{{ s[1] }} & {{ s[2] }}</h1>
    <p class="text-xs font-semibold mt-1 opacity-90"><i class="fa-regular fa-calendar-heart mr-1"></i> {{ s[3] }}</p>
    <div id="countdown" class="mt-2 bg-white/50 backdrop-blur-sm py-1 px-4 rounded-full inline-block text-xs font-bold text-gray-800 shadow-sm"></div>

    <div class="mt-4 bg-white/40 p-3.5 rounded-2xl max-w-lg mx-auto text-left shadow-sm border border-white/50">
      <div class="flex justify-between text-xs font-bold mb-1">
        <span><i class="fa-solid fa-chart-pie mr-1"></i> Akumulasi Kesiapan Keseluruhan Acara</span>
        <span class="text-sm font-extrabold">{{ overall_pct }}%</span>
      </div>
      <div class="w-full bg-white/60 rounded-full h-3 overflow-hidden">
        <div class="{{ 'bg-rose-500' if is_pink else 'bg-sky-600' }} h-3 rounded-full transition-all duration-500" style="width: {{ overall_pct }}%"></div>
      </div>
      <p class="text-[10px] text-gray-700 mt-1 text-center font-medium">Rata-rata kesiapan persiapan pernikahan</p>
    </div>
  </div>

  <div class="max-w-6xl mx-auto px-4 mt-4 space-y-4">

    <div class="no-print flex overflow-x-auto space-x-2 pb-2 scrollbar-none text-xs font-semibold">
      <button onclick="tab('dashboard')" id="btn-dashboard" class="tab-btn px-4 py-2 rounded-xl {{ btn_inactive_tab }} transition font-bold"><i class="fa-solid fa-gauge-high mr-1"></i> Dashboard</button>
      <button onclick="tab('roadmap')" id="btn-roadmap" class="tab-btn px-4 py-2 rounded-xl {{ btn_inactive_tab }} transition font-bold text-indigo-900"><i class="fa-solid fa-route mr-1"></i> Roadmap Bulanan</button>
      <button onclick="tab('vendor')" id="btn-vendor" class="tab-btn px-4 py-2 rounded-xl {{ btn_inactive_tab }} transition"><i class="fa-solid fa-handshake mr-1"></i> Vendor & Anggaran</button>
      <button onclick="tab('seserahan')" id="btn-seserahan" class="tab-btn px-4 py-2 rounded-xl {{ btn_inactive_tab }} transition"><i class="fa-solid fa-gift mr-1"></i> Seserahan</button>
      <button onclick="tab('tamu')" id="btn-tamu" class="tab-btn px-4 py-2 rounded-xl {{ btn_inactive_tab }} transition"><i class="fa-solid fa-users mr-1"></i> Tamu Undangan</button>
      <button onclick="tab('amplop')" id="btn-amplop" class="tab-btn px-4 py-2 rounded-xl {{ btn_inactive_tab }} transition font-bold text-emerald-800"><i class="fa-solid fa-envelope-open-text mr-1"></i> Buku Amplop</button>
      <button onclick="tab('panitia')" id="btn-panitia" class="tab-btn px-4 py-2 rounded-xl {{ btn_inactive_tab }} transition font-bold text-rose-800"><i class="fa-solid fa-phone-volume mr-1"></i> Kontak Panitia Inti</button>
      <button onclick="tab('kua')" id="btn-kua" class="tab-btn px-4 py-2 rounded-xl {{ btn_inactive_tab }} transition"><i class="fa-solid fa-book-bookmark mr-1"></i> Berkas KUA & Mahar</button>
      <button onclick="tab('rundown')" id="btn-rundown" class="tab-btn px-4 py-2 rounded-xl {{ btn_inactive_tab }} transition"><i class="fa-solid fa-clock mr-1"></i> Rundown & Musik</button>
      <button onclick="tab('seragam')" id="btn-seragam" class="tab-btn px-4 py-2 rounded-xl {{ btn_inactive_tab }} transition"><i class="fa-solid fa-vest mr-1"></i> Seragam Keluarga</button>
      <button onclick="tab('darurat')" id="btn-darurat" class="tab-btn px-4 py-2 rounded-xl {{ btn_inactive_tab }} transition"><i class="fa-solid fa-kit-medical mr-1"></i> Darurat</button>
      <button onclick="tab('pengaturan')" id="btn-pengaturan" class="tab-btn px-4 py-2 rounded-xl {{ btn_inactive_tab }} transition"><i class="fa-solid fa-gear"></i></button>
    </div>

    <!-- 1. DASHBOARD -->
    <div id="tab-dashboard" class="tab-pane space-y-4">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
        <div class="{{ card_box }} p-3.5 rounded-2xl">
          <span class="opacity-75 font-medium block">Target Budget Acara</span>
          <b class="text-base font-extrabold block mt-0.5">Rp {{ "{:,.0f}".format(s[4] or 0).replace(",", ".") }}</b>
          <span class="text-[10px] opacity-70">Ditentukan di pengaturan</span>
        </div>
        <div class="{{ card_box }} p-3.5 rounded-2xl">
          <span class="opacity-75 font-medium block">Total Estimasi Rencana</span>
          <b class="text-base font-extrabold block mt-0.5">Rp {{ "{:,.0f}".format(total_est).replace(",", ".") }}</b>
          <span class="text-[10px] opacity-70">Perkiraan seluruh vendor</span>
        </div>
        <div class="{{ card_box }} p-3.5 rounded-2xl">
          <span class="opacity-75 font-medium block">Total Realisasi / Deal</span>
          <b class="text-base font-extrabold {{ 'text-rose-700' if is_pink else 'text-sky-700' }} block mt-0.5">Rp {{ "{:,.0f}".format(total_real).replace(",", ".") }}</b>
          <span class="text-[10px] font-bold {{ 'text-emerald-700' if selisih >= 0 else 'text-rose-700' }}">
            {{ 'Hemat Rp ' if selisih >= 0 else 'Over Rp ' }}{{ "{:,.0f}".format(abs_selisih).replace(",", ".") }}
          </span>
        </div>
        <div class="{{ card_box }} p-3.5 rounded-2xl">
          <span class="opacity-75 font-medium block">Sisa Pembayaran (Utang)</span>
          <b class="text-base font-extrabold text-amber-700 block mt-0.5">Rp {{ "{:,.0f}".format(sisa_bayar).replace(",", ".") }}</b>
          <span class="text-[10px] opacity-70">Sudah bayar: Rp {{ "{:,.0f}".format(total_paid).replace(",", ".") }}</span>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="{{ card_box }} p-4 rounded-2xl flex flex-col items-center">
          <h3 class="text-xs font-bold mb-2 opacity-90"><i class="fa-solid fa-chart-pie mr-1"></i> Komposisi Biaya per Kategori Pos</h3>
          <div class="w-full max-w-[280px] h-[220px] flex items-center justify-center">
            <canvas id="categoryPieChart"></canvas>
          </div>
        </div>

        <div class="{{ card_box }} p-4 rounded-2xl flex flex-col items-center">
          <h3 class="text-xs font-bold mb-2 opacity-90"><i class="fa-solid fa-chart-column mr-1"></i> Estimasi vs Realisasi per Pos (Rp)</h3>
          <div class="w-full h-[220px]">
            <canvas id="comparisonBarChart"></canvas>
          </div>
        </div>
      </div>

      <div class="{{ card_box }} p-4 rounded-2xl">
        <div class="flex flex-wrap justify-between items-center border-b {{ 'border-rose-200' if is_pink else 'border-sky-200' }} pb-2 mb-3">
          <div>
            <h3 class="text-xs font-bold text-indigo-900"><i class="fa-solid fa-calculator mr-1"></i> Kalkulator Porsi Katering & Makanan Otomatis</h3>
            <p class="text-[10px] opacity-75">Formula standar pernikahan Indonesia (Rasio 60% Buffet : 40% Gubukan)</p>
          </div>
          <div class="flex items-center gap-2 mt-2 sm:mt-0">
            <label class="text-xs font-bold">Jumlah Undangan:</label>
            <input type="number" id="catering_invites" value="300" oninput="calcCatering()" class="w-24 p-1.5 rounded-lg text-xs font-bold text-center {{ input_style }}">
          </div>
        </div>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-center text-xs">
          <div class="bg-white/40 p-2.5 rounded-xl">
            <span class="opacity-75 text-[10px] block">Estimasi Tamu Hadir</span>
            <b id="c_total_pax" class="text-sm font-bold text-indigo-700">600 Orang</b>
            <span class="text-[9px] opacity-70 block">(Undangan × 2)</span>
          </div>
          <div class="bg-white/40 p-2.5 rounded-xl">
            <span class="opacity-75 text-[10px] block">Rekomendasi Prasmanan (Buffet)</span>
            <b id="c_buffet" class="text-sm font-bold text-emerald-700">360 Porsi</b>
            <span class="text-[9px] opacity-70 block">(60% dari total tamu)</span>
          </div>
          <div class="bg-white/40 p-2.5 rounded-xl">
            <span class="opacity-75 text-[10px] block">Rekomendasi Total Porsi Gubukan</span>
            <b id="c_stall" class="text-sm font-bold text-amber-700">960 Porsi</b>
            <span class="text-[9px] opacity-70 block">(40% × 4 variasi menu)</span>
          </div>
          <div class="bg-white/40 p-2.5 rounded-xl">
            <span class="opacity-75 text-[10px] block">Estimasi Air Minum (Cup/Botol)</span>
            <b id="c_water" class="text-sm font-bold text-sky-700">720 Cup / Botol</b>
            <span class="text-[9px] opacity-70 block">(~15 Dus cup kemasan)</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 2. ROADMAP PERSAPAN BULANAN (FITUR BARU!) -->
    <div id="tab-roadmap" class="tab-pane hidden space-y-3">
      <div class="{{ card_box }} p-3.5 rounded-2xl flex flex-wrap gap-2 justify-between items-center text-xs">
        <div>
          <span class="font-bold text-indigo-900 text-sm"><i class="fa-solid fa-route mr-1"></i> Roadmap Tahapan Persiapan (H-6 Bulan s/d H-1 Hari)</span>
          <p class="text-[11px] opacity-75 mt-0.5">Panduan persiapan bertahap agar tidak ada agenda penting yang terlewatkan</p>
        </div>
      </div>

      <div class="{{ card_box }} rounded-2xl overflow-x-auto p-2">
        <table class="w-full text-left text-xs whitespace-nowrap">
          <thead class="{{ thead_style }} rounded-xl border-b text-[11px]">
            <tr>
              <th class="p-2 text-center rounded-l-lg">Selesai?</th>
              <th class="p-2 min-w-[130px]">Fase / Periode</th>
              <th class="p-2 min-w-[260px]">Agenda / Target Pekerjaan</th>
              <th class="p-2 min-w-[140px]">Penanggung Jawab (PIC)</th>
              <th class="p-2 min-w-[200px]">Catatan / Tips Tambahan</th>
              <th class="p-2 text-center rounded-r-lg">Aksi</th>
            </tr>
          </thead>
          <tbody id="tbody-roadmap" class="divide-y {{ 'divide-rose-200/60' if is_pink else 'divide-sky-200/60' }}">
            {% for r in roadmap %}
            <tr id="row-roadmap-{{ r[0] }}" class="hover:bg-white/40 transition {{ 'bg-emerald-100/40' if r[5] else '' }}">
              <td class="p-2 text-center">
                <button type="button" onclick="ajaxToggle('roadmap', {{ r[0] }}, this)" class="text-base {{ 'text-emerald-500' if r[5] else 'text-gray-300 hover:text-emerald-500' }}"><i class="fa-solid fa-circle-check"></i></button>
              </td>
              <td class="p-2">
                <select name="period" class="w-full p-1.5 rounded-lg text-xs font-bold {{ input_style }}">
                  <option value="H-6 Bulan" {{ 'selected' if r[2]=='H-6 Bulan' }}>H-6 Bulan</option>
                  <option value="H-3 Bulan" {{ 'selected' if r[2]=='H-3 Bulan' }}>H-3 Bulan</option>
                  <option value="H-1 Bulan" {{ 'selected' if r[2]=='H-1 Bulan' }}>H-1 Bulan</option>
                  <option value="H-2 Minggu" {{ 'selected' if r[2]=='H-2 Minggu' }}>H-2 Minggu</option>
                  <option value="H-1 Minggu" {{ 'selected' if r[2]=='H-1 Minggu' }}>H-1 Minggu</option>
                  <option value="H-1 Hari" {{ 'selected' if r[2]=='H-1 Hari' }}>H-1 Hari</option>
                </select>
              </td>
              <td class="p-2"><input type="text" name="task" value="{{ r[3] }}" class="w-full p-1.5 rounded-lg text-xs font-semibold {{ input_style }} {{ 'line-through opacity-60' if r[5] }}"></td>
              <td class="p-2"><input type="text" name="pic" value="{{ r[4] or '' }}" placeholder="PIC..." class="w-full p-1.5 rounded-lg text-xs {{ input_style }}"></td>
              <td class="p-2"><input type="text" name="notes" value="{{ r[5] or '' }}" placeholder="Catatan..." class="w-full p-1.5 rounded-lg text-xs {{ input_style }}"></td>
              <td class="p-2 text-center whitespace-nowrap">
                <button type="button" onclick="ajaxSaveRow('roadmap', {{ r[0] }}, this)" class="bg-indigo-400 hover:bg-indigo-500 text-white font-bold p-1.5 rounded-lg text-xs mr-1 shadow-sm"><i class="fa-solid fa-floppy-disk"></i></button>
                <button type="button" onclick="ajaxDeleteRow('roadmap', {{ r[0] }}, this)" class="text-rose-400 hover:text-rose-600 p-1.5"><i class="fa-solid fa-trash"></i></button>
              </td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
        <div class="p-3 {{ 'bg-rose-200/40' if is_pink else 'bg-sky-200/40' }} rounded-b-xl border-t {{ 'border-rose-200' if is_pink else 'border-sky-200' }}">
          <button type="button" onclick="ajaxAddRow('roadmap')" class="bg-indigo-500 hover:bg-indigo-600 text-white font-bold py-2 px-4 rounded-xl text-xs inline-flex items-center gap-1 transition">
            <i class="fa-solid fa-plus"></i> Tambah Target Roadmap Baru
          </button>
        </div>
      </div>
    </div>

    <!-- 3. VENDOR & ANGGARAN -->
    <div id="tab-vendor" class="tab-pane hidden space-y-3">
      <div class="{{ card_box }} p-3.5 rounded-2xl flex flex-wrap gap-2 justify-between items-center text-xs">
        <div>
          <span class="font-bold text-indigo-800 text-sm"><i class="fa-solid fa-receipt mr-1"></i> Daftar Seluruh Vendor & Pos Anggaran</span>
          <p class="text-[11px] opacity-75 mt-0.5">Status Pelunasan: <b>{{ ven_done }} / {{ ven_total }} Selesai</b> ({{ ven_pct }}%) | Realisasi: <b>Rp {{ "{:,.0f}".format(total_real).replace(",", ".") }}</b></p>
        </div>
        <div class="relative">
          <input type="text" onkeyup="filterTable('tbody-vendors', this.value)" placeholder="Cari vendor / pos..." class="p-1.5 pl-7 rounded-xl text-xs bg-white/80 border border-indigo-200 focus:outline-none focus:ring-1 focus:ring-indigo-400">
          <i class="fa-solid fa-magnifying-glass absolute left-2.5 top-2.5 text-gray-400 text-[10px]"></i>
        </div>
      </div>

      <div class="{{ card_box }} rounded-2xl overflow-x-auto p-2">
        <table class="w-full text-left text-xs whitespace-nowrap">
          <thead class="{{ thead_style }} rounded-xl border-b text-[11px]">
            <tr>
              <th class="p-2 text-center rounded-l-lg">Lunas?</th>
              <th class="p-2 min-w-[130px]">Kategori Pos</th>
              <th class="p-2 min-w-[170px]">Nama Pos / Vendor</th>
              <th class="p-2 min-w-[150px]">No. Rekening & Bank</th>
              <th class="p-2 min-w-[105px]">Estimasi (Rp)</th>
              <th class="p-2 min-w-[105px]">Realisasi (Rp)</th>
              <th class="p-2 min-w-[90px]">Status</th>
              <th class="p-2 min-w-[105px]">Dibayar (Rp)</th>
              <th class="p-2 min-w-[105px]">Sisa Bayar</th>
              <th class="p-2 min-w-[120px]">Kontak / WA</th>
              <th class="p-2 min-w-[120px]">Jatuh Tempo DP</th>
              <th class="p-2 min-w-[140px]">Catatan Pos</th>
              <th class="p-2 text-center rounded-r-lg">Aksi</th>
            </tr>
          </thead>
          <tbody id="tbody-vendors" class="divide-y {{ 'divide-rose-200/60' if is_pink else 'divide-sky-200/60' }}">
            {% for v in vendors %}
            <tr id="row-vendors-{{ v[0] }}" class="hover:bg-white/40 transition {{ 'bg-emerald-100/40' if v[7]=='Lunas' else '' }}">
              <td class="p-2 text-center">
                <button type="button" onclick="ajaxToggle('vendors', {{ v[0] }}, this)" class="text-base {{ 'text-emerald-500' if v[7]=='Lunas' else 'text-gray-300 hover:text-emerald-500' }}"><i class="fa-solid fa-circle-check"></i></button>
              </td>
              <td class="p-2">
                <select name="category" class="w-full p-1.5 rounded-lg text-xs {{ input_style }}">
                  <option value="Venue & Catering" {{ 'selected' if v[3]=='Venue & Catering' }}>Venue & Catering</option>
                  <option value="Dekorasi & Tenda" {{ 'selected' if v[3]=='Dekorasi & Tenda' }}>Dekorasi & Tenda</option>
                  <option value="Busana & Make Up" {{ 'selected' if v[3]=='Busana & Make Up' }}>Busana & Make Up</option>
                  <option value="Dokumentasi" {{ 'selected' if v[3]=='Dokumentasi' }}>Dokumentasi</option>
                  <option value="Undangan & Souvenir" {{ 'selected' if v[3]=='Undangan & Souvenir' }}>Undangan & Souvenir</option>
                  <option value="Acara & MC" {{ 'selected' if v[3]=='Acara & MC' }}>Acara & MC</option>
                  <option value="Lain-lain" {{ 'selected' if v[3]=='Lain-lain' or not v[3] }}>Lain-lain</option>
                </select>
              </td>
              <td class="p-2"><input type="text" name="name" value="{{ v[2] }}" class="w-full p-1.5 rounded-lg text-xs font-semibold {{ input_style }}"></td>
              <td class="p-2"><input type="text" name="bank_info" value="{{ v[8] or '' }}" placeholder="BCA 1234 a/n..." class="w-full p-1.5 rounded-lg text-xs font-mono {{ input_style }}"></td>
              <td class="p-2"><input type="number" name="budget_cost" value="{{ v[4] or 0 }}" class="w-full p-1.5 rounded-lg text-xs {{ input_style }}"></td>
              <td class="p-2"><input type="number" name="actual_cost" value="{{ v[5] or 0 }}" oninput="calcSisa(this)" class="w-full p-1.5 rounded-lg text-xs font-bold {{ input_style }}"></td>
              <td class="p-2">
                <select name="pay_status" class="w-full p-1.5 rounded-lg text-xs font-bold {{ input_style }}">
                  <option value="DP" {{ 'selected' if v[7]=='DP' }}>DP</option>
                  <option value="Lunas" {{ 'selected' if v[7]=='Lunas' }}>Lunas</option>
                </select>
              </td>
              <td class="p-2"><input type="number" name="paid" value="{{ v[6] or 0 }}" oninput="calcSisa(this)" class="w-full p-1.5 rounded-lg text-xs {{ input_style }}"></td>
              <td class="p-2 font-bold text-amber-700 sisa-val">Rp {{ "{:,.0f}".format((v[5] or 0) - (v[6] or 0)).replace(",", ".") }}</td>
              <td class="p-2"><input type="text" name="contact" value="{{ v[9] or '' }}" placeholder="WA/Telp..." class="w-full p-1.5 rounded-lg text-xs {{ input_style }}"></td>
              <td class="p-2"><input type="date" name="due_date" value="{{ v[10] or '' }}" class="p-1 rounded-lg text-[11px] {{ input_style }}"></td>
              <td class="p-2"><input type="text" name="notes" value="{{ v[11] or '' }}" placeholder="Catatan pos..." class="w-full p-1.5 rounded-lg text-xs {{ input_style }}"></td>
              <td class="p-2 text-center whitespace-nowrap">
                <button type="button" onclick="ajaxSaveRow('vendors', {{ v[0] }}, this)" class="bg-indigo-400 hover:bg-indigo-500 text-white font-bold p-1.5 rounded-lg text-xs mr-1 shadow-sm"><i class="fa-solid fa-floppy-disk"></i></button>
                <button type="button" onclick="ajaxDeleteRow('vendors', {{ v[0] }}, this)" class="text-rose-400 hover:text-rose-600 p-1.5"><i class="fa-solid fa-trash"></i></button>
              </td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
        <div class="p-3 {{ 'bg-rose-200/40' if is_pink else 'bg-sky-200/40' }} rounded-b-xl border-t {{ 'border-rose-200' if is_pink else 'border-sky-200' }}">
          <button type="button" onclick="ajaxAddRow('vendors')" class="bg-indigo-500 hover:bg-indigo-600 text-white font-bold py-2 px-4 rounded-xl text-xs inline-flex items-center gap-1 transition">
            <i class="fa-solid fa-plus"></i> Tambah Pos / Vendor Baru
          </button>
        </div>
      </div>
    </div>

    <!-- 4. SESERAHAN -->
    <div id="tab-seserahan" class="tab-pane hidden space-y-3">
      <div class="{{ card_box }} p-3 rounded-2xl flex justify-between items-center text-xs">
        <span class="font-bold text-emerald-800"><i class="fa-solid fa-gift mr-1"></i> Seserahan Dibeli: {{ ses_bought }}/{{ ses_total }} ({{ ses_pct }}%)</span>
      </div>
      <div class="{{ card_box }} rounded-2xl overflow-x-auto p-2">
        <table class="w-full text-left text-xs whitespace-nowrap">
          <thead class="{{ thead_style }} rounded-xl border-b text-[11px]">
            <tr>
              <th class="p-2 text-center rounded-l-lg">Sudah Beli?</th>
              <th class="p-2 min-w-[180px]">Nama Barang Seserahan</th>
              <th class="p-2 min-w-[140px]">Link Toko Online</th>
              <th class="p-2 min-w-[130px]">Kontak Toko / WA</th>
              <th class="p-2 min-w-[110px]">Estimasi (Rp)</th>
              <th class="p-2 min-w-[110px]">Realisasi (Rp)</th>
              <th class="p-2 min-w-[100px]">Status</th>
              <th class="p-2 min-w-[110px]">Dibayar (Rp)</th>
              <th class="p-2 min-w-[110px]">Sisa Bayar</th>
              <th class="p-2 text-center rounded-r-lg">Aksi</th>
            </tr>
          </thead>
          <tbody id="tbody-seserahan" class="divide-y {{ 'divide-rose-200/60' if is_pink else 'divide-sky-200/60' }}">
            {% for ses in seserahan %}
            <tr id="row-seserahan-{{ ses[0] }}" class="hover:bg-white/40 transition {{ 'bg-emerald-100/40' if ses[8] else '' }}">
              <td class="p-2 text-center">
                <button type="button" onclick="ajaxToggle('seserahan', {{ ses[0] }}, this)" class="text-base {{ 'text-emerald-500' if ses[8] else 'text-gray-300 hover:text-emerald-500' }}"><i class="fa-solid fa-circle-check"></i></button>
              </td>
              <td class="p-2"><input type="text" name="name" value="{{ ses[2] }}" class="w-full p-1.5 rounded-lg text-xs font-semibold {{ input_style }} {{ 'line-through opacity-60' if ses[8] }}"></td>
              <td class="p-2">
                <div class="flex gap-1 items-center">
                  <input type="url" name="link" value="{{ ses[3] or '' }}" placeholder="https://..." class="w-full p-1.5 rounded-lg text-xs {{ input_style }}">
                  {% if ses[3] %}<a href="{{ ses[3] }}" target="_blank" class="text-blue-600 p-1.5 bg-blue-100 rounded-lg"><i class="fa-solid fa-arrow-up-right-from-square"></i></a>{% endif %}
                </div>
              </td>
              <td class="p-2"><input type="text" name="contact" value="{{ ses[4] or '' }}" placeholder="WA Toko..." class="w-full p-1.5 rounded-lg text-xs {{ input_style }}"></td>
              <td class="p-2"><input type="number" name="budget_cost" value="{{ ses[5] or 0 }}" class="w-full p-1.5 rounded-lg text-xs {{ input_style }}"></td>
              <td class="p-2"><input type="number" name="actual_cost" value="{{ ses[6] or 0 }}" oninput="calcSisa(this)" class="w-full p-1.5 rounded-lg text-xs font-bold {{ input_style }}"></td>
              <td class="p-2">
                <select name="pay_status" class="w-full p-1.5 rounded-lg text-xs font-bold {{ input_style }}">
                  <option value="DP" {{ 'selected' if ses[8]=='DP' }}>DP</option>
                  <option value="Lunas" {{ 'selected' if ses[8]=='Lunas' }}>Lunas</option>
                </select>
              </td>
              <td class="p-2"><input type="number" name="paid" value="{{ ses[7] or 0 }}" oninput="calcSisa(this)" class="w-full p-1.5 rounded-lg text-xs {{ input_style }}"></td>
              <td class="p-2 font-bold text-amber-700 sisa-val">Rp {{ "{:,.0f}".format((ses[6] or 0) - (ses[7] or 0)).replace(",", ".") }}</td>
              <td class="p-2 text-center whitespace-nowrap">
                <button type="button" onclick="ajaxSaveRow('seserahan', {{ ses[0] }}, this)" class="bg-emerald-400 hover:bg-emerald-500 text-white font-bold p-1.5 rounded-lg text-xs mr-1 shadow-sm"><i class="fa-solid fa-floppy-disk"></i></button>
                <button type="button" onclick="ajaxDeleteRow('seserahan', {{ ses[0] }}, this)" class="text-rose-400 hover:text-rose-600 p-1.5"><i class="fa-solid fa-trash"></i></button>
              </td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
        <div class="p-3 {{ 'bg-rose-200/40' if is_pink else 'bg-sky-200/40' }} rounded-b-xl border-t {{ 'border-rose-200' if is_pink else 'border-sky-200' }}">
          <button type="button" onclick="ajaxAddRow('seserahan')" class="bg-emerald-400 hover:bg-emerald-500 text-white font-bold py-2 px-4 rounded-xl text-xs inline-flex items-center gap-1 transition">
            <i class="fa-solid fa-plus"></i> Tambah Baris Seserahan
          </button>
        </div>
      </div>
    </div>

    <!-- 5. TAMU UNDANGAN -->
    <div id="tab-tamu" class="tab-pane hidden space-y-3">
      <div class="{{ card_box }} p-3 rounded-2xl flex flex-wrap gap-2 justify-between items-center text-xs">
        <span class="font-bold text-purple-800"><i class="fa-solid fa-envelope-circle-check mr-1"></i> Undangan Terkirim: {{ invite_sent }}/{{ guest_total }} ({{ invite_pct }}%) | Hadir: {{ guest_hadir }} Orang</span>
        
        <div class="flex items-center gap-2">
          <div class="relative">
            <input type="text" onkeyup="filterTable('tbody-guests', this.value)" placeholder="Cari nama tamu..." class="p-1.5 pl-7 rounded-xl text-xs bg-white/80 border border-purple-200 focus:outline-none focus:ring-1 focus:ring-purple-400">
            <i class="fa-solid fa-magnifying-glass absolute left-2.5 top-2.5 text-gray-400 text-[10px]"></i>
          </div>
          <a href="/export_guests_csv" class="bg-emerald-500 hover:bg-emerald-600 text-white px-3 py-1.5 rounded-xl font-bold transition flex items-center gap-1 shadow-sm">
            <i class="fa-solid fa-file-excel"></i> Export Excel
          </a>
        </div>
      </div>

      <div class="{{ card_box }} rounded-2xl overflow-x-auto p-2">
        <table class="w-full text-left text-xs whitespace-nowrap">
          <thead class="{{ thead_style }} rounded-xl border-b text-[11px]">
            <tr>
              <th class="p-2 min-w-[170px] rounded-l-lg">Nama Tamu / Keluarga</th>
              <th class="p-2 min-w-[130px]">No. WhatsApp</th>
              <th class="p-2 min-w-[110px]">Pihak</th>
              <th class="p-2 min-w-[130px]">Status Undangan</th>
              <th class="p-2 min-w-[180px]">Alamat</th>
              <th class="p-2 min-w-[110px]">Kehadiran</th>
              <th class="p-2 min-w-[140px]">Catatan</th>
              <th class="p-2 text-center rounded-r-lg">Aksi & Kirim WA</th>
            </tr>
          </thead>
          <tbody id="tbody-guests" class="divide-y {{ 'divide-rose-200/60' if is_pink else 'divide-sky-200/60' }}">
            {% for g in guests %}
            <tr id="row-guests-{{ g[0] }}" class="hover:bg-white/40 transition">
              <td class="p-2"><input type="text" name="name" value="{{ g[2] }}" class="w-full p-1.5 rounded-lg text-xs font-semibold {{ input_style }}"></td>
              <td class="p-2"><input type="text" name="phone" value="{{ g[3] or '' }}" placeholder="0812345..." class="w-full p-1.5 rounded-lg text-xs font-mono {{ input_style }}"></td>
              <td class="p-2">
                <select name="side" class="w-full p-1.5 rounded-lg text-xs {{ input_style }}">
                  <option value="Pihak Pria" {{ 'selected' if g[4]=='Pihak Pria' }}>Pihak Pria</option>
                  <option value="Pihak Wanita" {{ 'selected' if g[4]=='Pihak Wanita' }}>Pihak Wanita</option>
                </select>
              </td>
              <td class="p-2">
                <select name="invite_status" class="w-full p-1.5 rounded-lg text-xs font-bold {{ input_style }}">
                  <option value="Belum Terkirim" {{ 'selected' if g[5]=='Belum Terkirim' }}>Belum Terkirim</option>
                  <option value="Terkirim" {{ 'selected' if g[5]=='Terkirim' }}>Terkirim</option>
                </select>
              </td>
              <td class="p-2"><input type="text" name="address" value="{{ g[6] or '' }}" placeholder="Alamat..." class="w-full p-1.5 rounded-lg text-xs {{ input_style }}"></td>
              <td class="p-2">
                <select name="rsvp" class="w-full p-1.5 rounded-lg text-xs font-bold {{ input_style }}">
                  <option value="Menunggu" {{ 'selected' if g[7]=='Menunggu' }}>Menunggu</option>
                  <option value="Hadir" {{ 'selected' if g[7]=='Hadir' }}>Hadir</option>
                  <option value="Tidak Hadir" {{ 'selected' if g[7]=='Tidak Hadir' }}>Tidak Hadir</option>
                </select>
              </td>
              <td class="p-2"><input type="text" name="notes" value="{{ g[8] or '' }}" placeholder="Catatan..." class="w-full p-1.5 rounded-lg text-xs {{ input_style }}"></td>
              <td class="p-2 text-center whitespace-nowrap">
                <button type="button" onclick="sendWhatsapp('{{ g[2] }}', this)" class="bg-emerald-500 hover:bg-emerald-600 text-white font-bold px-2 py-1.5 rounded-lg text-xs mr-1 shadow-sm transition" title="Kirim Undangan WA">
                  <i class="fa-brands fa-whatsapp text-sm"></i> Kirim
                </button>
                <button type="button" onclick="ajaxSaveRow('guests', {{ g[0] }}, this)" class="bg-purple-400 hover:bg-purple-500 text-white font-bold p-1.5 rounded-lg text-xs mr-1 shadow-sm"><i class="fa-solid fa-floppy-disk"></i></button>
                <button type="button" onclick="ajaxDeleteRow('guests', {{ g[0] }}, this)" class="text-rose-400 hover:text-rose-600 p-1.5"><i class="fa-solid fa-trash"></i></button>
              </td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
        <div class="p-3 {{ 'bg-rose-200/40' if is_pink else 'bg-sky-200/40' }} rounded-b-xl border-t {{ 'border-rose-200' if is_pink else 'border-sky-200' }}">
          <button type="button" onclick="ajaxAddRow('guests')" class="bg-purple-400 hover:bg-purple-500 text-white font-bold py-2 px-4 rounded-xl text-xs inline-flex items-center gap-1 transition">
            <i class="fa-solid fa-plus"></i> Tambah Baris Tamu
          </button>
        </div>
      </div>
    </div>

    <!-- 6. BUKU AMPLOP & KADO -->
    <div id="tab-amplop" class="tab-pane hidden space-y-3">
      <div class="{{ card_box }} p-4 rounded-2xl flex flex-wrap gap-3 justify-between items-center text-xs">
        <div>
          <h3 class="font-bold text-sm text-emerald-800"><i class="fa-solid fa-hand-holding-dollar mr-1"></i> Rekapitulasi Amplop & Kado Masuk</h3>
          <p class="text-[11px] opacity-75 mt-0.5">Total Uang Terkumpul: <b class="text-emerald-700 text-xs">Rp {{ "{:,.0f}".format(total_amplop_uang).replace(",", ".") }}</b> | Total Kado Fisik: <b>{{ total_kado_barang }} Barang</b></p>
        </div>
        <div class="flex items-center gap-2">
          <a href="/sync_guests_to_amplop" class="bg-emerald-600 hover:bg-emerald-700 text-white font-bold px-3 py-1.5 rounded-xl transition shadow-sm" title="Salin semua nama tamu yang hadir ke daftar amplop">
            <i class="fa-solid fa-arrows-rotate mr-1"></i> Tarik Tamu Hadir ke Amplop
          </a>
          <div class="relative">
            <input type="text" onkeyup="filterTable('tbody-amplop', this.value)" placeholder="Cari nama pemberi..." class="p-1.5 pl-7 rounded-xl text-xs bg-white/80 border border-emerald-200 focus:outline-none focus:ring-1 focus:ring-emerald-400">
            <i class="fa-solid fa-magnifying-glass absolute left-2.5 top-2.5 text-gray-400 text-[10px]"></i>
          </div>
        </div>
      </div>

      <div class="{{ card_box }} rounded-2xl overflow-x-auto p-2">
        <table class="w-full text-left text-xs whitespace-nowrap">
          <thead class="{{ thead_style }} rounded-xl border-b text-[11px]">
            <tr>
              <th class="p-2 min-w-[180px] rounded-l-lg">Nama Tamu / Pemberi</th>
              <th class="p-2 min-w-[120px]">Bentuk Pemberian</th>
              <th class="p-2 min-w-[130px]">Nominal Uang (Rp)</th>
              <th class="p-2 min-w-[180px]">Nama Kado / Hadiah Fisik</th>
              <th class="p-2 min-w-[180px]">Catatan / Doa</th>
              <th class="p-2 text-center rounded-r-lg">Aksi</th>
            </tr>
          </thead>
          <tbody id="tbody-amplop" class="divide-y {{ 'divide-rose-200/60' if is_pink else 'divide-sky-200/60' }}">
            {% for a in amplop_rows %}
            <tr id="row-amplop-{{ a[0] }}" class="hover:bg-white/40 transition">
              <td class="p-2"><input type="text" name="giver_name" value="{{ a[2] }}" class="w-full p-1.5 rounded-lg text-xs font-semibold {{ input_style }}"></td>
              <td class="p-2">
                <select name="gift_type" class="w-full p-1.5 rounded-lg text-xs font-bold {{ input_style }}">
                  <option value="Uang" {{ 'selected' if a[3]=='Uang' }}>Uang Amplop</option>
                  <option value="Kado" {{ 'selected' if a[3]=='Kado' }}>Kado Barang</option>
                </select>
              </td>
              <td class="p-2"><input type="number" name="amount" value="{{ a[4] or 0 }}" class="w-full p-1.5 rounded-lg text-xs font-bold text-emerald-700 {{ input_style }}"></td>
              <td class="p-2"><input type="text" name="gift_item" value="{{ a[5] or '' }}" placeholder="Set Cangkir / Emas..." class="w-full p-1.5 rounded-lg text-xs {{ input_style }}"></td>
              <td class="p-2"><input type="text" name="notes" value="{{ a[6] or '' }}" placeholder="Catatan / Meja..." class="w-full p-1.5 rounded-lg text-xs {{ input_style }}"></td>
              <td class="p-2 text-center whitespace-nowrap">
                <button type="button" onclick="ajaxSaveRow('amplop', {{ a[0] }}, this)" class="bg-emerald-500 hover:bg-emerald-600 text-white font-bold p-1.5 rounded-lg text-xs mr-1 shadow-sm"><i class="fa-solid fa-floppy-disk"></i></button>
                <button type="button" onclick="ajaxDeleteRow('amplop', {{ a[0] }}, this)" class="text-rose-400 hover:text-rose-600 p-1.5"><i class="fa-solid fa-trash"></i></button>
              </td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
        <div class="p-3 {{ 'bg-rose-200/40' if is_pink else 'bg-sky-200/40' }} rounded-b-xl border-t {{ 'border-rose-200' if is_pink else 'border-sky-200' }}">
          <button type="button" onclick="ajaxAddRow('amplop')" class="bg-emerald-500 hover:bg-emerald-600 text-white font-bold py-2 px-4 rounded-xl text-xs inline-flex items-center gap-1 transition">
            <i class="fa-solid fa-plus"></i> Catat Amplop / Kado Baru
          </button>
        </div>
      </div>
    </div>

    <!-- 7. KONTAK DARURAT PANITIA INTI (FITUR BARU!) -->
    <div id="tab-panitia" class="tab-pane hidden space-y-3">
      <div class="no-print {{ card_box }} p-3.5 rounded-2xl flex flex-wrap gap-2 justify-between items-center text-xs">
        <div>
          <span class="font-bold text-rose-900 text-sm"><i class="fa-solid fa-phone-volume mr-1"></i> Direktori Kontak Darurat Panitia Inti Hari-H</span>
          <p class="text-[11px] opacity-75 mt-0.5">Pegangan wajib bagi keluarga & WO untuk koordinasi cepat saat acara berlangsung</p>
        </div>
        <button onclick="window.print()" class="bg-rose-500 hover:bg-rose-600 text-white px-3 py-1.5 rounded-xl font-bold transition flex items-center gap-1 shadow-sm">
          <i class="fa-solid fa-print"></i> Cetak Lembar Kontak
        </button>
      </div>

      <div id="printable-panitia" class="{{ card_box }} rounded-2xl overflow-x-auto p-4 bg-white">
        <div class="hidden print:block text-center mb-4">
          <h2 class="text-xl font-bold font-serif">{{ s[1] }} & {{ s[2] }}</h2>
          <p class="text-xs text-gray-500">Lembar Kontak Cepat & Darurat Panitia Pernikahan ({{ s[3] }})</p>
          <hr class="my-2">
        </div>
        <table class="w-full text-left text-xs whitespace-nowrap">
          <thead class="{{ thead_style }} rounded-xl border-b text-[11px]">
            <tr>
              <th class="p-2 min-w-[200px] rounded-l-lg">Tugas / Peran Lapangan</th>
              <th class="p-2 min-w-[180px]">Nama Penanggung Jawab</th>
              <th class="p-2 min-w-[140px]">Nomor HP / WhatsApp</th>
              <th class="p-2 min-w-[200px]">Tugas Khusus / Catatan</th>
              <th class="p-2 text-center rounded-r-lg no-print">Aksi & Hubungi</th>
            </tr>
          </thead>
          <tbody id="tbody-panitia_contacts" class="divide-y {{ 'divide-rose-200/60' if is_pink else 'divide-sky-200/60' }}">
            {% for p in panitia_contacts %}
            <tr id="row-panitia_contacts-{{ p[0] }}" class="hover:bg-white/40 transition">
              <td class="p-2"><input type="text" name="role_name" value="{{ p[2] }}" class="w-full p-1.5 rounded-lg text-xs font-bold text-rose-900 {{ input_style }}"></td>
              <td class="p-2"><input type="text" name="person_name" value="{{ p[3] }}" class="w-full p-1.5 rounded-lg text-xs font-semibold {{ input_style }}"></td>
              <td class="p-2"><input type="text" name="phone" value="{{ p[4] or '' }}" placeholder="08..." class="w-full p-1.5 rounded-lg text-xs font-mono {{ input_style }}"></td>
              <td class="p-2"><input type="text" name="notes" value="{{ p[5] or '' }}" placeholder="Catatan tugas..." class="w-full p-1.5 rounded-lg text-xs {{ input_style }}"></td>
              <td class="p-2 text-center whitespace-nowrap no-print">
                {% if p[4] %}
                <a href="https://api.whatsapp.com/send?phone={{ p[4] | replace(' ', '') | replace('-', '') }}" target="_blank" class="bg-emerald-500 hover:bg-emerald-600 text-white font-bold px-2 py-1.5 rounded-lg text-xs mr-1 shadow-sm inline-flex items-center gap-1" title="Hubungi WA">
                  <i class="fa-brands fa-whatsapp"></i> Chat
                </a>
                {% endif %}
                <button type="button" onclick="ajaxSaveRow('panitia_contacts', {{ p[0] }}, this)" class="bg-indigo-400 hover:bg-indigo-500 text-white font-bold p-1.5 rounded-lg text-xs mr-1 shadow-sm"><i class="fa-solid fa-floppy-disk"></i></button>
                <button type="button" onclick="ajaxDeleteRow('panitia_contacts', {{ p[0] }}, this)" class="text-rose-400 hover:text-rose-600 p-1.5"><i class="fa-solid fa-trash"></i></button>
              </td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
        <div class="no-print p-3 {{ 'bg-rose-200/40' if is_pink else 'bg-sky-200/40' }} rounded-b-xl border-t {{ 'border-rose-200' if is_pink else 'border-sky-200' }}">
          <button type="button" onclick="ajaxAddRow('panitia_contacts')" class="bg-rose-500 hover:bg-rose-600 text-white font-bold py-2 px-4 rounded-xl text-xs inline-flex items-center gap-1 transition">
            <i class="fa-solid fa-plus"></i> Tambah Kontak Panitia Baru
          </button>
        </div>
      </div>
    </div>

    <!-- 8. BERKAS KUA, SAKSI & MAHAR -->
    <div id="tab-kua" class="tab-pane hidden space-y-4">
      <div class="{{ card_box }} p-4 rounded-2xl">
        <h3 class="text-xs font-bold border-b {{ 'border-rose-200' if is_pink else 'border-sky-200' }} pb-2 mb-3 text-indigo-900"><i class="fa-solid fa-signature mr-1"></i> Data Saksi, Wali & Teks Mahar Akad Nikah</h3>
        <form action="/update_kua_details" method="POST" class="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          <div>
            <label class="font-bold opacity-80">Nama Wali Nikah</label>
            <input type="text" name="wali_nikah" value="{{ s[6] or '' }}" placeholder="Ayah Kandung / Saudara..." class="w-full p-2 rounded-xl mt-1 {{ input_style }}">
          </div>
          <div>
            <label class="font-bold opacity-80">Rincian Mahar / Maskawin</label>
            <input type="text" name="mahar_desc" value="{{ s[9] or '' }}" placeholder="Emas 10 Gram & Seperangkat Alat Sholat..." class="w-full p-2 rounded-xl mt-1 {{ input_style }}">
          </div>
          <div>
            <label class="font-bold opacity-80">Saksi Nikah 1 (Pihak Pria)</label>
            <input type="text" name="saksi1" value="{{ s[7] or '' }}" placeholder="Paman / Tokoh..." class="w-full p-2 rounded-xl mt-1 {{ input_style }}">
          </div>
          <div>
            <label class="font-bold opacity-80">Saksi Nikah 2 (Pihak Wanita)</label>
            <input type="text" name="saksi2" value="{{ s[8] or '' }}" placeholder="Paman / Tokoh..." class="w-full p-2 rounded-xl mt-1 {{ input_style }}">
          </div>
          <div class="md:col-span-2 text-right">
            <button type="submit" class="{{ btn_primary }} px-4 py-2 rounded-xl text-xs">Simpan Data Akad</button>
          </div>
        </form>
      </div>

      <div class="{{ card_box }} rounded-2xl overflow-x-auto p-2">
        <div class="p-2 border-b {{ 'border-rose-200' if is_pink else 'border-sky-200' }} flex justify-between items-center text-xs font-bold text-indigo-900">
          <span><i class="fa-solid fa-list-check mr-1"></i> Checklist Kelengkapan Dokumen KUA / Catatan Sipil</span>
          <span>{{ kua_done }}/{{ kua_total }} Dokumen Siap</span>
        </div>
        <table class="w-full text-left text-xs whitespace-nowrap">
          <thead class="{{ thead_style }} rounded-xl border-b text-[11px]">
            <tr>
              <th class="p-2 text-center rounded-l-lg">Selesai?</th>
              <th class="p-2 min-w-[240px]">Nama Berkas / Syarat KUA</th>
              <th class="p-2 min-w-[140px]">Penanggung Jawab (PIC)</th>
              <th class="p-2 min-w-[200px]">Catatan / Lokasi Pengurusan</th>
              <th class="p-2 text-center rounded-r-lg">Aksi</th>
            </tr>
          </thead>
          <tbody id="tbody-kua_docs" class="divide-y {{ 'divide-rose-200/60' if is_pink else 'divide-sky-200/60' }}">
            {% for k in kua_docs %}
            <tr id="row-kua_docs-{{ k[0] }}" class="hover:bg-white/40 transition {{ 'bg-emerald-100/40' if k[4] else '' }}">
              <td class="p-2 text-center">
                <button type="button" onclick="ajaxToggle('kua_docs', {{ k[0] }}, this)" class="text-base {{ 'text-emerald-500' if k[4] else 'text-gray-300 hover:text-emerald-500' }}"><i class="fa-solid fa-circle-check"></i></button>
              </td>
              <td class="p-2"><input type="text" name="doc_name" value="{{ k[2] }}" class="w-full p-1.5 rounded-lg text-xs font-semibold {{ input_style }} {{ 'line-through opacity-60' if k[4] }}"></td>
              <td class="p-2"><input type="text" name="pic" value="{{ k[3] or '' }}" placeholder="PIC..." class="w-full p-1.5 rounded-lg text-xs {{ input_style }}"></td>
              <td class="p-2"><input type="text" name="notes" value="{{ k[4] or '' }}" placeholder="Catatan..." class="w-full p-1.5 rounded-lg text-xs {{ input_style }}"></td>
              <td class="p-2 text-center whitespace-nowrap">
                <button type="button" onclick="ajaxSaveRow('kua_docs', {{ k[0] }}, this)" class="bg-indigo-400 hover:bg-indigo-500 text-white font-bold p-1.5 rounded-lg text-xs mr-1 shadow-sm"><i class="fa-solid fa-floppy-disk"></i></button>
                <button type="button" onclick="ajaxDeleteRow('kua_docs', {{ k[0] }}, this)" class="text-rose-400 hover:text-rose-600 p-1.5"><i class="fa-solid fa-trash"></i></button>
              </td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
        <div class="p-3 {{ 'bg-rose-200/40' if is_pink else 'bg-sky-200/40' }} rounded-b-xl border-t {{ 'border-rose-200' if is_pink else 'border-sky-200' }}">
          <button type="button" onclick="ajaxAddRow('kua_docs')" class="bg-indigo-500 hover:bg-indigo-600 text-white font-bold py-2 px-4 rounded-xl text-xs inline-flex items-center gap-1 transition">
            <i class="fa-solid fa-plus"></i> Tambah Syarat Dokumen Baru
          </button>
        </div>
      </div>
    </div>

    <!-- 9. RUNDOWN & PLAYLIST MUSIK -->
    <div id="tab-rundown" class="tab-pane hidden space-y-4">
      <div class="no-print {{ card_box }} p-3 rounded-2xl flex justify-between items-center text-xs">
        <span class="font-bold text-amber-800"><i class="fa-solid fa-calendar-check mr-1"></i> Progres Rundown: {{ time_done }}/{{ time_total }} Siap ({{ time_pct }}%)</span>
        <button onclick="window.print()" class="bg-amber-500 hover:bg-amber-600 text-white px-3 py-1.5 rounded-xl font-bold transition flex items-center gap-1 shadow-sm">
          <i class="fa-solid fa-print"></i> Cetak Rundown Hari-H
        </button>
      </div>

      <div id="printable-area" class="{{ card_box }} rounded-2xl overflow-x-auto p-4 bg-white">
        <div class="hidden print:block text-center mb-4">
          <h2 class="text-xl font-bold font-serif">{{ s[1] }} & {{ s[2] }}</h2>
          <p class="text-xs text-gray-500">Rundown & Susunan Acara Pernikahan ({{ s[3] }})</p>
          <hr class="my-2">
        </div>
        <table class="w-full text-left text-xs whitespace-nowrap">
          <thead class="{{ thead_style }} rounded-xl border-b text-[11px]">
            <tr>
              <th class="p-2 text-center rounded-l-lg no-print">Terlaksana?</th>
              <th class="p-2 min-w-[120px]">Waktu (Jam)</th>
              <th class="p-2 min-w-[200px]">Agenda / Aktivitas Hari-H</th>
              <th class="p-2 min-w-[140px]">Penanggung Jawab (PIC)</th>
              <th class="p-2 min-w-[180px]">Catatan / Lokasi</th>
              <th class="p-2 text-center rounded-r-lg no-print">Aksi</th>
            </tr>
          </thead>
          <tbody id="tbody-timeline" class="divide-y {{ 'divide-rose-200/60' if is_pink else 'divide-sky-200/60' }}">
            {% for r in timeline %}
            <tr id="row-timeline-{{ r[0] }}" class="hover:bg-white/40 transition {{ 'bg-emerald-100/40' if r[6] else '' }}">
              <td class="p-2 text-center no-print">
                <button type="button" onclick="ajaxToggle('timeline', {{ r[0] }}, this)" class="text-base {{ 'text-emerald-500' if r[6] else 'text-gray-300 hover:text-emerald-500' }}"><i class="fa-solid fa-circle-check"></i></button>
              </td>
              <td class="p-2"><input type="text" name="time" value="{{ r[2] }}" placeholder="08:00 - 09:00" class="w-full p-1.5 rounded-lg text-xs font-bold text-amber-800 {{ input_style }}"></td>
              <td class="p-2"><input type="text" name="activity" value="{{ r[3] }}" class="w-full p-1.5 rounded-lg text-xs font-semibold {{ input_style }} {{ 'line-through opacity-60' if r[6] }}"></td>
              <td class="p-2"><input type="text" name="pic" value="{{ r[4] or '' }}" placeholder="Keluarga / WO" class="w-full p-1.5 rounded-lg text-xs {{ input_style }}"></td>
              <td class="p-2"><input type="text" name="notes" value="{{ r[5] or '' }}" placeholder="Panggung utama..." class="w-full p-1.5 rounded-lg text-xs {{ input_style }}"></td>
              <td class="p-2 text-center whitespace-nowrap no-print">
                <button type="button" onclick="ajaxSaveRow('timeline', {{ r[0] }}, this)" class="bg-amber-400 hover:bg-amber-500 text-white font-bold p-1.5 rounded-lg text-xs mr-1 shadow-sm"><i class="fa-solid fa-floppy-disk"></i></button>
                <button type="button" onclick="ajaxDeleteRow('timeline', {{ r[0] }}, this)" class="text-rose-400 hover:text-rose-600 p-1.5"><i class="fa-solid fa-trash"></i></button>
              </td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
        <div class="no-print p-3 {{ 'bg-rose-200/40' if is_pink else 'bg-sky-200/40' }} rounded-b-xl border-t {{ 'border-rose-200' if is_pink else 'border-sky-200' }}">
          <button type="button" onclick="ajaxAddRow('timeline')" class="bg-amber-400 hover:bg-amber-500 text-white font-bold py-2 px-4 rounded-xl text-xs inline-flex items-center gap-1 transition">
            <i class="fa-solid fa-plus"></i> Tambah Baris Rundown
          </button>
        </div>
      </div>

      <div class="no-print {{ card_box }} rounded-2xl overflow-x-auto p-2">
        <div class="p-2 border-b {{ 'border-rose-200' if is_pink else 'border-sky-200' }} text-xs font-bold text-amber-900">
          <i class="fa-solid fa-music mr-1"></i> Panduan Playlist Lagu Hari-H (Untuk Operator / Band / MC)
        </div>
        <table class="w-full text-left text-xs whitespace-nowrap">
          <thead class="{{ thead_style }} rounded-xl border-b text-[11px]">
            <tr>
              <th class="p-2 text-center rounded-l-lg">Ready?</th>
              <th class="p-2 min-w-[180px]">Momen Acara</th>
              <th class="p-2 min-w-[220px]">Judul Lagu & Penyanyi</th>
              <th class="p-2 min-w-[180px]">Catatan Operator</th>
              <th class="p-2 text-center rounded-r-lg">Aksi</th>
            </tr>
          </thead>
          <tbody id="tbody-music_playlist" class="divide-y {{ 'divide-rose-200/60' if is_pink else 'divide-sky-200/60' }}">
            {% for m in music_playlist %}
            <tr id="row-music_playlist-{{ m[0] }}" class="hover:bg-white/40 transition {{ 'bg-emerald-100/40' if m[4] else '' }}">
              <td class="p-2 text-center">
                <button type="button" onclick="ajaxToggle('music_playlist', {{ m[0] }}, this)" class="text-base {{ 'text-emerald-500' if m[4] else 'text-gray-300 hover:text-emerald-500' }}"><i class="fa-solid fa-circle-check"></i></button>
              </td>
              <td class="p-2"><input type="text" name="moment" value="{{ m[2] }}" class="w-full p-1.5 rounded-lg text-xs font-semibold {{ input_style }}"></td>
              <td class="p-2"><input type="text" name="song_title" value="{{ m[3] }}" class="w-full p-1.5 rounded-lg text-xs font-bold text-amber-800 {{ input_style }}"></td>
              <td class="p-2"><input type="text" name="notes" value="{{ m[4] or '' }}" placeholder="Catatan tempo/fade..." class="w-full p-1.5 rounded-lg text-xs {{ input_style }}"></td>
              <td class="p-2 text-center whitespace-nowrap">
                <button type="button" onclick="ajaxSaveRow('music_playlist', {{ m[0] }}, this)" class="bg-amber-400 hover:bg-amber-500 text-white font-bold p-1.5 rounded-lg text-xs mr-1 shadow-sm"><i class="fa-solid fa-floppy-disk"></i></button>
                <button type="button" onclick="ajaxDeleteRow('music_playlist', {{ m[0] }}, this)" class="text-rose-400 hover:text-rose-600 p-1.5"><i class="fa-solid fa-trash"></i></button>
              </td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
        <div class="p-3 {{ 'bg-rose-200/40' if is_pink else 'bg-sky-200/40' }} rounded-b-xl border-t {{ 'border-rose-200' if is_pink else 'border-sky-200' }}">
          <button type="button" onclick="ajaxAddRow('music_playlist')" class="bg-amber-400 hover:bg-amber-500 text-white font-bold py-2 px-4 rounded-xl text-xs inline-flex items-center gap-1 transition">
            <i class="fa-solid fa-plus"></i> Tambah Lagu Baru
          </button>
        </div>
      </div>
    </div>

    <!-- 10. SERAGAM KELUARGA -->
    <div id="tab-seragam" class="tab-pane hidden space-y-3">
      <div class="{{ card_box }} p-3 rounded-2xl flex justify-between items-center text-xs">
        <span class="font-bold text-indigo-900"><i class="fa-solid fa-vest mr-1"></i> Rekapitulasi Bahan & Seragam Keluarga / Panitia</span>
      </div>
      <div class="{{ card_box }} rounded-2xl overflow-x-auto p-2">
        <table class="w-full text-left text-xs whitespace-nowrap">
          <thead class="{{ thead_style }} rounded-xl border-b text-[11px]">
            <tr>
              <th class="p-2 min-w-[180px] rounded-l-lg">Nama Penerima Seragam</th>
              <th class="p-2 min-w-[140px]">Peran / Pihak</th>
              <th class="p-2 min-w-[120px]">Ukuran / Meter Kain</th>
              <th class="p-2 min-w-[130px]">Status Jahit</th>
              <th class="p-2 min-w-[180px]">Catatan / Model</th>
              <th class="p-2 text-center rounded-r-lg">Aksi</th>
            </tr>
          </thead>
          <tbody id="tbody-seragam" class="divide-y {{ 'divide-rose-200/60' if is_pink else 'divide-sky-200/60' }}">
            {% for srg in seragam %}
            <tr id="row-seragam-{{ srg[0] }}" class="hover:bg-white/40 transition">
              <td class="p-2"><input type="text" name="receiver_name" value="{{ srg[2] }}" class="w-full p-1.5 rounded-lg text-xs font-semibold {{ input_style }}"></td>
              <td class="p-2">
                <select name="side" class="w-full p-1.5 rounded-lg text-xs {{ input_style }}">
                  <option value="Keluarga Pria" {{ 'selected' if srg[3]=='Keluarga Pria' }}>Keluarga Pria</option>
                  <option value="Keluarga Wanita" {{ 'selected' if srg[3]=='Keluarga Wanita' }}>Keluarga Wanita</option>
                  <option value="Bridesmaid" {{ 'selected' if srg[3]=='Bridesmaid' }}>Bridesmaid</option>
                  <option value="Bestman / Groomsmen" {{ 'selected' if srg[3]=='Bestman / Groomsmen' }}>Bestman / Groomsmen</option>
                  <option value="Panitia Keluarga" {{ 'selected' if srg[3]=='Panitia Keluarga' }}>Panitia Keluarga</option>
                </select>
              </td>
              <td class="p-2"><input type="text" name="fabric_meter" value="{{ srg[4] or '' }}" placeholder="2.5 Meter / L" class="w-full p-1.5 rounded-lg text-xs {{ input_style }}"></td>
              <td class="p-2">
                <select name="status" class="w-full p-1.5 rounded-lg text-xs font-bold {{ input_style }}">
                  <option value="Belum Diberi" {{ 'selected' if srg[5]=='Belum Diberi' }}>Belum Diberi</option>
                  <option value="Sudah Diberi Kain" {{ 'selected' if srg[5]=='Sudah Diberi Kain' }}>Sudah Diberi Kain</option>
                  <option value="Sedang Dijahit" {{ 'selected' if srg[5]=='Sedang Dijahit' }}>Sedang Dijahit</option>
                  <option value="Selesai Siap Pakai" {{ 'selected' if srg[5]=='Selesai Siap Pakai' }}>Selesai Siap Pakai</option>
                </select>
              </td>
              <td class="p-2"><input type="text" name="notes" value="{{ srg[6] or '' }}" placeholder="Model kutubaru/kebaya..." class="w-full p-1.5 rounded-lg text-xs {{ input_style }}"></td>
              <td class="p-2 text-center whitespace-nowrap">
                <button type="button" onclick="ajaxSaveRow('seragam', {{ srg[0] }}, this)" class="bg-indigo-400 hover:bg-indigo-500 text-white font-bold p-1.5 rounded-lg text-xs mr-1 shadow-sm"><i class="fa-solid fa-floppy-disk"></i></button>
                <button type="button" onclick="ajaxDeleteRow('seragam', {{ srg[0] }}, this)" class="text-rose-400 hover:text-rose-600 p-1.5"><i class="fa-solid fa-trash"></i></button>
              </td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
        <div class="p-3 {{ 'bg-rose-200/40' if is_pink else 'bg-sky-200/40' }} rounded-b-xl border-t {{ 'border-rose-200' if is_pink else 'border-sky-200' }}">
          <button type="button" onclick="ajaxAddRow('seragam')" class="bg-indigo-500 hover:bg-indigo-600 text-white font-bold py-2 px-4 rounded-xl text-xs inline-flex items-center gap-1 transition">
            <i class="fa-solid fa-plus"></i> Tambah Penerima Seragam
          </button>
        </div>
      </div>
    </div>

    <!-- 11. DARURAT -->
    <div id="tab-darurat" class="tab-pane hidden space-y-3">
      <div class="{{ card_box }} p-3 rounded-2xl flex justify-between items-center text-xs">
        <span class="font-bold text-rose-800"><i class="fa-solid fa-kit-medical mr-1"></i> Barang Darurat Siap: {{ chk_done }}/{{ chk_total }} ({{ chk_pct }}%)</span>
      </div>
      <div class="{{ card_box }} rounded-2xl overflow-x-auto p-2">
        <table class="w-full text-left text-xs whitespace-nowrap">
          <thead class="{{ thead_style }} rounded-xl border-b text-[11px]">
            <tr>
              <th class="p-2 text-center rounded-l-lg">Siap?</th>
              <th class="p-2 min-w-[200px]">Nama Barang</th>
              <th class="p-2 min-w-[140px]">PIC Bawa</th>
              <th class="p-2 text-center rounded-r-lg">Aksi</th>
            </tr>
          </thead>
          <tbody id="tbody-checklist" class="divide-y {{ 'divide-rose-200/60' if is_pink else 'divide-sky-200/60' }}">
            {% for c in checklist %}
            <tr id="row-checklist-{{ c[0] }}" class="hover:bg-white/40 transition {{ 'bg-emerald-100/40' if c[8] else '' }}">
              <td class="p-2 text-center">
                <button type="button" onclick="ajaxToggle('checklist', {{ c[0] }}, this)" class="text-base {{ 'text-emerald-500' if c[8] else 'text-gray-300 hover:text-emerald-500' }}"><i class="fa-solid fa-circle-check"></i></button>
              </td>
              <td class="p-2"><input type="text" name="item" value="{{ c[2] }}" class="w-full p-1.5 rounded-lg text-xs font-semibold {{ input_style }} {{ 'line-through opacity-60' if c[8] }}"></td>
              <td class="p-2"><input type="text" name="pic" value="{{ c[7] or '' }}" placeholder="Ibu/Bridesmaid..." class="w-full p-1.5 rounded-lg text-xs {{ input_style }}"></td>
              <td class="p-2 text-center whitespace-nowrap">
                <button type="button" onclick="ajaxSaveRow('checklist', {{ c[0] }}, this)" class="bg-rose-400 hover:bg-rose-500 text-white font-bold p-1.5 rounded-lg text-xs mr-1 shadow-sm"><i class="fa-solid fa-floppy-disk"></i></button>
                <button type="button" onclick="ajaxDeleteRow('checklist', {{ c[0] }}, this)" class="text-rose-400 hover:text-rose-600 p-1.5"><i class="fa-solid fa-trash"></i></button>
              </td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
        <div class="p-3 {{ 'bg-rose-200/40' if is_pink else 'bg-sky-200/40' }} rounded-b-xl border-t {{ 'border-rose-200' if is_pink else 'border-sky-200' }}">
          <button type="button" onclick="ajaxAddRow('checklist')" class="bg-rose-400 hover:bg-rose-500 text-white font-bold py-2 px-4 rounded-xl text-xs inline-flex items-center gap-1 transition">
            <i class="fa-solid fa-plus"></i> Tambah Baris Barang Darurat
          </button>
        </div>
      </div>
    </div>

    <!-- 12. PENGATURAN -->
    <div id="tab-pengaturan" class="no-print tab-pane hidden">
      <div class="{{ card_box }} p-6 rounded-2xl space-y-4">
        <h2 class="text-sm font-bold border-b {{ 'border-rose-200' if is_pink else 'border-sky-200' }} pb-2">Pengaturan Acara, Tema & Cadangan Data</h2>
        
        <form action="/update_settings" method="POST" class="space-y-3 text-xs">
          <div>
            <label class="font-bold opacity-80">Nama Pengantin Pria & Wanita</label>
            <div class="grid grid-cols-2 gap-2 mt-1">
              <input type="text" name="groom" id="setting_groom" value="{{ s[1] }}" required class="p-2.5 rounded-xl {{ input_style }}">
              <input type="text" name="bride" id="setting_bride" value="{{ s[2] }}" required class="p-2.5 rounded-xl {{ input_style }}">
            </div>
          </div>
          <div>
            <label class="font-bold opacity-80">Tanggal Pernikahan</label>
            <input type="date" name="wedding_date" id="setting_date" value="{{ s[3] }}" required class="w-full p-2.5 rounded-xl mt-1 {{ input_style }}">
          </div>
          <div>
            <label class="font-bold opacity-80">Target Budget Acara (Rp)</label>
            <input type="number" name="budget" value="{{ s[4] }}" required class="w-full p-2.5 rounded-xl mt-1 {{ input_style }}">
          </div>
          <div>
            <label class="font-bold opacity-80">Pilihan Warna Tema Pastel</label>
            <select name="theme" class="w-full p-2.5 rounded-xl mt-1 font-bold {{ input_style }}">
              <option value="pink" {{ 'selected' if s[5]=='pink' }}>🌸 Soft Pastel Rose Romantic</option>
              <option value="blue" {{ 'selected' if s[5]=='blue' }}>🌊 Soft Pastel Sky Blue Elegant</option>
            </select>
          </div>
          <button type="submit" class="w-full py-3 {{ btn_primary }} rounded-xl text-xs mt-2 transition">Simpan Perubahan Tema</button>
        </form>

        <div class="pt-4 border-t {{ 'border-rose-200' if is_pink else 'border-sky-200' }}">
          <h3 class="text-xs font-bold text-gray-700 mb-1"><i class="fa-solid fa-shield-halved mr-1"></i> Keamanan Data (Backup 1-Klik)</h3>
          <p class="text-[11px] opacity-75 mb-3">Unduh seluruh file database ke laptop Anda agar data aman dari kehilangan.</p>
          <a href="/backup_database" class="bg-gray-800 hover:bg-black text-white px-4 py-2.5 rounded-xl font-bold text-xs inline-flex items-center gap-2 shadow-sm transition">
            <i class="fa-solid fa-download"></i> Unduh File Cadangan Database (.db)
          </a>
        </div>
      </div>
    </div>

  </div>

  {% raw %}
  <script>
    const isPinkTheme = document.body.classList.contains('bg-rose-50/80');
    const activeTabClass = isPinkTheme ? ['bg-rose-400', 'text-white', 'shadow-sm', 'font-bold'] : ['bg-sky-500', 'text-white', 'shadow-sm', 'font-bold'];
    const inactiveTabClass = isPinkTheme ? ['bg-rose-200/60', 'text-rose-800'] : ['bg-sky-200/60', 'text-sky-800'];

    function tab(name) {
      document.querySelectorAll('.tab-pane').forEach(el => el.classList.add('hidden'));
      document.querySelectorAll('.tab-btn').forEach(el => {
        el.classList.remove(...activeTabClass);
        el.classList.add(...inactiveTabClass);
      });
      document.getElementById('tab-' + name).classList.remove('hidden');
      const curBtn = document.getElementById('btn-' + name);
      if(curBtn) {
        curBtn.classList.remove(...inactiveTabClass);
        curBtn.classList.add(...activeTabClass);
      }
      localStorage.setItem('active_wedding_tab', name);
    }

    window.onload = function() {
      const savedTab = localStorage.getItem('active_wedding_tab') || 'dashboard';
      tab(savedTab);
      calcCatering();
    };

    function showToast(msg = "Tersimpan!") {
      const toast = document.getElementById('toast');
      document.getElementById('toast-msg').innerText = msg;
      toast.classList.remove('translate-y-20', 'opacity-0');
      setTimeout(() => {
        toast.classList.add('translate-y-20', 'opacity-0');
      }, 1500);
    }

    function filterTable(tbodyId, query) {
      const rows = document.querySelectorAll('#' + tbodyId + ' tr');
      const q = query.toLowerCase();
      rows.forEach(tr => {
        const text = tr.innerText.toLowerCase() + Array.from(tr.querySelectorAll('input, select')).map(i => i.value.toLowerCase()).join(' ');
        tr.style.display = text.includes(q) ? '' : 'none';
      });
    }

    function calcCatering() {
      const invites = parseInt(document.getElementById('catering_invites').value || 0);
      const totalPax = invites * 2;
      const buffet = Math.round(totalPax * 0.6);
      const stall = Math.round(totalPax * 0.4 * 4);
      const water = Math.round(totalPax * 1.2);

      document.getElementById('c_total_pax').innerText = totalPax.toLocaleString('id-ID') + ' Orang';
      document.getElementById('c_buffet').innerText = buffet.toLocaleString('id-ID') + ' Porsi';
      document.getElementById('c_stall').innerText = stall.toLocaleString('id-ID') + ' Porsi';
      document.getElementById('c_water').innerText = water.toLocaleString('id-ID') + ' Cup / Botol';
    }

    function sendWhatsapp(guestName, btn) {
      const tr = btn.closest('tr');
      const phoneInput = tr.querySelector('[name="phone"]');
      let phone = phoneInput ? phoneInput.value.trim().replace(/[^0-9]/g, '') : '';
      if(!phone) {
        alert("Harap isi nomor WhatsApp terlebih dahulu!");
        phoneInput.focus();
        return;
      }
      if(phone.startsWith('0')) {
        phone = '62' + phone.substring(1);
      }

      const groom = document.getElementById('setting_groom') ? document.getElementById('setting_groom').value : 'Pengantin';
      const bride = document.getElementById('setting_bride') ? document.getElementById('setting_bride').value : 'Pengantin';
      const date = document.getElementById('setting_date') ? document.getElementById('setting_date').value : '';

      const msg = `Halo *${guestName}*,%0A%0AKami bermaksud mengundang Anda untuk hadir dan memberikan doa restu di acara pernikahan kami:%0A%0A💍 *${groom} & ${bride}*%0A📅 Tanggal: ${date}%0A%0ASuatu kehormatan dan kebahagiaan bagi kami apabila Anda berkenan hadir di hari istimewa kami.%0A%0ATerima kasih banyak!`;
      
      const url = `https://api.whatsapp.com/send?phone=${phone}&text=${msg}`;
      window.open(url, '_blank');
    }

    function calcSisa(input) {
      const tr = input.closest('tr');
      const act = parseFloat(tr.querySelector('[name="actual_cost"]')?.value || 0);
      const paid = parseFloat(tr.querySelector('[name="paid"]')?.value || 0);
      const sisa = act - paid;
      const sisaEl = tr.querySelector('.sisa-val');
      if (sisaEl) {
        sisaEl.innerText = 'Rp ' + sisa.toLocaleString('id-ID');
      }
    }

    function ajaxSaveRow(tbl, id, btn) {
      const tr = document.getElementById('row-' + tbl + '-' + id);
      const inputs = tr.querySelectorAll('input, select');
      const data = new URLSearchParams();
      inputs.forEach(inp => data.append(inp.name, inp.value));

      btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';

      fetch('/api/update_row/' + tbl + '/' + id, {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: data.toString()
      })
      .then(res => res.json())
      .then(res => {
        btn.innerHTML = '<i class="fa-solid fa-floppy-disk"></i>';
        showToast("Tersimpan!");
      })
      .catch(() => {
        btn.innerHTML = '<i class="fa-solid fa-floppy-disk"></i>';
        showToast("Gagal menyimpan!");
      });
    }

    function ajaxAddRow(tbl) {
      fetch('/api/add_empty_row/' + tbl)
      .then(res => res.json())
      .then(data => {
        const id = data.id;
        const tbody = document.getElementById('tbody-' + tbl);
        const inpCls = isPinkTheme ? "bg-rose-50/90 border border-rose-200 text-rose-950 focus:bg-white focus:outline-none p-1.5 rounded-lg text-xs" : "bg-sky-50/90 border border-sky-200 text-slate-900 focus:bg-white focus:outline-none p-1.5 rounded-lg text-xs";
        const btnCls = isPinkTheme ? "bg-rose-400 hover:bg-rose-500 text-white font-bold p-1.5 rounded-lg text-xs mr-1 shadow-sm" : "bg-sky-500 hover:bg-sky-600 text-white font-bold p-1.5 rounded-lg text-xs mr-1 shadow-sm";
        let rowHtml = '';

        if(tbl === 'vendors') {
          rowHtml = `
            <tr id="row-vendors-${id}" class="hover:bg-white/40 transition">
              <td class="p-2 text-center"><button type="button" onclick="ajaxToggle('vendors', ${id}, this)" class="text-base text-gray-300 hover:text-emerald-500"><i class="fa-solid fa-circle-check"></i></button></td>
              <td class="p-2"><select name="category" class="w-full ${inpCls}"><option>Venue & Catering</option><option>Dekorasi & Tenda</option><option>Busana & Make Up</option><option>Dokumentasi</option><option>Undangan & Souvenir</option><option>Acara & MC</option><option>Lain-lain</option></select></td>
              <td class="p-2"><input type="text" name="name" value="Pos / Vendor Baru" class="w-full font-semibold ${inpCls}"></td>
              <td class="p-2"><input type="text" name="bank_info" placeholder="No Rek / Bank..." class="w-full font-mono ${inpCls}"></td>
              <td class="p-2"><input type="number" name="budget_cost" value="0" class="w-full ${inpCls}"></td>
              <td class="p-2"><input type="number" name="actual_cost" value="0" oninput="calcSisa(this)" class="w-full font-bold ${inpCls}"></td>
              <td class="p-2"><select name="pay_status" class="w-full font-bold ${inpCls}"><option value="DP">DP</option><option value="Lunas">Lunas</option></select></td>
              <td class="p-2"><input type="number" name="paid" value="0" oninput="calcSisa(this)" class="w-full ${inpCls}"></td>
              <td class="p-2 font-bold text-amber-700 sisa-val">Rp 0</td>
              <td class="p-2"><input type="text" name="contact" placeholder="WA..." class="w-full ${inpCls}"></td>
              <td class="p-2"><input type="date" name="due_date" class="${inpCls}"></td>
              <td class="p-2"><input type="text" name="notes" placeholder="Catatan..." class="w-full ${inpCls}"></td>
              <td class="p-2 text-center whitespace-nowrap">
                <button type="button" onclick="ajaxSaveRow('vendors', ${id}, this)" class="bg-indigo-400 hover:bg-indigo-500 text-white font-bold p-1.5 rounded-lg text-xs mr-1 shadow-sm"><i class="fa-solid fa-floppy-disk"></i></button>
                <button type="button" onclick="ajaxDeleteRow('vendors', ${id}, this)" class="text-rose-400 hover:text-rose-600 p-1.5"><i class="fa-solid fa-trash"></i></button>
              </td>
            </tr>`;
        } else if(tbl === 'roadmap') {
          rowHtml = `
            <tr id="row-roadmap-${id}" class="hover:bg-white/40 transition">
              <td class="p-2 text-center"><button type="button" onclick="ajaxToggle('roadmap', ${id}, this)" class="text-base text-gray-300 hover:text-emerald-500"><i class="fa-solid fa-circle-check"></i></button></td>
              <td class="p-2"><select name="period" class="w-full font-bold ${inpCls}"><option>H-6 Bulan</option><option>H-3 Bulan</option><option>H-1 Bulan</option><option>H-2 Minggu</option><option>H-1 Minggu</option><option>H-1 Hari</option></select></td>
              <td class="p-2"><input type="text" name="task" value="Target Pekerjaan Baru" class="w-full font-semibold ${inpCls}"></td>
              <td class="p-2"><input type="text" name="pic" placeholder="PIC..." class="w-full ${inpCls}"></td>
              <td class="p-2"><input type="text" name="notes" placeholder="Catatan..." class="w-full ${inpCls}"></td>
              <td class="p-2 text-center whitespace-nowrap">
                <button type="button" onclick="ajaxSaveRow('roadmap', ${id}, this)" class="bg-indigo-400 hover:bg-indigo-500 text-white font-bold p-1.5 rounded-lg text-xs mr-1 shadow-sm"><i class="fa-solid fa-floppy-disk"></i></button>
                <button type="button" onclick="ajaxDeleteRow('roadmap', ${id}, this)" class="text-rose-400 hover:text-rose-600 p-1.5"><i class="fa-solid fa-trash"></i></button>
              </td>
            </tr>`;
        } else if(tbl === 'panitia_contacts') {
          rowHtml = `
            <tr id="row-panitia_contacts-${id}" class="hover:bg-white/40 transition">
              <td class="p-2"><input type="text" name="role_name" value="Tugas Baru" class="w-full font-bold text-rose-900 ${inpCls}"></td>
              <td class="p-2"><input type="text" name="person_name" value="Nama Panitia" class="w-full font-semibold ${inpCls}"></td>
              <td class="p-2"><input type="text" name="phone" placeholder="08..." class="w-full font-mono ${inpCls}"></td>
              <td class="p-2"><input type="text" name="notes" placeholder="Catatan tugas..." class="w-full ${inpCls}"></td>
              <td class="p-2 text-center whitespace-nowrap no-print">
                <button type="button" onclick="ajaxSaveRow('panitia_contacts', ${id}, this)" class="bg-indigo-400 hover:bg-indigo-500 text-white font-bold p-1.5 rounded-lg text-xs mr-1 shadow-sm"><i class="fa-solid fa-floppy-disk"></i></button>
                <button type="button" onclick="ajaxDeleteRow('panitia_contacts', ${id}, this)" class="text-rose-400 hover:text-rose-600 p-1.5"><i class="fa-solid fa-trash"></i></button>
              </td>
            </tr>`;
        } else if(tbl === 'seserahan') {
          rowHtml = `
            <tr id="row-seserahan-${id}" class="hover:bg-white/40 transition">
              <td class="p-2 text-center"><button type="button" onclick="ajaxToggle('seserahan', ${id}, this)" class="text-base text-gray-300 hover:text-emerald-500"><i class="fa-solid fa-circle-check"></i></button></td>
              <td class="p-2"><input type="text" name="name" value="Barang Baru" class="w-full font-semibold ${inpCls}"></td>
              <td class="p-2"><input type="url" name="link" placeholder="https://..." class="w-full ${inpCls}"></td>
              <td class="p-2"><input type="text" name="contact" placeholder="WA Toko..." class="w-full ${inpCls}"></td>
              <td class="p-2"><input type="number" name="budget_cost" value="0" class="w-full ${inpCls}"></td>
              <td class="p-2"><input type="number" name="actual_cost" value="0" oninput="calcSisa(this)" class="w-full font-bold ${inpCls}"></td>
              <td class="p-2"><select name="pay_status" class="w-full font-bold ${inpCls}"><option value="DP">DP</option><option value="Lunas" selected>Lunas</option></select></td>
              <td class="p-2"><input type="number" name="paid" value="0" oninput="calcSisa(this)" class="w-full ${inpCls}"></td>
              <td class="p-2 font-bold text-amber-700 sisa-val">Rp 0</td>
              <td class="p-2 text-center whitespace-nowrap">
                <button type="button" onclick="ajaxSaveRow('seserahan', ${id}, this)" class="bg-emerald-400 hover:bg-emerald-500 text-white font-bold p-1.5 rounded-lg text-xs mr-1 shadow-sm"><i class="fa-solid fa-floppy-disk"></i></button>
                <button type="button" onclick="ajaxDeleteRow('seserahan', ${id}, this)" class="text-rose-400 hover:text-rose-600 p-1.5"><i class="fa-solid fa-trash"></i></button>
              </td>
            </tr>`;
        } else if(tbl === 'guests') {
          rowHtml = `
            <tr id="row-guests-${id}" class="hover:bg-white/40 transition">
              <td class="p-2"><input type="text" name="name" value="Tamu Baru" class="w-full font-semibold ${inpCls}"></td>
              <td class="p-2"><input type="text" name="phone" placeholder="08..." class="w-full font-mono ${inpCls}"></td>
              <td class="p-2"><select name="side" class="w-full ${inpCls}"><option>Pihak Pria</option><option>Pihak Wanita</option></select></td>
              <td class="p-2"><select name="invite_status" class="w-full font-bold ${inpCls}"><option>Belum Terkirim</option><option>Terkirim</option></select></td>
              <td class="p-2"><input type="text" name="address" placeholder="Alamat..." class="w-full ${inpCls}"></td>
              <td class="p-2"><select name="rsvp" class="w-full font-bold ${inpCls}"><option>Menunggu</option><option>Hadir</option><option>Tidak Hadir</option></select></td>
              <td class="p-2"><input type="text" name="notes" placeholder="Catatan..." class="w-full ${inpCls}"></td>
              <td class="p-2 text-center whitespace-nowrap">
                <button type="button" onclick="sendWhatsapp('Tamu Baru', this)" class="bg-emerald-500 hover:bg-emerald-600 text-white font-bold px-2 py-1.5 rounded-lg text-xs mr-1 shadow-sm transition"><i class="fa-brands fa-whatsapp text-sm"></i> Kirim</button>
                <button type="button" onclick="ajaxSaveRow('guests', ${id}, this)" class="bg-purple-400 hover:bg-purple-500 text-white font-bold p-1.5 rounded-lg text-xs mr-1 shadow-sm"><i class="fa-solid fa-floppy-disk"></i></button>
                <button type="button" onclick="ajaxDeleteRow('guests', ${id}, this)" class="text-rose-400 hover:text-rose-600 p-1.5"><i class="fa-solid fa-trash"></i></button>
              </td>
            </tr>`;
        } else if(tbl === 'amplop') {
          rowHtml = `
            <tr id="row-amplop-${id}" class="hover:bg-white/40 transition">
              <td class="p-2"><input type="text" name="giver_name" value="Tamu Pemberi" class="w-full font-semibold ${inpCls}"></td>
              <td class="p-2"><select name="gift_type" class="w-full font-bold ${inpCls}"><option value="Uang" selected>Uang Amplop</option><option value="Kado">Kado Barang</option></select></td>
              <td class="p-2"><input type="number" name="amount" value="0" class="w-full font-bold text-emerald-700 ${inpCls}"></td>
              <td class="p-2"><input type="text" name="gift_item" placeholder="Kado fisik..." class="w-full ${inpCls}"></td>
              <td class="p-2"><input type="text" name="notes" placeholder="Catatan..." class="w-full ${inpCls}"></td>
              <td class="p-2 text-center whitespace-nowrap">
                <button type="button" onclick="ajaxSaveRow('amplop', ${id}, this)" class="bg-emerald-500 hover:bg-emerald-600 text-white font-bold p-1.5 rounded-lg text-xs mr-1 shadow-sm"><i class="fa-solid fa-floppy-disk"></i></button>
                <button type="button" onclick="ajaxDeleteRow('amplop', ${id}, this)" class="text-rose-400 hover:text-rose-600 p-1.5"><i class="fa-solid fa-trash"></i></button>
              </td>
            </tr>`;
        } else if(tbl === 'kua_docs') {
          rowHtml = `
            <tr id="row-kua_docs-${id}" class="hover:bg-white/40 transition">
              <td class="p-2 text-center"><button type="button" onclick="ajaxToggle('kua_docs', ${id}, this)" class="text-base text-gray-300 hover:text-emerald-500"><i class="fa-solid fa-circle-check"></i></button></td>
              <td class="p-2"><input type="text" name="doc_name" value="Syarat Berkas Baru" class="w-full font-semibold ${inpCls}"></td>
              <td class="p-2"><input type="text" name="pic" placeholder="PIC..." class="w-full ${inpCls}"></td>
              <td class="p-2"><input type="text" name="notes" placeholder="Catatan..." class="w-full ${inpCls}"></td>
              <td class="p-2 text-center whitespace-nowrap">
                <button type="button" onclick="ajaxSaveRow('kua_docs', ${id}, this)" class="bg-indigo-400 hover:bg-indigo-500 text-white font-bold p-1.5 rounded-lg text-xs mr-1 shadow-sm"><i class="fa-solid fa-floppy-disk"></i></button>
                <button type="button" onclick="ajaxDeleteRow('kua_docs', ${id}, this)" class="text-rose-400 hover:text-rose-600 p-1.5"><i class="fa-solid fa-trash"></i></button>
              </td>
            </tr>`;
        } else if(tbl === 'seragam') {
          rowHtml = `
            <tr id="row-seragam-${id}" class="hover:bg-white/40 transition">
              <td class="p-2"><input type="text" name="receiver_name" value="Penerima Baru" class="w-full font-semibold ${inpCls}"></td>
              <td class="p-2"><select name="side" class="w-full ${inpCls}"><option>Keluarga Pria</option><option>Keluarga Wanita</option><option>Bridesmaid</option><option>Bestman / Groomsmen</option><option>Panitia Keluarga</option></select></td>
              <td class="p-2"><input type="text" name="fabric_meter" placeholder="2.5 Meter" class="w-full ${inpCls}"></td>
              <td class="p-2"><select name="status" class="w-full font-bold ${inpCls}"><option>Belum Diberi</option><option>Sudah Diberi Kain</option><option>Sedang Dijahit</option><option>Selesai Siap Pakai</option></select></td>
              <td class="p-2"><input type="text" name="notes" placeholder="Catatan..." class="w-full ${inpCls}"></td>
              <td class="p-2 text-center whitespace-nowrap">
                <button type="button" onclick="ajaxSaveRow('seragam', ${id}, this)" class="bg-indigo-400 hover:bg-indigo-500 text-white font-bold p-1.5 rounded-lg text-xs mr-1 shadow-sm"><i class="fa-solid fa-floppy-disk"></i></button>
                <button type="button" onclick="ajaxDeleteRow('seragam', ${id}, this)" class="text-rose-400 hover:text-rose-600 p-1.5"><i class="fa-solid fa-trash"></i></button>
              </td>
            </tr>`;
        } else if(tbl === 'music_playlist') {
          rowHtml = `
            <tr id="row-music_playlist-${id}" class="hover:bg-white/40 transition">
              <td class="p-2 text-center"><button type="button" onclick="ajaxToggle('music_playlist', ${id}, this)" class="text-base text-gray-300 hover:text-emerald-500"><i class="fa-solid fa-circle-check"></i></button></td>
              <td class="p-2"><input type="text" name="moment" value="Momen Acara Baru" class="w-full font-semibold ${inpCls}"></td>
              <td class="p-2"><input type="text" name="song_title" value="Judul Lagu" class="w-full font-bold text-amber-800 ${inpCls}"></td>
              <td class="p-2"><input type="text" name="notes" placeholder="Catatan..." class="w-full ${inpCls}"></td>
              <td class="p-2 text-center whitespace-nowrap">
                <button type="button" onclick="ajaxSaveRow('music_playlist', ${id}, this)" class="bg-amber-400 hover:bg-amber-500 text-white font-bold p-1.5 rounded-lg text-xs mr-1 shadow-sm"><i class="fa-solid fa-floppy-disk"></i></button>
                <button type="button" onclick="ajaxDeleteRow('music_playlist', ${id}, this)" class="text-rose-400 hover:text-rose-600 p-1.5"><i class="fa-solid fa-trash"></i></button>
              </td>
            </tr>`;
        } else if(tbl === 'timeline') {
          rowHtml = `
            <tr id="row-timeline-${id}" class="hover:bg-white/40 transition">
              <td class="p-2 text-center no-print"><button type="button" onclick="ajaxToggle('timeline', ${id}, this)" class="text-base text-gray-300 hover:text-emerald-500"><i class="fa-solid fa-circle-check"></i></button></td>
              <td class="p-2"><input type="text" name="time" value="08:00" class="w-full font-bold text-amber-800 ${inpCls}"></td>
              <td class="p-2"><input type="text" name="activity" value="Agenda Baru" class="w-full font-semibold ${inpCls}"></td>
              <td class="p-2"><input type="text" name="pic" placeholder="PIC..." class="w-full ${inpCls}"></td>
              <td class="p-2"><input type="text" name="notes" placeholder="Catatan..." class="w-full ${inpCls}"></td>
              <td class="p-2 text-center whitespace-nowrap no-print">
                <button type="button" onclick="ajaxSaveRow('timeline', ${id}, this)" class="bg-amber-400 hover:bg-amber-500 text-white font-bold p-1.5 rounded-lg text-xs mr-1 shadow-sm"><i class="fa-solid fa-floppy-disk"></i></button>
                <button type="button" onclick="ajaxDeleteRow('timeline', ${id}, this)" class="text-rose-400 hover:text-rose-600 p-1.5"><i class="fa-solid fa-trash"></i></button>
              </td>
            </tr>`;
        } else if(tbl === 'checklist') {
          rowHtml = `
            <tr id="row-checklist-${id}" class="hover:bg-white/40 transition">
              <td class="p-2 text-center"><button type="button" onclick="ajaxToggle('checklist', ${id}, this)" class="text-base text-gray-300 hover:text-emerald-500"><i class="fa-solid fa-circle-check"></i></button></td>
              <td class="p-2"><input type="text" name="item" value="Barang Baru" class="w-full font-semibold ${inpCls}"></td>
              <td class="p-2"><input type="text" name="pic" placeholder="PIC..." class="w-full ${inpCls}"></td>
              <td class="p-2 text-center whitespace-nowrap">
                <button type="button" onclick="ajaxSaveRow('checklist', ${id}, this)" class="bg-rose-400 hover:bg-rose-500 text-white font-bold p-1.5 rounded-lg text-xs mr-1 shadow-sm"><i class="fa-solid fa-floppy-disk"></i></button>
                <button type="button" onclick="ajaxDeleteRow('checklist', ${id}, this)" class="text-rose-400 hover:text-rose-600 p-1.5"><i class="fa-solid fa-trash"></i></button>
              </td>
            </tr>`;
        }

        tbody.insertAdjacentHTML('beforeend', rowHtml);
        showToast("Baris Ditambahkan di Bawah!");
      });
    }

    function ajaxDeleteRow(tbl, id, btn) {
      if(!confirm("Yakin ingin menghapus baris ini?")) return;
      fetch('/api/delete_row/' + tbl + '/' + id)
      .then(res => res.json())
      .then(() => {
        document.getElementById('row-' + tbl + '-' + id).remove();
        showToast("Baris Terhapus!");
      });
    }

    function ajaxToggle(tbl, id, btn) {
      fetch('/api/toggle/' + tbl + '/' + id)
      .then(res => res.json())
      .then(data => {
        const tr = document.getElementById('row-' + tbl + '-' + id);
        if(data.is_done) {
          btn.className = 'text-base text-emerald-500';
          tr.classList.add('bg-emerald-100/40');
        } else {
          btn.className = 'text-base text-gray-300 hover:text-emerald-500';
          tr.classList.remove('bg-emerald-100/40');
        }
        showToast("Status Diperbarui!");
      });
    }
  </script>
  {% endraw %}

  <script>
    const chartLabels = {{ cat_labels | tojson }};
    const chartRealValues = {{ cat_real_values | tojson }};
    const chartEstValues = {{ cat_est_values | tojson }};

    const ctxPie = document.getElementById('categoryPieChart');
    if(ctxPie && chartLabels.length > 0) {
      new Chart(ctxPie, {
        type: 'doughnut',
        data: {
          labels: chartLabels,
          datasets: [{
            data: chartRealValues,
            backgroundColor: [
              '#fb7185', '#38bdf8', '#818cf8', '#34d399', '#fbbf24', '#c084fc', '#a3e635'
            ],
            borderWidth: 2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 10 } } }
          }
        }
      });
    }

    const ctxBar = document.getElementById('comparisonBarChart');
    if(ctxBar && chartLabels.length > 0) {
      new Chart(ctxBar, {
        type: 'bar',
        data: {
          labels: chartLabels,
          datasets: [
            {
              label: 'Estimasi (Rp)',
              data: chartEstValues,
              backgroundColor: '#94a3b8',
              borderRadius: 6
            },
            {
              label: 'Realisasi (Rp)',
              data: chartRealValues,
              backgroundColor: '{{ "#fb7185" if is_pink else "#38bdf8" }}',
              borderRadius: 6
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: { ticks: { font: { size: 9 } } },
            x: { ticks: { font: { size: 9 } } }
          },
          plugins: {
            legend: { position: 'top', labels: { boxWidth: 12, font: { size: 10 } } }
          }
        }
      });
    }

    const targetDate = new Date("{{ s[3] }}").getTime();
    setInterval(() => {
      const diff = targetDate - new Date().getTime();
      const days = Math.ceil(diff / (1000 * 60 * 60 * 24));
      document.getElementById('countdown').innerHTML = days >= 0 ? `Tinggal <b>${days}</b> Hari Lagi Menuju Hari Bahagia!` : "Selamat Hari Bahagia!";
    }, 1000);
  </script>
</body>
</html>
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username'].lower().strip()
        pwd = request.form['password']
        conn = sqlite3.connect('nikah.db')
        c = conn.cursor()
        row = c.execute('SELECT id, password FROM users WHERE username = ?', (user,)).fetchone()
        
        if not row:
            c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (user, pwd))
            uid = c.lastrowid
            c.execute('INSERT INTO settings (user_id, groom, bride, wedding_date, budget, theme, wali_nikah, saksi1, saksi2, mahar_desc) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                      (uid, 'Pengantin Pria', 'Pengantin Wanita', datetime.now().strftime('%Y-%m-%d'), 50000000, 'pink', '', '', '', ''))
            conn.commit()
            conn.close()
            seed_user_defaults(uid)
            session['user_id'] = uid
            session['username'] = user
            return redirect(url_for('index'))
        else:
            conn.close()
            if row[1] == pwd:
                session['user_id'] = row[0]
                session['username'] = user
                seed_user_defaults(row[0])
                return redirect(url_for('index'))
    return redirect(url_for('login_page'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/login_page')
def login_page():
    return '''<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"><script src="https://cdn.tailwindcss.com"></script><title>Login</title></head><body class="bg-rose-50/70 flex items-center justify-center min-h-screen p-4 font-sans"><div class="bg-rose-100/80 p-8 rounded-3xl shadow-md w-full max-w-sm text-center border border-rose-200"><div class="text-3xl mb-2">💍</div><h2 class="text-xl font-bold text-rose-950 font-serif">Wedding Planner Pro</h2><p class="text-xs text-rose-700 mb-6">Kelola Pernikahan Impianmu</p><form action="/login" method="POST" class="space-y-3 text-left text-xs"><div><label class="font-bold text-rose-900">Username</label><input type="text" name="username" placeholder="riyan" required class="w-full p-2.5 bg-rose-50 border border-rose-200 rounded-xl mt-1 text-rose-950"></div><div><label class="font-bold text-rose-900">Password</label><input type="password" name="password" placeholder="123" required class="w-full p-2.5 bg-rose-50 border border-rose-200 rounded-xl mt-1 text-rose-950"></div><button type="submit" class="w-full bg-rose-400 hover:bg-rose-500 text-white font-bold py-2.5 rounded-xl shadow-sm transition">Masuk / Daftar Akun</button></form></div></body></html>'''

@app.route('/')
def index():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    uid = session['user_id']
    seed_user_defaults(uid)

    conn = sqlite3.connect('nikah.db')
    c = conn.cursor()
    s = c.execute('SELECT * FROM settings WHERE user_id = ?', (uid,)).fetchone()

    vendors = c.execute('SELECT id, user_id, name, category, budget_cost, actual_cost, paid, pay_status, bank_info, contact, due_date, notes, is_done FROM vendors WHERE user_id = ? ORDER BY id ASC', (uid,)).fetchall()
    roadmap = c.execute('SELECT id, user_id, period, task, pic, notes, is_done FROM roadmap WHERE user_id = ? ORDER BY id ASC', (uid,)).fetchall()
    panitia_contacts = c.execute('SELECT id, user_id, role_name, person_name, phone, notes FROM panitia_contacts WHERE user_id = ? ORDER BY id ASC', (uid,)).fetchall()
    seserahan = c.execute('SELECT id, user_id, name, link, contact, budget_cost, actual_cost, paid, pay_status, is_bought FROM seserahan WHERE user_id = ? ORDER BY id ASC', (uid,)).fetchall()
    guests = c.execute('SELECT id, user_id, name, phone, side, invite_status, address, rsvp, notes FROM guests WHERE user_id = ? ORDER BY id ASC', (uid,)).fetchall()
    timeline = c.execute('SELECT id, user_id, time, activity, pic, notes, is_done FROM timeline WHERE user_id = ? ORDER BY id ASC', (uid,)).fetchall()
    checklist = c.execute('SELECT id, user_id, item, budget_cost, actual_cost, paid, pay_status, pic, is_done FROM checklist WHERE user_id = ? ORDER BY id ASC', (uid,)).fetchall()
    amplop_rows = c.execute('SELECT id, user_id, giver_name, gift_type, amount, gift_item, notes FROM amplop WHERE user_id = ? ORDER BY id ASC', (uid,)).fetchall()
    kua_docs = c.execute('SELECT id, user_id, doc_name, pic, notes, is_done FROM kua_docs WHERE user_id = ? ORDER BY id ASC', (uid,)).fetchall()
    seragam = c.execute('SELECT id, user_id, receiver_name, side, fabric_meter, status, notes FROM seragam WHERE user_id = ? ORDER BY id ASC', (uid,)).fetchall()
    music_playlist = c.execute('SELECT id, user_id, moment, song_title, notes, is_ready FROM music_playlist WHERE user_id = ? ORDER BY id ASC', (uid,)).fetchall()
    conn.close()

    total_est = 0
    total_real = 0
    total_paid = 0
    cat_est = {}
    cat_real = {}

    for v in vendors:
        b_est = v[4] or 0
        b_act = v[5] or 0
        b_paid = v[6] or 0
        total_est += b_est
        total_real += b_act
        total_paid += b_paid
        cat = v[3] or 'Lain-lain'
        cat_est[cat] = cat_est.get(cat, 0) + b_est
        cat_real[cat] = cat_real.get(cat, 0) + (b_act if b_act > 0 else b_est)

    all_cats = list(set(list(cat_est.keys()) + list(cat_real.keys())))
    if not all_cats:
        all_cats = ['Venue & Catering', 'Dekorasi & Tenda', 'Busana & Make Up']
        cat_labels = all_cats
        cat_est_values = [0, 0, 0]
        cat_real_values = [0, 0, 0]
    else:
        cat_labels = all_cats
        cat_est_values = [cat_est.get(c, 0) for c in all_cats]
        cat_real_values = [cat_real.get(c, 0) for c in all_cats]

    selisih = total_est - total_real
    abs_selisih = abs(selisih)
    sisa_bayar = total_real - total_paid

    ven_total = len(vendors)
    ven_done = sum(1 for v in vendors if v[7] == 'Lunas')
    ven_pct = round((ven_done / ven_total * 100)) if ven_total else 0

    ses_total = len(seserahan)
    ses_bought = sum(1 for item in seserahan if item[9] == 1)
    ses_pct = round((ses_bought / ses_total * 100)) if ses_total else 0

    guest_total = len(guests)
    invite_sent = sum(1 for g in guests if g[5] == 'Terkirim')
    invite_pct = round((invite_sent / guest_total * 100)) if guest_total else 0
    guest_hadir = sum(1 for g in guests if g[7] == 'Hadir')

    time_total = len(timeline)
    time_done = sum(1 for t in timeline if len(t) > 6 and t[6] == 1)
    time_pct = round((time_done / time_total * 100)) if time_total else 0

    chk_total = len(checklist)
    chk_done = sum(1 for ch in checklist if ch[8] == 1)
    chk_pct = round((chk_done / chk_total * 100)) if chk_total else 0

    kua_total = len(kua_docs)
    kua_done = sum(1 for k in kua_docs if k[5] == 1)

    total_amplop_uang = sum((a[4] or 0) for a in amplop_rows if a[3] == 'Uang')
    total_kado_barang = sum(1 for a in amplop_rows if a[3] == 'Kado')

    overall_pct = round((ven_pct + ses_pct + invite_pct + time_pct + chk_pct) / 5)

    return render_template_string(APP_HTML, s=s, vendors=vendors, roadmap=roadmap, panitia_contacts=panitia_contacts,
                                  seserahan=seserahan, guests=guests, timeline=timeline, checklist=checklist, amplop_rows=amplop_rows,
                                  kua_docs=kua_docs, seragam=seragam, music_playlist=music_playlist,
                                  total_est=total_est, total_real=total_real, selisih=selisih, abs_selisih=abs_selisih, sisa_bayar=sisa_bayar, total_paid=total_paid,
                                  ven_total=ven_total, ven_done=ven_done, ven_pct=ven_pct,
                                  ses_total=ses_total, ses_bought=ses_bought, ses_pct=ses_pct,
                                  guest_total=guest_total, invite_sent=invite_sent, invite_pct=invite_pct, guest_hadir=guest_hadir,
                                  time_total=time_total, time_done=time_done, time_pct=time_pct,
                                  chk_total=chk_total, chk_done=chk_done, chk_pct=chk_pct,
                                  kua_total=kua_total, kua_done=kua_done,
                                  total_amplop_uang=total_amplop_uang, total_kado_barang=total_kado_barang,
                                  overall_pct=overall_pct, cat_labels=cat_labels, cat_est_values=cat_est_values, cat_real_values=cat_real_values,
                                  username=session['username'].capitalize())

@app.route('/sync_guests_to_amplop')
def sync_guests_to_amplop():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    uid = session['user_id']
    conn = sqlite3.connect('nikah.db')
    c = conn.cursor()
    hadir_guests = c.execute("SELECT name FROM guests WHERE user_id = ? AND rsvp = 'Hadir'", (uid,)).fetchall()
    for g in hadir_guests:
        exists = c.execute("SELECT 1 FROM amplop WHERE user_id = ? AND giver_name = ?", (uid, g[0])).fetchone()
        if not exists:
            c.execute("INSERT INTO amplop (user_id, giver_name, gift_type, amount, gift_item, notes) VALUES (?, ?, 'Uang', 0, '', 'Hadir')", (uid, g[0]))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/export_guests_csv')
def export_guests_csv():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    conn = sqlite3.connect('nikah.db')
    guests = conn.cursor().execute('SELECT name, phone, side, invite_status, address, rsvp, notes FROM guests WHERE user_id = ?', (session['user_id'],)).fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Nama Tamu', 'No WhatsApp', 'Pihak', 'Status Undangan', 'Alamat', 'RSVP Kehadiran', 'Catatan'])
    for g in guests:
        writer.writerow(g)
    
    return Response('\ufeff' + output.getvalue(), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=Daftar_Tamu_Pernikahan.csv'})

@app.route('/backup_database')
def backup_database():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    db_path = os.path.join(os.path.dirname(__file__), 'nikah.db')
    return send_file(db_path, as_attachment=True, download_name=f'Backup_Nikah_{datetime.now().strftime("%Y%m%d")}.db')

@app.route('/update_kua_details', methods=['POST'])
def update_kua_details():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    conn = sqlite3.connect('nikah.db')
    conn.cursor().execute('UPDATE settings SET wali_nikah=?, saksi1=?, saksi2=?, mahar_desc=? WHERE user_id=?',
                          (request.form['wali_nikah'], request.form['saksi1'], request.form['saksi2'], request.form['mahar_desc'], session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/api/add_empty_row/<tbl>')
def api_add_empty_row(tbl):
    if 'user_id' not in session: return jsonify({'error': 'unauthorized'}), 401
    uid = session['user_id']
    conn = sqlite3.connect('nikah.db')
    c = conn.cursor()
    new_id = None
    if tbl == 'vendors':
        c.execute("INSERT INTO vendors (user_id, name, category, budget_cost, actual_cost, paid, pay_status, bank_info, contact, due_date, notes, is_done) VALUES (?, 'Pos / Vendor Baru', 'Venue & Catering', 0, 0, 0, 'DP', '', '', '', '', 0)", (uid,))
    elif tbl == 'roadmap':
        c.execute("INSERT INTO roadmap (user_id, period, task, pic, notes, is_done) VALUES (?, 'H-6 Bulan', 'Target Pekerjaan Baru', '', '', 0)", (uid,))
    elif tbl == 'panitia_contacts':
        c.execute("INSERT INTO panitia_contacts (user_id, role_name, person_name, phone, notes) VALUES (?, 'Tugas / Peran Baru', 'Nama Panitia', '', '')", (uid,))
    elif tbl == 'seserahan':
        c.execute("INSERT INTO seserahan (user_id, name, link, contact, budget_cost, actual_cost, paid, pay_status, is_bought) VALUES (?, 'Barang Baru', '', '', 0, 0, 0, 'Lunas', 0)", (uid,))
    elif tbl == 'guests':
        c.execute("INSERT INTO guests (user_id, name, phone, side, invite_status, address, rsvp, notes) VALUES (?, 'Tamu Baru', '', 'Pihak Pria', 'Belum Terkirim', '', 'Menunggu', '')", (uid,))
    elif tbl == 'timeline':
        c.execute("INSERT INTO timeline (user_id, time, activity, pic, notes, is_done) VALUES (?, '08:00', 'Agenda Baru', '', '', 0)", (uid,))
    elif tbl == 'checklist':
        c.execute("INSERT INTO checklist (user_id, item, budget_cost, actual_cost, paid, pay_status, pic, is_done) VALUES (?, 'Barang Baru', 0, 0, 0, 'Lunas', '', 0)", (uid,))
    elif tbl == 'amplop':
        c.execute("INSERT INTO amplop (user_id, giver_name, gift_type, amount, gift_item, notes) VALUES (?, 'Tamu Pemberi', 'Uang', 0, '', '')", (uid,))
    elif tbl == 'kua_docs':
        c.execute("INSERT INTO kua_docs (user_id, doc_name, pic, notes, is_done) VALUES (?, 'Syarat Berkas Baru', '', '', 0)", (uid,))
    elif tbl == 'seragam':
        c.execute("INSERT INTO seragam (user_id, receiver_name, side, fabric_meter, status, notes) VALUES (?, 'Penerima Baru', 'Keluarga Pria', '2.5 Meter', 'Belum Diberi', '')", (uid,))
    elif tbl == 'music_playlist':
        c.execute("INSERT INTO music_playlist (user_id, moment, song_title, notes, is_ready) VALUES (?, 'Momen Acara Baru', 'Judul Lagu', '', 0)", (uid,))
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok', 'id': new_id})

@app.route('/api/update_row/<tbl>/<int:id>', methods=['POST'])
def api_update_row(tbl, id):
    if 'user_id' not in session: return jsonify({'error': 'unauthorized'}), 401
    uid = session['user_id']
    conn = sqlite3.connect('nikah.db')
    c = conn.cursor()
    if tbl == 'vendors':
        c.execute("UPDATE vendors SET category=?, name=?, budget_cost=?, actual_cost=?, paid=?, pay_status=?, bank_info=?, contact=?, due_date=?, notes=? WHERE id=? AND user_id=?",
                  (request.form.get('category'), request.form.get('name'), int(request.form.get('budget_cost') or 0), int(request.form.get('actual_cost') or 0), int(request.form.get('paid') or 0), request.form.get('pay_status'), request.form.get('bank_info'), request.form.get('contact'), request.form.get('due_date'), request.form.get('notes'), id, uid))
    elif tbl == 'roadmap':
        c.execute("UPDATE roadmap SET period=?, task=?, pic=?, notes=? WHERE id=? AND user_id=?",
                  (request.form.get('period'), request.form.get('task'), request.form.get('pic'), request.form.get('notes'), id, uid))
    elif tbl == 'panitia_contacts':
        c.execute("UPDATE panitia_contacts SET role_name=?, person_name=?, phone=?, notes=? WHERE id=? AND user_id=?",
                  (request.form.get('role_name'), request.form.get('person_name'), request.form.get('phone'), request.form.get('notes'), id, uid))
    elif tbl == 'seserahan':
        c.execute("UPDATE seserahan SET name=?, link=?, contact=?, budget_cost=?, actual_cost=?, paid=?, pay_status=? WHERE id=? AND user_id=?",
                  (request.form.get('name'), request.form.get('link'), request.form.get('contact'), int(request.form.get('budget_cost') or 0), int(request.form.get('actual_cost') or 0), int(request.form.get('paid') or 0), request.form.get('pay_status'), id, uid))
    elif tbl == 'guests':
        c.execute("UPDATE guests SET name=?, phone=?, side=?, invite_status=?, address=?, rsvp=?, notes=? WHERE id=? AND user_id=?",
                  (request.form.get('name'), request.form.get('phone'), request.form.get('side'), request.form.get('invite_status'), request.form.get('address'), request.form.get('rsvp'), request.form.get('notes'), id, uid))
    elif tbl == 'timeline':
        c.execute("UPDATE timeline SET time=?, activity=?, pic=?, notes=? WHERE id=? AND user_id=?",
                  (request.form.get('time'), request.form.get('activity'), request.form.get('pic'), request.form.get('notes'), id, uid))
    elif tbl == 'checklist':
        c.execute("UPDATE checklist SET item=?, pic=? WHERE id=? AND user_id=?",
                  (request.form.get('item'), request.form.get('pic'), id, uid))
    elif tbl == 'amplop':
        c.execute("UPDATE amplop SET giver_name=?, gift_type=?, amount=?, gift_item=?, notes=? WHERE id=? AND user_id=?",
                  (request.form.get('giver_name'), request.form.get('gift_type'), int(request.form.get('amount') or 0), request.form.get('gift_item'), request.form.get('notes'), id, uid))
    elif tbl == 'kua_docs':
        c.execute("UPDATE kua_docs SET doc_name=?, pic=?, notes=? WHERE id=? AND user_id=?",
                  (request.form.get('doc_name'), request.form.get('pic'), request.form.get('notes'), id, uid))
    elif tbl == 'seragam':
        c.execute("UPDATE seragam SET receiver_name=?, side=?, fabric_meter=?, status=?, notes=? WHERE id=? AND user_id=?",
                  (request.form.get('receiver_name'), request.form.get('side'), request.form.get('fabric_meter'), request.form.get('status'), request.form.get('notes'), id, uid))
    elif tbl == 'music_playlist':
        c.execute("UPDATE music_playlist SET moment=?, song_title=?, notes=? WHERE id=? AND user_id=?",
                  (request.form.get('moment'), request.form.get('song_title'), request.form.get('notes'), id, uid))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/api/delete_row/<tbl>/<int:id>')
def api_delete_row(tbl, id):
    if 'user_id' not in session: return jsonify({'error': 'unauthorized'}), 401
    conn = sqlite3.connect('nikah.db')
    conn.cursor().execute(f"DELETE FROM {tbl} WHERE id=? AND user_id=?", (id, session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/api/toggle/<tbl>/<int:id>')
def api_toggle(tbl, id):
    if 'user_id' not in session: return jsonify({'error': 'unauthorized'}), 401
    conn = sqlite3.connect('nikah.db')
    c = conn.cursor()
    col = 'is_bought' if tbl == 'seserahan' else ('is_ready' if tbl == 'music_playlist' else 'is_done')
    if tbl == 'vendors':
        curr = c.execute("SELECT pay_status FROM vendors WHERE id=? AND user_id=?", (id, session['user_id'])).fetchone()[0]
        new_val = 'DP' if curr == 'Lunas' else 'Lunas'
        c.execute("UPDATE vendors SET pay_status=? WHERE id=? AND user_id=?", (new_val, id, session['user_id']))
        is_done = (new_val == 'Lunas')
    else:
        c.execute(f"UPDATE {tbl} SET {col} = 1 - {col} WHERE id=? AND user_id=?", (id, session['user_id']))
        is_done = c.execute(f"SELECT {col} FROM {tbl} WHERE id=? AND user_id=?", (id, session['user_id'])).fetchone()[0]
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok', 'is_done': is_done})

@app.route('/update_settings', methods=['POST'])
def update_settings():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    conn = sqlite3.connect('nikah.db')
    conn.cursor().execute('UPDATE settings SET groom=?, bride=?, wedding_date=?, budget=?, theme=? WHERE user_id=?',
                          (request.form['groom'], request.form['bride'], request.form['wedding_date'], int(request.form['budget'] or 0), request.form['theme'], session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)