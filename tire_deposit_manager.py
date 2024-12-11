# tire_deposit_manager.py

import os
import logging
import shutil
import sqlite3
import sys
import time
import glob
import tempfile
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, A6
from reportlab.lib.units import mm
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QMessageBox,
    QLabel, QFormLayout, QDialog, QComboBox, QMenu, QFileDialog,
    QTabWidget, QInputDialog, QCompleter, QListWidget,
    QPlainTextEdit, QHeaderView, QTextEdit, QDateEdit, QListWidget, QListWidgetItem, QCheckBox
)
from PySide6.QtGui import QAction, QColor, QPixmap, QIcon
from PySide6.QtCore import Qt, QTimer, QSize, QSettings, QDate
import traceback
import platform
import matplotlib.pyplot as plt
import win32print
import win32api

# Inicjalizacja aplikacji PySide6
app = QApplication(sys.argv)

#Upewnij się, że zmienna DATABASE_PATH wskazuje na katalog Dane w C:\Program Files\Menadżer Depozytów Opon
APP_DATA_DIR = r"C:\Program Files\Menadżer Depozytów Opon"
DATA_DIR = os.path.join(APP_DATA_DIR, "Dane")
DATABASE_PATH = os.path.join(DATA_DIR, "tire_deposits.db")



def check_admin_rights():
    """Sprawdza, czy aplikacja działa jako administrator."""
    if not ctypes.windll.shell32.IsUserAnAdmin():
        QMessageBox.warning(None, "Brak uprawnień", "Uruchom aplikację jako administrator.")
        sys.exit()


def initialize_test_data(conn):
    """Wstaw dane testowe do bazy danych, jeśli są potrzebne."""
    try:
        cursor = conn.cursor()

        # Dodaj klienta testowego, jeśli brak rekordów
        cursor.execute("SELECT COUNT(*) FROM clients")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO clients (name, phone_number) VALUES (?, ?)", ("Test Client", "123456789"))

        # Dodaj depozyt testowy, jeśli brak rekordów
        cursor.execute("SELECT COUNT(*) FROM deposits")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO deposits (client_id, tire_brand, tire_size, quantity, deposit_date)
                VALUES (1, ?, ?, ?, ?)
            """, ("Michelin", "205/55 R16", 4, datetime.now().strftime("%Y-%m-%d")))

        conn.commit()
        logger.info("Dane testowe zostały dodane do bazy danych.")
    except sqlite3.Error as e:
        logger.error(f"Błąd podczas inicjalizacji danych testowych: {e}")


# Funkcja do uzyskania ścieżki pliku w katalogu programu
def get_file_path(filename):
    """Zapewnia, że pliki są zapisywane w katalogu programu."""
    program_dir = os.path.abspath(os.path.dirname(__file__))  # Pobiera katalog, w którym znajduje się skrypt
    return os.path.join(program_dir, filename)

# Ścieżki do bazy danych i logów
DATABASE_PATH = os.path.join(APP_DATA_DIR, "Dane", "tire_deposits.db")
LOG_FILE = get_file_path("application.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

#Upewnij się, że katalog Dane jest tworzony, jeśli nie istnieje
DATA_DIR = os.path.join(APP_DATA_DIR, "Dane")
os.makedirs(DATA_DIR, exist_ok=True)


# Jeśli baza danych nie istnieje, skopiuj ją z zasobów

def ensure_database_exists():
    """Sprawdza istnienie bazy danych i kopiuje ją z zasobów, jeśli brak."""
    if not os.path.exists(DATABASE_PATH):
        # Ścieżka do domyślnej bazy danych w zasobach
        source_db_path = resource_path("Dane/tire_deposits.db")

        # Jeśli baza w zasobach istnieje, kopiujemy ją do lokalizacji docelowej
        if os.path.exists(source_db_path):
            shutil.copy(source_db_path, DATABASE_PATH)
            logger.info(f"Skopiowano bazę danych do {DATABASE_PATH}")
        else:
            logger.error(f"Nie znaleziono pliku bazy danych: {source_db_path}")
            raise FileNotFoundError(f"Nie znaleziono pliku bazy danych: {source_db_path}")


# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),  # Zapis do pliku
        logging.StreamHandler()        # Wyświetlanie w konsoli
    ]
)
logger = logging.getLogger(__name__)

# Informacja o lokalizacji logów
logger.info(f"Logi aplikacji zapisywane w: {LOG_FILE}")

# Funkcje pomocnicze
def resource_path(relative_path):
    """Zwraca ścieżkę do zasobu, uwzględniając środowisko PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Utworzenie katalogu danych i kopia bazy danych, jeśli nie istnieje
ensure_database_exists()

# Funkcja tworzenia połączenia z bazą danych
def create_connection():
    """Tworzy połączenie z bazą danych SQLite."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        logger.info(f"Połączono z bazą danych: {DATABASE_PATH}")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Błąd połączenia z bazą danych: {e}")
        sys.exit(1)

def create_tables(conn):
    """Tworzy tabele w bazie danych lub aktualizuje ich strukturę."""
    try:
        cursor = conn.cursor()

        # Tworzenie tabel, jeśli nie istnieją
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone_number TEXT,
                email TEXT,
                additional_info TEXT,
                discount REAL DEFAULT 0,
                barcode TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deposits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER,
                car_model TEXT,
                registration_number TEXT,
                tire_brand TEXT,
                tire_size TEXT,
                quantity INTEGER,
                location TEXT,
                washing BOOLEAN,
                conservation BOOLEAN,
                deposit_date TEXT,
                issue_date TEXT,
                status TEXT,
                duration INTEGER,
                season TEXT,
                expected_return_date TEXT,
                technical_condition TEXT,
                storage_date TEXT,
                price REAL,
                FOREIGN KEY(client_id) REFERENCES clients(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deposit_id INTEGER,
                change_date TEXT,
                user TEXT,
                description TEXT,
                FOREIGN KEY(deposit_id) REFERENCES deposits(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS client_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER,
                interaction_date TEXT,
                notes TEXT,
                FOREIGN KEY(client_id) REFERENCES clients(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                to_address TEXT,
                subject TEXT,
                body TEXT,
                sent_date TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                is_default BOOLEAN DEFAULT 0
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                subject TEXT,
                body TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER,
                order_date TEXT,
                expected_delivery_date TEXT,
                status TEXT,
                notes TEXT,
                FOREIGN KEY(client_id) REFERENCES clients(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                brand_model TEXT,
                size TEXT,
                quantity INTEGER,
                price REAL,
                FOREIGN KEY(order_id) REFERENCES orders(id)
            )
        ''')

        # Tworzenie tabeli 'inventory' (Opony na stanie)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand_model TEXT NOT NULL,
                size TEXT NOT NULL,
                quantity INTEGER DEFAULT 0,
                price REAL DEFAULT 0.0,
                dot TEXT
            )
        ''')

        # Dodawanie brakujących kolumn do istniejących tabel
        def add_missing_columns(table, columns):
            cursor.execute(f"PRAGMA table_info({table})")
            existing_columns = [column[1] for column in cursor.fetchall()]
            for column_name, column_def in columns.items():
                if column_name not in existing_columns:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column_name} {column_def}")

        # Dodawanie brakujących kolumn do tabel
        add_missing_columns("clients", {
            "email": "TEXT",
            "discount": "REAL DEFAULT 0",
            "barcode": "TEXT"
        })
        add_missing_columns("deposits", {
            "technical_condition": "TEXT",
            "storage_date": "TEXT",
            "price": "REAL",
            "season": "TEXT",
            "expected_return_date": "TEXT"
        })
        add_missing_columns("inventory", {
            "brand_model": "TEXT NOT NULL",
            "size": "TEXT NOT NULL",
            "quantity": "INTEGER DEFAULT 0",
            "price": "REAL DEFAULT 0.0",
            "dot": "TEXT",
            "notes": "TEXT DEFAULT ''",  # Dodanie kolumny 'notes'
            "season_type": "TEXT DEFAULT 'Letnia'"  # Dodanie kolumny 'season_type'
        })

        # Zatwierdzenie zmian
        conn.commit()
        logger.info("Tabele bazy danych zostały utworzone lub zaktualizowane.")
    except sqlite3.Error as e:
        logger.error(f"Błąd tworzenia lub aktualizacji tabel: {e}")

        # Dodanie domyślnego szablonu e-mail
        create_default_email_template(conn)






def create_default_email_template(conn):
    """Tworzy domyślny szablon e-mail, jeśli nie istnieje."""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM email_templates")
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.execute('''
                INSERT INTO email_templates (name, subject, body)
                VALUES (?, ?, ?)
            ''', (
                "Przypomnienie o zwrocie",
                "Przypomnienie o zwrocie opon",
                "Szanowny/a {client_name},\n\nPrzypominamy o oczekiwanym zwrocie opon do dnia {expected_return_date}.\n\nPozdrawiamy,\n{company_name}"
            ))
            conn.commit()
            logger.info("Dodano domyślny szablon e-mail.")
    except Exception as e:
        logger.error(f"Błąd podczas tworzenia domyślnego szablonu e-mail: {e}")

def resource_path(relative_path):
    """Funkcja do obsługi ścieżek zasobów w PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# Funkcje generowania PDF
def generate_pdf_label(deposit_id, client_name, tire_brand, tire_size, quantity, logo_path):
    """Generuje etykietę PDF."""
    output_path = get_file_path(f"label_deposit_{deposit_id}.pdf")  # Tworzy plik w katalogu programu
    logger.info(f"Generowanie etykiety PDF w: {output_path}")
    
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A6
    from reportlab.lib.units import mm
    
    c = canvas.Canvas(output_path, pagesize=A6)
    width, height = A6

    # Dodanie logo
    if os.path.exists(logo_path):
        c.drawImage(logo_path, 10 * mm, height - 30 * mm, width=40 * mm, preserveAspectRatio=True, mask='auto')
    else:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(10 * mm, height - 20 * mm, "Logo nie znalezione")

    # Nagłówek
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, height - 40 * mm, "Etykieta Depozytu")

    # Informacje o depozycie
    c.setFont("Helvetica", 10)
    c.drawString(10 * mm, height - 50 * mm, f"ID Depozytu: {deposit_id}")
    c.drawString(10 * mm, height - 55 * mm, f"Klient: {client_name}")
    c.drawString(10 * mm, height - 60 * mm, f"Marka Opon: {tire_brand}")
    c.drawString(10 * mm, height - 65 * mm, f"Rozmiar Opon: {tire_size}")
    c.drawString(10 * mm, height - 70 * mm, f"Ilość: {quantity}")
    c.drawString(10 * mm, height - 75 * mm, f"Data: {datetime.now().strftime('%Y-%m-%d')}")

    c.save()
    logger.info(f"Etykieta PDF wygenerowana: {output_path}")
    return output_path


def generate_pdf_confirmation(deposit_id, client_name, deposit_details, logo_path):
    """Generuje potwierdzenie PDF."""
    output_path = get_file_path(f"confirmation_{deposit_id}.pdf")  # Tworzy plik w katalogu programu
    logger.info(f"Generowanie potwierdzenia PDF w: {output_path}")
    
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm

    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    # Dodanie logo
    if os.path.exists(logo_path):
        c.drawImage(logo_path, 10 * mm, height - 30 * mm, width=60 * mm, preserveAspectRatio=True, mask='auto')
    else:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(10 * mm, height - 20 * mm, "Logo nie znalezione")

    # Nagłówek
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 40 * mm, "Potwierdzenie Przyjęcia Depozytu")

    # Informacje o depozycie
    c.setFont("Helvetica", 12)
    c.drawString(10 * mm, height - 60 * mm, f"ID Depozytu: {deposit_id}")
    c.drawString(10 * mm, height - 70 * mm, f"Klient: {client_name}")
    for i, detail in enumerate(deposit_details, start=1):
        c.drawString(10 * mm, height - (80 + i * 10) * mm, detail)

    c.save()
    logger.info(f"Potwierdzenie PDF wygenerowane: {output_path}")
    return output_path




def open_file(self, file_path):
    """Otwiera wygenerowany plik PDF w domyślnej przeglądarce PDF."""
    try:
        if os.path.exists(file_path):
            logger.info(f"Otwieranie pliku PDF: {file_path}")
            if sys.platform == "win32":
                os.startfile(file_path)  # Działa na Windows
            elif sys.platform == "darwin":
                subprocess.run(["open", file_path])
            else:
                subprocess.run(["xdg-open", file_path])
        else:
            logger.error(f"Plik PDF nie istnieje: {file_path}")
            QMessageBox.critical(self, "Błąd", f"Plik PDF nie istnieje: {file_path}")
    except Exception as e:
        logger.error(f"Błąd podczas otwierania pliku PDF: {e}")
        QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas otwierania pliku:\n{e}")






# Otwórz połączenie z bazą danych
conn = create_connection()
cursor = conn.cursor()

try:
    # Pobierz dane przykładowego depozytu z bazy
    cursor.execute("""
        SELECT d.id, c.name, d.tire_brand, d.tire_size, d.quantity
        FROM deposits d
        LEFT JOIN clients c ON d.client_id = c.id
        LIMIT 1
    """)
    deposit = cursor.fetchone()

    if deposit:
        deposit_id, client_name, tire_brand, tire_size, quantity = deposit
        deposit_details = [
            f"Marka Opon: {tire_brand}",
            f"Rozmiar Opon: {tire_size}",
            f"Ilość: {quantity}",
            f"Klient: {client_name}",
        ]
        logo_path = "path/to/logo.png"  # Ścieżka do logo, podmień na rzeczywistą ścieżkę

    else:
        logger.error("Brak danych w tabeli 'deposits'. Upewnij się, że baza danych zawiera rekordy.")

finally:
    conn.close()


class DepositManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Menadżer Depozytów Opon")
        self.setWindowIcon(QIcon("icon.ico"))  # Ścieżka do ikony
        self.setGeometry(100, 100, 1200, 800)
        self.conn = create_connection()
        create_tables(self.conn)

        # Połączenie z bazą danych
        self.conn = create_connection()
        if self.conn is None:
            QMessageBox.critical(self, "Błąd", "Nie można nawiązać połączenia z bazą danych.")
            sys.exit(1)  # Zakończ aplikację, jeśli baza danych nie działa

        # Inicjalizacja atrybutów domyślnych
        self.backup_folder = 'backups'
        self.company_name = ''
        self.company_address = ''
        self.company_contact = ''
        self.company_logo = ''
        self.default_location = ''
        self.auto_print = False
        self.email_settings = {
            'email_address': '',
            'email_password': '',
            'smtp_server': '',
            'smtp_port': 465,
        }

        # Wczytaj ustawienia
        self.load_settings()

        # Główny widget i układ
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)

        # Pole do skanowania kodów kreskowych
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Skanuj kartę stałego klienta.")
        self.barcode_input.returnPressed.connect(self.handle_barcode_scanned)
        self.main_layout.addWidget(self.barcode_input)


        # Pasek menu
        self.menu_bar = self.menuBar()
        self.init_menus()

        # Zakładki
        self.tabs = QTabWidget()
        self.active_tab = QWidget()
        self.issued_tab = QWidget()
        self.overdue_tab = QWidget()
        self.clients_tab = QWidget()
        self.stats_tab = QWidget()
        self.admin_tab = QWidget()
        self.orders_tab = QWidget()  # Nowa zakładka Zamówienia
        self.tabs.addTab(self.active_tab, "Depozyty aktywne")
        self.tabs.addTab(self.issued_tab, "Depozyty wydane")
        self.tabs.addTab(self.overdue_tab, "Depozyty przeterminowane")
        self.tabs.addTab(self.clients_tab, "Klienci")
        self.tabs.addTab(self.orders_tab, "Zamówienia")  # Dodaj zakładkę Zamówienia
        self.tabs.addTab(self.stats_tab, "Statystyki")
        self.tabs.addTab(self.admin_tab, "Administracja")
        self.main_layout.addWidget(self.tabs)

        # Inicjalizacja zakładek
        self.init_active_tab()
        self.init_issued_tab()
        self.init_overdue_tab()
        self.init_clients_tab()
        self.init_orders_tab()  # Inicjalizacja zakładki Zamówienia
        self.init_stats_tab()
        self.init_inventory_tab()

        # Ładowanie danych
        self.load_active_deposits()
        self.load_issued_deposits()
        self.load_overdue_deposits()
        self.load_clients()
        self.load_orders()  # Ładowanie zamówień
        self.load_statistics()

        # Timer do aktualizacji czasu trwania depozytów
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_deposit_durations)
        self.timer.start(60000)  # Aktualizacja co minutę

        # Timer do wysyłania przypomnień
        self.reminder_timer = QTimer()
        self.reminder_timer.timeout.connect(self.check_and_send_reminders)
        self.reminder_timer.start(86400000)  # Sprawdzanie co 24 godziny

        # Ustawienia okna
        self.load_window_settings()

    def init_menus(self):
        # Menu Plik
        file_menu = self.menu_bar.addMenu("Plik")
        export_action = QAction("Eksportuj dane", self)
        export_action.triggered.connect(self.export_data)
        import_action = QAction("Importuj dane", self)
        import_action.triggered.connect(self.import_data)
        exit_action = QAction("Wyjście", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(export_action)
        file_menu.addAction(import_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        # Menu Ustawienia
        settings_menu = self.menu_bar.addMenu("Ustawienia")
        settings_action = QAction("Ustawienia aplikacji", self)
        settings_action.triggered.connect(self.open_settings)
        settings_menu.addAction(settings_action)
        email_settings_action = QAction("Ustawienia e-mail", self)
        email_settings_action.triggered.connect(self.open_email_settings)
        settings_menu.addAction(email_settings_action)
        printer_settings_action = QAction("Ustawienia drukarki", self)
        printer_settings_action.triggered.connect(self.printer_settings)
        settings_menu.addAction(printer_settings_action)
        email_history_action = QAction("Historia wysłanych e-maili", self)
        email_history_action.triggered.connect(self.view_email_history)
        settings_menu.addAction(email_history_action)
        manage_locations_action = QAction("Zarządzaj lokalizacjami", self)
        manage_locations_action.triggered.connect(self.manage_locations)
        settings_menu.addAction(manage_locations_action)
        view_logs_action = QAction("Wyświetl logi", self)
        view_logs_action.triggered.connect(self.view_logs)
        settings_menu.addAction(view_logs_action)

        # Zarządzanie szablonami e-maili
        email_templates_action = QAction("Zarządzaj szablonami e-mail", self)
        email_templates_action.triggered.connect(self.manage_email_templates)
        settings_menu.addAction(email_templates_action)

        # Menu Pomoc
        help_menu = self.menu_bar.addMenu("Pomoc")
        about_action = QAction("O aplikacji", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def init_active_tab(self):
        """Inicjalizuje zakładkę z aktywnymi depozytami."""
        layout = QVBoxLayout()
        self.active_tab.setLayout(layout)

        # Pasek wyszukiwania
        self.search_bar_active = QLineEdit()
        self.search_bar_active.setPlaceholderText("Szukaj depozytów...")
        self.search_bar_active.textChanged.connect(self.load_active_deposits)
        layout.addWidget(self.search_bar_active)

        # Tabela depozytów
        self.table_active = QTableWidget()
        self.table_active.setColumnCount(19)
        self.table_active.setHorizontalHeaderLabels([
            "ID", "Klient", "Telefon", "E-mail", "Model auta", "Nr rejestracyjny", "Marka opon", "Rozmiar opon",
            "Ilość", "Lokalizacja", "Mycie", "Konserwacja", "Data", "Sezon", "Status", "Czas trwania (dni)", "Stan techniczny", "Data przechowywania", "Cena"
        ])
        self.table_active.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_active.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_active.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_active.customContextMenuRequested.connect(self.open_context_menu_active)
        self.table_active.horizontalHeader().setStretchLastSection(True)
        self.table_active.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_active)

        # Przyciski
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Dodaj depozyt")
        self.add_button.clicked.connect(self.add_deposit)
        button_layout.addWidget(self.add_button)
        layout.addLayout(button_layout)

    def init_issued_tab(self):
        """Inicjalizuje zakładkę z wydanymi depozytami."""
        layout = QVBoxLayout()
        self.issued_tab.setLayout(layout)

        # Pasek wyszukiwania
        self.search_bar_issued = QLineEdit()
        self.search_bar_issued.setPlaceholderText("Szukaj depozytów...")
        self.search_bar_issued.textChanged.connect(self.load_issued_deposits)
        layout.addWidget(self.search_bar_issued)

        # Tabela depozytów
        self.table_issued = QTableWidget()
        self.table_issued.setColumnCount(20)
        self.table_issued.setHorizontalHeaderLabels([
            "ID", "Klient", "Telefon", "E-mail", "Model auta", "Nr rejestracyjny", "Marka opon", "Rozmiar opon",
            "Ilość", "Lokalizacja", "Mycie", "Konserwacja", "Data depozytu", "Data wydania", "Sezon", "Status", "Czas trwania (dni)", "Stan techniczny", "Data przechowywania", "Cena"
        ])
        self.table_issued.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_issued.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_issued.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_issued.customContextMenuRequested.connect(self.open_context_menu_issued)
        self.table_issued.horizontalHeader().setStretchLastSection(True)
        self.table_issued.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_issued)

    def init_overdue_tab(self):
        """Inicjalizuje zakładkę z przeterminowanymi depozytami."""
        layout = QVBoxLayout()
        self.overdue_tab.setLayout(layout)

        # Pasek wyszukiwania
        self.search_bar_overdue = QLineEdit()
        self.search_bar_overdue.setPlaceholderText("Szukaj depozytów...")
        self.search_bar_overdue.textChanged.connect(self.load_overdue_deposits)
        layout.addWidget(self.search_bar_overdue)

        # Tabela depozytów
        self.table_overdue = QTableWidget()
        self.table_overdue.setColumnCount(17)
        self.table_overdue.setHorizontalHeaderLabels([
            "ID", "Klient", "Telefon", "E-mail", "Model auta", "Nr rejestracyjny", "Marka opon", "Rozmiar opon",
            "Ilość", "Lokalizacja", "Data", "Oczekiwany zwrot", "Sezon", "Status", "Przeterminowany (dni)", "Kontakt", "Cena"
        ])
        self.table_overdue.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_overdue.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_overdue.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_overdue.customContextMenuRequested.connect(self.open_context_menu_overdue)
        self.table_overdue.horizontalHeader().setStretchLastSection(True)
        self.table_overdue.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_overdue)

    def init_clients_tab(self):
        """Inicjalizuje zakładkę z klientami."""
        layout = QVBoxLayout()
        self.clients_tab.setLayout(layout)

        # Pasek wyszukiwania
        self.search_bar_clients = QLineEdit()
        self.search_bar_clients.setPlaceholderText("Szukaj klientów...")
        self.search_bar_clients.textChanged.connect(self.load_clients)
        layout.addWidget(self.search_bar_clients)

        # Tabela klientów
        self.table_clients = QTableWidget()
        self.table_clients.setColumnCount(7)
        self.table_clients.setHorizontalHeaderLabels([
            "ID", "Nazwa", "Numer telefonu", "E-mail", "Dodatkowe informacje", "Rabat (%)", "Kod kreskowy"
        ])
        self.table_clients.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_clients.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_clients.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_clients.customContextMenuRequested.connect(self.open_context_menu_clients)
        self.table_clients.horizontalHeader().setStretchLastSection(True)
        self.table_clients.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_clients)

        # Przyciski
        button_layout = QHBoxLayout()
        self.add_client_button = QPushButton("Dodaj klienta")
        self.add_client_button.clicked.connect(self.add_client)
        button_layout.addWidget(self.add_client_button)
        layout.addLayout(button_layout)

    def load_orders(self):
        """Ładuje zamówienia z bazy danych i wyświetla je w tabeli."""
        try:
            search_text = self.search_bar_orders.text()
            query = '''
                SELECT orders.id, clients.name, orders.order_date, orders.expected_delivery_date, orders.status, orders.notes
                FROM orders
                INNER JOIN clients ON orders.client_id = clients.id
                WHERE clients.name LIKE ? OR orders.status LIKE ?
                ORDER BY orders.order_date DESC
            '''
            parameters = (f'%{search_text}%', f'%{search_text}%')
            cursor = self.conn.cursor()
            cursor.execute(query, parameters)
            rows = cursor.fetchall()

            self.table_orders.setRowCount(len(rows))
            for row_idx, row in enumerate(rows):
                for col_idx, value in enumerate(row):
                    item = QTableWidgetItem(str(value))
                    self.table_orders.setItem(row_idx, col_idx, item)
        except Exception as e:
            error_code = traceback.format_exc()
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas ładowania zamówień.\nKod błędu:\n{error_code}")
            logger.error(f"Błąd podczas ładowania zamówień: {e}")

    def add_order(self):
        """Otwiera okno dialogowe do dodawania nowego zamówienia."""
        try:
            dialog = OrderDialog(self.conn, parent=self)
            if dialog.exec() == QDialog.Accepted:
                self.load_orders()
        except Exception as e:
            logger.error(f"Błąd podczas dodawania zamówienia: {e}")
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas dodawania zamówienia:\n{traceback.format_exc()}")


    def open_context_menu_orders(self, position):
        """Obsługuje menu kontekstowe dla tabeli zamówień."""
        try:
            menu = QMenu()
            view_action = QAction("Pokaż szczegóły zamówienia", self)
            edit_action = QAction("Edytuj zamówienie", self)
            delete_action = QAction("Usuń zamówienie", self)
            menu.addAction(view_action)
            menu.addAction(edit_action)
            menu.addAction(delete_action)

            action = menu.exec(self.table_orders.viewport().mapToGlobal(position))
            selected_row = self.table_orders.currentRow()
            if selected_row < 0:
                return
            order_id = int(self.table_orders.item(selected_row, 0).text())

            if action == view_action:
                self.view_order_details(order_id)
            elif action == edit_action:
                self.edit_order(order_id)
            elif action == delete_action:
                self.delete_order(order_id)
        except Exception as e:
            error_code = traceback.format_exc()
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas obsługi menu kontekstowego.\nKod błędu:\n{error_code}")
            logger.error(f"Błąd podczas obsługi menu kontekstowego: {e}")

    def view_order_details(self, order_id):
        """Wyświetla szczegóły zamówienia."""
        try:
            dialog = OrderDetailsDialog(self.conn, order_id, parent=self)
            dialog.exec()
        except Exception as e:
            logger.error(f"Błąd podczas wyświetlania szczegółów zamówienia: {e}")

    def edit_order(self, order_id):
        """Edytuje istniejące zamówienie."""
        try:
            dialog = OrderDialog(self.conn, order_id=order_id, parent=self)
            if dialog.exec() == QDialog.Accepted:
                self.load_orders()
        except Exception as e:
            logger.error(f"Błąd podczas edycji zamówienia: {e}")

    def delete_order(self, order_id):
        """Usuwa zamówienie."""
        try:
            reply = QMessageBox.question(
                self, "Usuń zamówienie",
                "Czy na pewno chcesz usunąć to zamówienie?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
                cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
                self.conn.commit()
                self.load_orders()
        except Exception as e:
            logger.error(f"Błąd podczas usuwania zamówienia: {e}")

    def init_orders_tab(self):
        """Inicjalizuje zakładkę z zamówieniami."""
        layout = QVBoxLayout()
        self.orders_tab.setLayout(layout)

        # Pasek wyszukiwania
        self.search_bar_orders = QLineEdit()
        self.search_bar_orders.setPlaceholderText("Szukaj zamówień...")
        self.search_bar_orders.textChanged.connect(self.load_orders)
        layout.addWidget(self.search_bar_orders)

        # Tabela zamówień
        self.table_orders = QTableWidget()
        self.table_orders.setColumnCount(6)
        self.table_orders.setHorizontalHeaderLabels([
            "ID", "Klient", "Data zamówienia", "Oczekiwana dostawa", "Status", "Uwagi"
        ])
        self.table_orders.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_orders.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_orders.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_orders.customContextMenuRequested.connect(self.open_context_menu_orders)
        self.table_orders.horizontalHeader().setStretchLastSection(True)
        self.table_orders.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_orders)

        # Przyciski
        button_layout = QHBoxLayout()
        self.add_order_button = QPushButton("Dodaj zamówienie")
        self.add_order_button.clicked.connect(self.add_order)
        button_layout.addWidget(self.add_order_button)
        layout.addLayout(button_layout)

    def manage_email_templates(self):
        """Otwiera okno dialogowe do zarządzania szablonami e-mail."""
        dialog = EmailTemplateManagerDialog(self.conn, parent=self)
        dialog.exec()

    def init_stats_tab(self):
        """Inicjalizuje zakładkę ze statystykami."""
        layout = QVBoxLayout()
        self.stats_tab.setLayout(layout)

        self.stats_label = QLabel("Statystyki")
        self.stats_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.stats_label)

        self.stats_image = QLabel()
        self.stats_image.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.stats_image)

    def init_inventory_tab(self):
        """Inicjalizuje zakładkę Opony na stanie."""
        layout = QVBoxLayout()
        self.inventory_tab = QWidget()
        self.inventory_tab.setLayout(layout)

        # Pasek wyszukiwania
        self.search_bar_inventory = QLineEdit()
        self.search_bar_inventory.setPlaceholderText("Szukaj opon na stanie...")
        self.search_bar_inventory.textChanged.connect(self.load_inventory)
        layout.addWidget(self.search_bar_inventory)

        # Tabela opon
        self.table_inventory = QTableWidget()
        self.table_inventory.setColumnCount(6)
        self.table_inventory.setHorizontalHeaderLabels([
           "ID","Marka i model", "Rozmiar", "Ilość", "DOT", "Cena"
        ])
        self.table_inventory.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_inventory.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_inventory.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_inventory.customContextMenuRequested.connect(self.open_context_menu_inventory)
        self.table_inventory.horizontalHeader().setStretchLastSection(True)
        self.table_inventory.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_inventory)

        # Przyciski
        button_layout = QHBoxLayout()
        self.add_inventory_button = QPushButton("Dodaj oponę")
        self.add_inventory_button.clicked.connect(self.add_inventory_item)
        button_layout.addWidget(self.add_inventory_button)
        layout.addLayout(button_layout)

        # Zastąp zakładkę Administracja nową zakładką
        self.tabs.removeTab(self.tabs.indexOf(self.admin_tab))
        self.tabs.addTab(self.inventory_tab, "Opony na stanie")

        # Ładowanie danych przy starcie zakładki
        self.load_inventory()

    def add_inventory_item(self):
        """Dodaje nową oponę do stanu magazynowego."""
        dialog = InventoryItemDialog(self.conn, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.load_inventory()


    def load_inventory(self):
        """Ładuje dane o oponach na stanie do tabeli w zakładce 'Opony na stanie'."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT id, brand_model, size, quantity, price, dot
                FROM inventory
            ''')
            rows = cursor.fetchall()

            self.table_inventory.setRowCount(0)  # Wyczyszczenie tabeli przed załadowaniem nowych danych

            for row_idx, row_data in enumerate(rows):
                self.table_inventory.insertRow(row_idx)

                # Wstawiamy dane w odpowiedniej kolejności
                self.table_inventory.setItem(row_idx, 0, QTableWidgetItem(str(row_data[0])))  # ID
                self.table_inventory.setItem(row_idx, 1, QTableWidgetItem(row_data[1]))       # Marka i model
                self.table_inventory.setItem(row_idx, 2, QTableWidgetItem(row_data[2]))       # Rozmiar
                self.table_inventory.setItem(row_idx, 5, QTableWidgetItem(str(row_data[4])))  # Cena
                self.table_inventory.setItem(row_idx, 4, QTableWidgetItem(row_data[5]))       # DOT
                self.table_inventory.setItem(row_idx, 3, QTableWidgetItem(str(row_data[3])))  # Ilość

            logger.info("Dane opon na stanie zostały załadowane.")
        except Exception as e:
            logger.error(f"Błąd podczas ładowania danych opon na stanie: {e}")
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas ładowania danych:\n{e}")




    def open_context_menu_inventory(self, position):
        """Otwiera menu kontekstowe dla tabeli 'Opony na stanie'."""
        selected_row = self.table_inventory.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Brak zaznaczenia", "Nie zaznaczono żadnej pozycji.")
            return

        # Pobranie ID opony z tabeli (zakładamy, że ID jest w pierwszej kolumnie)
        tire_id_item = self.table_inventory.item(selected_row, 0)
        if tire_id_item and tire_id_item.text().isdigit():
            tire_id = int(tire_id_item.text())  # Przekształcenie ID na liczbę
        else:
            QMessageBox.warning(self, "Błąd", "Nie udało się pobrać ID opony.")
            return

        menu = QMenu(self)

        # Akcje menu kontekstowego
        add_action = QAction("Dodaj oponę", self)
        add_action.triggered.connect(self.add_inventory_item)
        menu.addAction(add_action)

        edit_action = QAction("Edytuj oponę", self)
        edit_action.triggered.connect(lambda: self.edit_inventory_item(tire_id))
        menu.addAction(edit_action)

        delete_action = QAction("Usuń oponę", self)
        delete_action.triggered.connect(lambda: self.delete_inventory_item(tire_id))
        menu.addAction(delete_action)

        print_action = QAction("Drukuj etykietę", self)
        print_action.triggered.connect(lambda: self.print_inventory_item_label(tire_id))
        menu.addAction(print_action)

        # Wyświetlenie menu kontekstowego
        menu.exec(self.table_inventory.viewport().mapToGlobal(position))




    def edit_inventory_item(self, tire_id):
        """Edytuje wybraną oponę."""
        dialog = InventoryItemDialog(self.conn, tire_id, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.load_inventory()
            QMessageBox.information(self, "Sukces", "Opona została zaktualizowana.")



    def delete_inventory_item(self, tire_id):
        """Usuwa wybraną oponę."""
        confirm = QMessageBox.question(self, "Potwierdzenie", "Czy na pewno chcesz usunąć tę oponę?",
                                        QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            try:
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM inventory WHERE id = ?", (tire_id,))
                self.conn.commit()
                self.load_inventory()
                QMessageBox.information(self, "Sukces", "Opona została usunięta.")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Błąd", f"Błąd bazy danych: {e}")



    def print_inventory_item_label(self, tire_id):
        """Drukuje etykietę dla wybranej opony."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT brand_model, size, quantity, price, dot
            FROM inventory WHERE id = ?
        ''', (tire_id,))
        item = cursor.fetchone()

        if item:
            brand_model, size, quantity, price, dot = item
            label_content = f"Marka i model: {brand_model}\nRozmiar: {size}\nIlość: {quantity}\nCena: {price:.2f}\nDOT: {dot}"

            # Drukowanie (prosty przykład)
            QMessageBox.information(self, "Drukowanie", f"Drukowanie etykiety:\n\n{label_content}")
        else:
            QMessageBox.warning(self, "Błąd", "Nie znaleziono opony w bazie danych.")




    def open_email_settings(self):
        """Otwiera okno ustawień e-mail."""
        dialog = EmailSettingsDialog(self)
        if dialog.exec():
            QMessageBox.information(self, "Ustawienia e-mail", "Ustawienia e-mail zostały zapisane.")

    def view_email_history(self):
        """Wyświetla historię wysłanych e-maili."""
        dialog = EmailHistoryDialog(self.conn, self)
        dialog.exec()

    def printer_settings(self):
        """Otwiera okno ustawień drukarki."""
        dialog = PrinterSettingsDialog(self)
        if dialog.exec():
            QMessageBox.information(self, "Ustawienia drukarki", "Ustawienia drukarki zostały zapisane.")

    def manage_locations(self):
        """Otwiera okno zarządzania lokalizacjami."""
        dialog = LocationManagerDialog(self)
        if dialog.exec():
            self.load_locations()

    def load_active_deposits(self):
        """Ładuje aktywne depozyty z bazy danych i wyświetla je w tabeli."""
        try:
            search_text = self.search_bar_active.text()
            query = '''
                SELECT deposits.id, clients.name, clients.phone_number, clients.email,
                       deposits.car_model, deposits.registration_number,
                       deposits.tire_brand, deposits.tire_size, deposits.quantity, deposits.location,
                       deposits.washing, deposits.conservation, deposits.deposit_date,
                       deposits.season, deposits.status, deposits.duration,
                       deposits.technical_condition, deposits.storage_date, deposits.price
                FROM deposits
                INNER JOIN clients ON deposits.client_id = clients.id
                WHERE (clients.name LIKE ? OR deposits.registration_number LIKE ?)
                  AND deposits.status = 'Aktywny'
                ORDER BY deposits.deposit_date DESC
            '''
            parameters = (f'%{search_text}%', f'%{search_text}%')
            cursor = self.conn.cursor()
            cursor.execute(query, parameters)
            rows = cursor.fetchall()

            self.table_active.setRowCount(len(rows))
            for row_idx, row in enumerate(rows):
                for col_idx, value in enumerate(row):
                    if col_idx == 10 or col_idx == 11:  # Kolumny Mycie i Konserwacja
                        value = "Tak" if value else "Nie"
                    if col_idx == 15:  # Czas trwania
                        value = str(int(value)) if value else "0"
                    item = QTableWidgetItem(str(value))
                    self.table_active.setItem(row_idx, col_idx, item)
                    if col_idx == 14:  # Status
                        if value == "Aktywny":
                            item.setBackground(QColor("lightgreen"))
                        else:
                            item.setBackground(QColor("lightgray"))
        except Exception as e:
            error_code = traceback.format_exc()
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas ładowania aktywnych depozytów.\nKod błędu:\n{error_code}")
            logger.error(f"Błąd podczas ładowania aktywnych depozytów: {e}")

    def load_issued_deposits(self):
        """Ładuje wydane depozyty z bazy danych i wyświetla je w tabeli."""
        try:
            search_text = self.search_bar_issued.text()
            query = '''
                SELECT deposits.id, clients.name, clients.phone_number, clients.email,
                       deposits.car_model, deposits.registration_number,
                       deposits.tire_brand, deposits.tire_size, deposits.quantity, deposits.location,
                       deposits.washing, deposits.conservation, deposits.deposit_date,
                       deposits.issue_date, deposits.season, deposits.status, deposits.duration,
                       deposits.technical_condition, deposits.storage_date, deposits.price
                FROM deposits
                INNER JOIN clients ON deposits.client_id = clients.id
                WHERE (clients.name LIKE ? OR deposits.registration_number LIKE ?)
                  AND deposits.status = 'Wydany'
                ORDER BY deposits.issue_date DESC
            '''
            parameters = (f'%{search_text}%', f'%{search_text}%')
            cursor = self.conn.cursor()
            cursor.execute(query, parameters)
            rows = cursor.fetchall()

            self.table_issued.setRowCount(len(rows))
            for row_idx, row in enumerate(rows):
                for col_idx, value in enumerate(row):
                    if col_idx == 10 or col_idx == 11:  # Kolumny Mycie i Konserwacja
                        value = "Tak" if value else "Nie"
                    if col_idx == 16:  # Czas trwania
                        value = str(int(value)) if value else "0"
                    item = QTableWidgetItem(str(value))
                    self.table_issued.setItem(row_idx, col_idx, item)
                    if col_idx == 15:  # Status
                        if value == "Wydany":
                            item.setBackground(QColor("lightgray"))
        except Exception as e:
            error_code = traceback.format_exc()
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas ładowania wydanych depozytów.\nKod błędu:\n{error_code}")
            logger.error(f"Błąd podczas ładowania wydanych depozytów: {e}")

    def load_overdue_deposits(self):
        """Ładuje przeterminowane depozyty i wyświetla je w tabeli."""
        try:
            search_text = self.search_bar_overdue.text()
            query = '''
                SELECT deposits.id, clients.name, clients.phone_number, clients.email,
                       deposits.car_model, deposits.registration_number,
                       deposits.tire_brand, deposits.tire_size, deposits.quantity, deposits.location,
                       deposits.deposit_date, deposits.expected_return_date, deposits.season, deposits.status,
                       ROUND(julianday(DATE('now')) - julianday(deposits.expected_return_date)) as overdue_days,
                       clients.phone_number, deposits.price
                FROM deposits
                INNER JOIN clients ON deposits.client_id = clients.id
                WHERE (clients.name LIKE ? OR deposits.registration_number LIKE ?)
                  AND deposits.status = 'Aktywny' AND deposits.expected_return_date < DATE('now')
                ORDER BY deposits.expected_return_date ASC
            '''
            parameters = (f'%{search_text}%', f'%{search_text}%')
            cursor = self.conn.cursor()
            cursor.execute(query, parameters)
            rows = cursor.fetchall()

            self.table_overdue.setRowCount(len(rows))
            for row_idx, row in enumerate(rows):
                for col_idx, value in enumerate(row):
                    if col_idx == 14:  # Przeterminowany (dni)
                        value = str(int(value)) if value else "0"
                    item = QTableWidgetItem(str(value))
                    self.table_overdue.setItem(row_idx, col_idx, item)
        except Exception as e:
            error_code = traceback.format_exc()
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas ładowania przeterminowanych depozytów.\nKod błędu:\n{error_code}")
            logger.error(f"Błąd podczas ładowania przeterminowanych depozytów: {e}")

    def load_clients(self):
        """Ładuje listę klientów i wyświetla w tabeli."""
        try:
            search_text = self.search_bar_clients.text()
            query = '''
                SELECT id, name, phone_number, email, additional_info, discount, barcode
                FROM clients
                WHERE name LIKE ?
                ORDER BY name ASC
            '''
            parameters = (f'%{search_text}%',)
            cursor = self.conn.cursor()
            cursor.execute(query, parameters)
            rows = cursor.fetchall()

            self.table_clients.setRowCount(len(rows))
            for row_idx, row in enumerate(rows):
                for col_idx, value in enumerate(row):
                    item = QTableWidgetItem(str(value))
                    self.table_clients.setItem(row_idx, col_idx, item)
        except Exception as e:
            error_code = traceback.format_exc()
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas ładowania klientów.\nKod błędu:\n{error_code}")
            logger.error(f"Błąd podczas ładowania klientów: {e}")

    def add_deposit(self):
        """Otwiera okno dialogowe do dodawania nowego depozytu."""
        try:
            dialog = DepositDialog(self.conn, default_location=self.default_location, parent=self)
            if dialog.exec() == QDialog.Accepted:
                self.load_clients()  # Odśwież listę klientów
                self.load_active_deposits()
                self.load_overdue_deposits()
        except Exception as e:
            logger.error(f"Błąd podczas dodawania depozytu: {e}")
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas dodawania depozytu:\n{traceback.format_exc()}")


    def add_client(self):
        """Otwiera okno dialogowe do dodawania nowego klienta."""
        try:
            dialog = AddClientDialog(self.conn, parent=self)
            if dialog.exec() == QDialog.Accepted:
                self.load_clients()
        except Exception as e:
            error_code = traceback.format_exc()
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas dodawania klienta.\nKod błędu:\n{error_code}")
            logger.error(f"Błąd podczas dodawania klienta: {e}")

    def open_context_menu_active(self, position):
        """Obsługuje menu kontekstowe dla tabeli aktywnych depozytów."""
        try:
            menu = QMenu()
            edit_action = QAction("Edytuj depozyt", self)
            delete_action = QAction("Usuń depozyt", self)
            issue_action = QAction("Oznacz jako wydany", self)
            generate_label_action = QAction("Generuj etykietę", self)
            print_confirmation_action = QAction("Drukuj potwierdzenie", self)
            view_details_action = QAction("Pokaż szczegóły", self)
            send_email_action = QAction("Wyślij e-mail", self)
            menu.addAction(edit_action)
            menu.addAction(issue_action)
            menu.addAction(generate_label_action)
            menu.addAction(print_confirmation_action)
            menu.addAction(view_details_action)
            menu.addAction(send_email_action)
            menu.addAction(delete_action)

            action = menu.exec(self.table_active.viewport().mapToGlobal(position))
            selected_row = self.table_active.currentRow()
            if selected_row < 0:
                return
            deposit_id = int(self.table_active.item(selected_row, 0).text())

            if action == edit_action:
                self.edit_deposit(deposit_id)
            elif action == delete_action:
                self.delete_deposit(deposit_id)
            elif action == issue_action:
                self.mark_as_issued(deposit_id)
            elif action == generate_label_action:
                self.generate_label(deposit_id)
            elif action == print_confirmation_action:
                self.print_confirmation(deposit_id)
            elif action == view_details_action:
                self.view_deposit_details(deposit_id)
            elif action == send_email_action:
                self.send_email_to_client(deposit_id)

        except Exception as e:
            error_code = traceback.format_exc()
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas obsługi menu kontekstowego.\nKod błędu:\n{error_code}")
            logger.error(f"Błąd podczas obsługi menu kontekstowego: {e}")

    def open_context_menu_issued(self, position):
        """Obsługuje menu kontekstowe dla tabeli wydanych depozytów."""
        try:
            menu = QMenu()
            edit_action = QAction("Edytuj depozyt", self)
            delete_action = QAction("Usuń depozyt", self)
            mark_active_action = QAction("Oznacz jako aktywny", self)
            generate_label_action = QAction("Generuj etykietę", self)
            view_details_action = QAction("Pokaż szczegóły", self)
            menu.addAction(edit_action)
            menu.addAction(mark_active_action)
            menu.addAction(generate_label_action)
            menu.addAction(view_details_action)
            menu.addAction(delete_action)

            action = menu.exec(self.table_issued.viewport().mapToGlobal(position))
            selected_row = self.table_issued.currentRow()
            if selected_row < 0:
                return
            deposit_id = int(self.table_issued.item(selected_row, 0).text())

            if action == edit_action:
                self.edit_deposit(deposit_id)
            elif action == delete_action:
                self.delete_deposit(deposit_id)
            elif action == mark_active_action:
                self.mark_as_active(deposit_id)
            elif action == generate_label_action:
                self.generate_label(deposit_id)
            elif action == view_details_action:
                self.view_deposit_details(deposit_id)
        except Exception as e:
            error_code = traceback.format_exc()
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas obsługi menu kontekstowego.\nKod błędu:\n{error_code}")
            logger.error(f"Błąd podczas obsługi menu kontekstowego: {e}")

    def open_context_menu_overdue(self, position):
        """Obsługuje menu kontekstowe dla tabeli przeterminowanych depozytów."""
        try:
            menu = QMenu()
            contact_action = QAction("Skontaktuj się z klientem", self)
            view_details_action = QAction("Pokaż szczegóły", self)
            delete_action = QAction("Usuń depozyt", self)
            menu.addAction(contact_action)
            menu.addAction(view_details_action)
            menu.addAction(delete_action)

            action = menu.exec(self.table_overdue.viewport().mapToGlobal(position))
            selected_row = self.table_overdue.currentRow()
            if selected_row < 0:
                return
            deposit_id = int(self.table_overdue.item(selected_row, 0).text())

            if action == contact_action:
                self.contact_client(deposit_id)
            elif action == delete_action:
                self.delete_deposit(deposit_id)
            elif action == view_details_action:
                self.view_deposit_details(deposit_id)
        except Exception as e:
            error_code = traceback.format_exc()
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas obsługi menu kontekstowego.\nKod błędu:\n{error_code}")
            logger.error(f"Błąd podczas obsługi menu kontekstowego: {e}")

    def open_context_menu_clients(self, position):
        """Obsługuje menu kontekstowe dla tabeli klientów."""
        try:
            menu = QMenu()
            view_deposits_action = QAction("Pokaż depozyty klienta", self)
            edit_client_action = QAction("Edytuj klienta", self)
            delete_client_action = QAction("Usuń klienta", self)
            assign_barcode_action = QAction("Przypisz kod kreskowy", self)
            send_email_action = QAction("Wyślij e-mail", self)
            menu.addAction(view_deposits_action)
            menu.addAction(edit_client_action)
            menu.addAction(assign_barcode_action)
            menu.addAction(send_email_action)
            menu.addAction(delete_client_action)

            action = menu.exec(self.table_clients.viewport().mapToGlobal(position))
            selected_row = self.table_clients.currentRow()
            if selected_row < 0:
                return
            client_id = int(self.table_clients.item(selected_row, 0).text())

            if action == view_deposits_action:
                self.view_client_deposits(client_id)
            elif action == edit_client_action:
                self.edit_client(client_id)
            elif action == delete_client_action:
                self.delete_client(client_id)
            elif action == assign_barcode_action:
                self.assign_barcode_to_client(client_id)
            elif action == send_email_action:
                self.send_email_to_client(deposit_id)
        except Exception as e:
            error_code = traceback.format_exc()
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas obsługi menu kontekstowego.\nKod błędu:\n{error_code}")
            logger.error(f"Błąd podczas obsługi menu kontekstowego: {e}")

    def assign_barcode_to_client(self, client_id):
        """Przypisuje kod kreskowy do klienta."""
        text, ok = QInputDialog.getText(self, "Przypisz kod kreskowy", "Wprowadź kod kreskowy:")
        if ok and text:
            try:
                cursor = self.conn.cursor()
                cursor.execute("UPDATE clients SET barcode = ? WHERE id = ?", (text, client_id))
                self.conn.commit()
                self.load_clients()
                QMessageBox.information(self, "Sukces", "Kod kreskowy został przypisany do klienta.")
            except Exception as e:
                error_code = traceback.format_exc()
                QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas przypisywania kodu kreskowego.\nKod błędu:\n{error_code}")
                logger.error(f"Błąd podczas przypisywania kodu kreskowego: {e}")

    def view_client_deposits(self, client_id):
        """Wyświetla depozyty powiązane z wybranym klientem."""
        try:
            dialog = ClientDepositsDialog(self.conn, client_id, parent=self)
            dialog.exec()
        except Exception as e:
            error_code = traceback.format_exc()
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas wyświetlania depozytów klienta.\nKod błędu:\n{error_code}")
            logger.error(f"Błąd podczas wyświetlania depozytów klienta: {e}")

    def edit_client(self, client_id):
        """Edytuje informacje o kliencie."""
        try:
            dialog = EditClientDialog(self.conn, client_id, parent=self)
            if dialog.exec() == QDialog.Accepted:
                self.load_clients()
        except Exception as e:
            error_code = traceback.format_exc()
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas edycji klienta.\nKod błędu:\n{error_code}")
            logger.error(f"Błąd podczas edycji klienta: {e}")

    def delete_client(self, client_id):
        """Usuwa klienta z bazy danych."""
        try:
            reply = QMessageBox.question(
                self, "Usuń klienta",
                "Czy na pewno chcesz usunąć tego klienta? Spowoduje to również usunięcie wszystkich jego depozytów.",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM deposits WHERE client_id = ?", (client_id,))
                cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
                self.conn.commit()
                self.load_clients()
                self.load_active_deposits()
                self.load_issued_deposits()
                self.load_overdue_deposits()
                self.load_statistics()
        except Exception as e:
            error_code = traceback.format_exc()
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas usuwania klienta.\nKod błędu:\n{error_code}")
            logger.error(f"Błąd podczas usuwania klienta: {e}")

    def edit_deposit(self, deposit_id):
        """Edytuje istniejący depozyt."""
        try:
            dialog = DepositDialog(self.conn, deposit_id, default_location=self.default_location, parent=self)
            if dialog.exec() == QDialog.Accepted:
                self.load_active_deposits()
                self.load_issued_deposits()
                self.load_overdue_deposits()
                self.load_statistics()
        except Exception as e:
            error_code = traceback.format_exc()
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas edycji depozytu.\nKod błędu:\n{error_code}")
            logger.error(f"Błąd podczas edycji depozytu: {e}")

    def delete_deposit(self, deposit_id):
        """Usuwa depozyt z bazy danych."""
        try:
            reply = QMessageBox.question(
                self, "Usuń depozyt",
                "Czy na pewno chcesz usunąć ten depozyt?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM deposits WHERE id = ?", (deposit_id,))
                self.conn.commit()
                self.record_history(deposit_id, "Usunięto depozyt")
                self.load_active_deposits()
                self.load_issued_deposits()
                self.load_overdue_deposits()
                self.load_statistics()
        except Exception as e:
            error_code = traceback.format_exc()
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas usuwania depozytu.\nKod błędu:\n{error_code}")
            logger.error(f"Błąd podczas usuwania depozytu: {e}")

    def generate_label(self, deposit_id):
        """Generuje etykietę PDF z opcją drukowania, otwierania lub anulowania."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT deposits.id, clients.name, deposits.tire_brand, deposits.tire_size, deposits.quantity
                FROM deposits
                INNER JOIN clients ON deposits.client_id = clients.id
                WHERE deposits.id = ?
            ''', (deposit_id,))
            result = cursor.fetchone()

            if result:
                deposit_id, client_name, tire_brand, tire_size, quantity = result
                logo_path = get_file_path("logo.png")
                output_path = generate_pdf_label(deposit_id, client_name, tire_brand, tire_size, quantity, logo_path)

                message_box = QMessageBox(self)
                message_box.setWindowTitle("Etykieta wygenerowana")
                message_box.setText(f"Etykieta została wygenerowana: {output_path}\n\nCo chcesz zrobić?")
                open_button = message_box.addButton("Otwórz", QMessageBox.ActionRole)
                print_button = message_box.addButton("Drukuj", QMessageBox.ActionRole)
                cancel_button = message_box.addButton("Nie", QMessageBox.RejectRole)

                message_box.exec()

                if message_box.clickedButton() == open_button:
                    self.open_file(output_path)
                elif message_box.clickedButton() == print_button:
                    self.print_file(output_path)
            else:
                QMessageBox.warning(self, "Błąd", "Nie znaleziono danych dla tego depozytu.")
        except Exception as e:
            logger.error(f"Błąd podczas generowania etykiety: {e}")
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas generowania etykiety:\n{e}")




    def print_label(self, file_path):
        """Drukuje etykietę na drukarce Niimbot B1."""
        try:
            printer_name = self.label_printer  # Pobierz ustawioną drukarkę Niimbot
            if not printer_name:
                QMessageBox.warning(self, "Błąd", "Drukarka Niimbot B1 nie jest ustawiona w ustawieniach.")
                return

            # Komenda drukowania – możesz dostosować dla Niimbot B1
            # Użyj subprocess do wysłania pliku na drukarkę
            subprocess.run(["lp", "-d", printer_name, file_path], check=True)

            QMessageBox.information(self, "Sukces", "Etykieta została wydrukowana.")
        except Exception as e:
            logger.error(f"Błąd podczas drukowania etykiety: {e}")
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas drukowania etykiety:\n{e}")

    def open_file(self, file_path):
        """Otwiera wygenerowany plik PDF w domyślnej przeglądarce PDF."""
        try:
            if os.path.exists(file_path):
                logger.info(f"Otwieranie pliku PDF: {file_path}")
                if sys.platform == "win32":
                    os.startfile(file_path)  # Działa na Windows
                elif sys.platform == "darwin":
                    subprocess.run(["open", file_path])
                else:
                    subprocess.run(["xdg-open", file_path])
            else:
                logger.error(f"Plik PDF nie istnieje: {file_path}")
                QMessageBox.critical(self, "Błąd", f"Plik PDF nie istnieje: {file_path}")
        except Exception as e:
            logger.error(f"Błąd podczas otwierania pliku PDF: {e}")
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas otwierania pliku:\n{e}")


    def print_confirmation(self, deposit_id):
        """Generuje potwierdzenie PDF z opcją drukowania, otwierania lub anulowania."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT deposits.id, clients.name, deposits.car_model, deposits.registration_number,
                    deposits.tire_brand, deposits.tire_size, deposits.quantity, deposits.deposit_date
                FROM deposits
                INNER JOIN clients ON deposits.client_id = clients.id
                WHERE deposits.id = ?
            ''', (deposit_id,))
            result = cursor.fetchone()

            if result:
                deposit_id, client_name, car_model, registration_number, tire_brand, tire_size, quantity, deposit_date = result
                logo_path = get_file_path("logo.png")
                output_path = generate_pdf_confirmation(
                    deposit_id,
                    client_name,
                    [
                        f"Model Auta: {car_model}",
                        f"Nr Rejestracyjny: {registration_number}",
                        f"Marka Opon: {tire_brand}",
                        f"Rozmiar Opon: {tire_size}",
                        f"Ilość: {quantity}",
                        f"Data Przyjęcia: {deposit_date}",
                    ],
                    logo_path
                )

                message_box = QMessageBox(self)
                message_box.setWindowTitle("Potwierdzenie wygenerowane")
                message_box.setText(f"Potwierdzenie zostało wygenerowane: {output_path}\n\nCo chcesz zrobić?")
                open_button = message_box.addButton("Otwórz", QMessageBox.ActionRole)
                print_button = message_box.addButton("Drukuj", QMessageBox.ActionRole)
                cancel_button = message_box.addButton("Nie", QMessageBox.RejectRole)

                message_box.exec()

                if message_box.clickedButton() == open_button:
                    self.open_file(output_path)
                elif message_box.clickedButton() == print_button:
                    self.print_file(output_path)
            else:
                QMessageBox.warning(self, "Błąd", "Nie znaleziono danych dla tego depozytu.")
        except Exception as e:
            logger.error(f"Błąd podczas drukowania potwierdzenia: {e}")
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas drukowania potwierdzenia:\n{e}")


    def print_file(self, file_path):
        """Drukuje plik PDF za pomocą domyślnej drukarki."""
        try:
            logger.info(f"Drukowanie pliku: {file_path}")
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Plik nie istnieje: {file_path}")

            # Wykorzystaj Windows API do drukowania
            win32api.ShellExecute(0, "print", file_path, None, ".", 0)
            logger.info(f"Plik {file_path} został wysłany do drukarki.")
        except Exception as e:
            logger.error(f"Błąd podczas drukowania pliku: {e}")
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas drukowania pliku:\n{e}")



    def print_confirmation_file(self, file_path):
        """Drukuje potwierdzenie na domyślnej drukarce."""
        try:
            printer_name = self.default_printer  # Pobierz domyślną drukarkę z ustawień
            if not printer_name:
                QMessageBox.warning(self, "Błąd", "Domyślna drukarka nie jest ustawiona w ustawieniach.")
                return

            # Komenda drukowania
            subprocess.run(["lp", "-d", printer_name, file_path], check=True)

            QMessageBox.information(self, "Sukces", "Potwierdzenie zostało wydrukowane.")
        except Exception as e:
            logger.error(f"Błąd podczas drukowania potwierdzenia: {e}")
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas drukowania potwierdzenia:\n{e}")

    def export_data(self):
        """Eksportuje dane do pliku CSV."""
        try:
            file_path, _ = QFileDialog.getSaveFileName(self, "Eksportuj dane", "", "CSV Files (*.csv)")
            if file_path:
                cursor = self.conn.cursor()
                cursor.execute('''
                    SELECT deposits.id, clients.name, clients.phone_number, clients.email,
                           deposits.car_model, deposits.registration_number,
                           deposits.tire_brand, deposits.tire_size, deposits.quantity, deposits.location,
                           deposits.washing, deposits.conservation, deposits.deposit_date,
                           deposits.status, deposits.duration, deposits.technical_condition,
                           deposits.storage_date, deposits.price
                    FROM deposits
                    INNER JOIN clients ON deposits.client_id = clients.id
                ''')
                rows = cursor.fetchall()
                import csv
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        "ID", "Klient", "Telefon", "E-mail", "Model auta", "Nr rejestracyjny", "Marka opon", "Rozmiar opon",
                        "Ilość", "Lokalizacja", "Mycie",
                        "Konserwacja", "Data depozytu", "Status", "Czas trwania (dni)", "Stan techniczny",
                        "Data przechowywania", "Cena"
                    ])
                    for row in rows:
                        writer.writerow(row)
                    QMessageBox.information(self, "Eksport zakończony", f"Dane zostały wyeksportowane do {file_path}")
        except Exception as e:
            error_code = traceback.format_exc()
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas eksportu danych.\nKod błędu:\n{error_code}")
            logger.error(f"Błąd podczas eksportu danych: {e}")

    def import_data(self):
        """Importuje dane z pliku CSV."""
        try:
            file_path, _ = QFileDialog.getOpenFileName(self, "Importuj dane", "", "CSV Files (*.csv)")
            if file_path:
                import csv
                with open(file_path, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    cursor = self.conn.cursor()
                    for row in reader:
                        # Wstaw lub zaktualizuj klienta
                        cursor.execute("SELECT id FROM clients WHERE name = ?", (row['Klient'],))
                        client = cursor.fetchone()
                        if client:
                            client_id = client[0]
                        else:
                            cursor.execute("INSERT INTO clients (name, phone_number, email) VALUES (?, ?, ?)", (row['Klient'], row['Telefon'], row['E-mail']))
                            client_id = cursor.lastrowid
                        # Wstaw depozyt
                        cursor.execute('''
                            INSERT INTO deposits (
                                client_id, car_model, registration_number, tire_brand, tire_size,
                                quantity, location, washing, conservation, deposit_date, status,
                                technical_condition, storage_date, price
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            client_id, row['Model auta'], row['Nr rejestracyjny'], row['Marka opon'], row['Rozmiar opon'],
                            row['Ilość'], row['Lokalizacja'], row['Mycie'] == 'Tak',
                            row['Konserwacja'] == 'Tak', row['Data depozytu'], row['Status'],
                            row['Stan techniczny'], row['Data przechowywania'], row['Cena']
                        ))
                    self.conn.commit()
                QMessageBox.information(self, "Import zakończony", f"Dane zostały zaimportowane z {file_path}")
                self.load_active_deposits()
                self.load_issued_deposits()
                self.load_overdue_deposits()
                self.load_clients()
                self.load_statistics()
        except Exception as e:
            error_code = traceback.format_exc()
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas importu danych.\nKod błędu:\n{error_code}")
            logger.error(f"Błąd podczas importu danych: {e}")

    def show_about(self):
        """Wyświetla informacje o aplikacji."""
        QMessageBox.information(
            self, "O aplikacji",
            "Menadżer Depozytów Opon\nWersja 1.0.0\nStworzony w Pythonie z użyciem PySide6.\nSerwis Opon MATEO z pomocą ChatGPT."
        )

    def mark_as_issued(self, deposit_id):
        """Oznacza depozyt jako wydany."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE deposits
                SET status = 'Wydany', issue_date = ?
                WHERE id = ?
            ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), deposit_id))
            self.conn.commit()
            self.record_history(deposit_id, "Oznaczono jako wydany")
            self.load_active_deposits()
            self.load_issued_deposits()
            self.load_overdue_deposits()
            self.load_statistics()
        except Exception as e:
            error_code = traceback.format_exc()
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas oznaczania depozytu jako wydany.\nKod błędu:\n{error_code}")
            logger.error(f"Błąd podczas oznaczania depozytu jako wydany: {e}")

    def mark_as_active(self, deposit_id):
        """Oznacza depozyt jako aktywny."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE deposits
                SET status = 'Aktywny', issue_date = NULL
                WHERE id = ?
            ''', (deposit_id,))
            self.conn.commit()
            self.record_history(deposit_id, "Oznaczono jako aktywny")
            self.load_active_deposits()
            self.load_issued_deposits()
            self.load_overdue_deposits()
            self.load_statistics()
        except Exception as e:
            error_code = traceback.format_exc()
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas oznaczania depozytu jako aktywny.\nKod błędu:\n{error_code}")
            logger.error(f"Błąd podczas oznaczania depozytu jako aktywny: {e}")

    def record_history(self, deposit_id, description):
        """Rejestruje zmianę w historii."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO history (deposit_id, change_date, user, description)
                VALUES (?, ?, ?, ?)
            ''', (
                deposit_id,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "Użytkownik",  # Możesz zastąpić to faktycznym użytkownikiem
                description
            ))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Błąd podczas rejestrowania historii: {e}")

    def open_settings(self):
        """Otwiera okno ustawień aplikacji."""
        try:
            dialog = SettingsDialog(self)
            if dialog.exec():  # Wywołanie `exec()` tylko raz
                self.load_settings()
                self.load_active_deposits()
                self.load_statistics()
                QMessageBox.information(self, "Ustawienia", "Ustawienia zostały zaktualizowane.")
            else:
                logger.info("Zmiany w ustawieniach zostały anulowane.")
        except Exception as e:
            error_code = traceback.format_exc()
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas otwierania ustawień.\nKod błędu:\n{error_code}")
            logger.error(f"Błąd podczas otwierania ustawień: {e}")


    def create_backup(self):
        """Tworzy kopię zapasową bazy danych."""
        try:
            if not os.path.exists(self.backup_folder):
                os.makedirs(self.backup_folder)
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d%H%M%S')}.db"
            backup_path = os.path.join(self.backup_folder, backup_name)
            shutil.copy(DATABASE_NAME, backup_path)
            QMessageBox.information(self, "Kopia zapasowa", f"Kopia zapasowa została utworzona: {backup_path}")
        except Exception as e:
            error_code = traceback.format_exc()
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas tworzenia kopii zapasowej.\nKod błędu:\n{error_code}")
            logger.error(f"Błąd podczas tworzenia kopii zapasowej: {e}")

    def load_statistics(self):
        """Ładuje i wyświetla statystyki."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM deposits WHERE status = 'Aktywny'")
            active_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM deposits WHERE status = 'Wydany'")
            issued_count = cursor.fetchone()[0]
            cursor.execute("SELECT AVG(duration) FROM deposits WHERE duration IS NOT NULL")
            avg_duration = cursor.fetchone()[0] or 0

            # Raport finansowy
            cursor.execute("SELECT SUM(price) FROM deposits WHERE status = 'Aktywny'")
            total_income = cursor.fetchone()[0] or 0

            stats_text = f"""
            <h2>Statystyki</h2>
            <p>Liczba aktywnych depozytów: {active_count}</p>
            <p>Liczba wydanych depozytów: {issued_count}</p>
            <p>Średni czas trwania depozytu: {avg_duration:.2f} dni</p>
            <p>Przychody z aktywnych depozytów: {total_income} PLN</p>
            """

            # Wykres
            cursor.execute('''
                SELECT strftime('%Y-%m', deposit_date) as month, COUNT(*) FROM deposits
                GROUP BY month
                ORDER BY month
            ''')
            data = cursor.fetchall()
            months = [row[0] for row in data]
            counts = [row[1] for row in data]

            plt.figure(figsize=(8, 4))
            plt.bar(months, counts)
            plt.xlabel('Miesiąc')
            plt.ylabel('Liczba depozytów')
            plt.title('Depozyty w czasie')
            plt.tight_layout()
            plt.savefig('stats.png')
            plt.close()

            self.stats_label.setText(stats_text)
            pixmap = QPixmap('stats.png')
            self.stats_image.setPixmap(pixmap)
        except Exception as e:
            error_code = traceback.format_exc()
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas ładowania statystyk.\nKod błędu:\n{error_code}")
            logger.error(f"Błąd podczas ładowania statystyk: {e}")

    def update_deposit_durations(self):
        """Aktualizuje czas trwania depozytów."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE deposits
                SET duration = ROUND(julianday(CASE WHEN issue_date IS NULL THEN DATE('now') ELSE issue_date END) - julianday(deposit_date))
                WHERE deposit_date IS NOT NULL
            ''')
            self.conn.commit()
            self.load_active_deposits()
            self.load_issued_deposits()
            self.load_overdue_deposits()
            self.load_statistics()
        except Exception as e:
            logger.error(f"Błąd podczas aktualizacji czasu trwania depozytów: {e}")

    def check_and_send_reminders(self):
        """Sprawdza terminy i wysyła przypomnienia do klientów."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT deposits.id, clients.name, clients.email, deposits.expected_return_date
                FROM deposits
                INNER JOIN clients ON deposits.client_id = clients.id
                WHERE deposits.status = 'Aktywny'
            ''')
            rows = cursor.fetchall()
            today = QDate.currentDate()
            for row in rows:
                deposit_id, client_name, client_email, expected_return_date = row
                if client_email and expected_return_date:
                    return_date = QDate.fromString(expected_return_date, 'yyyy-MM-dd')
                    days_left = today.daysTo(return_date)
                    if days_left == 7:  # Przypomnienie na 7 dni przed terminem
                        subject = "Przypomnienie o odbiorze opon"
                        body = f"Szanowny {client_name},\n\nPrzypominamy o zbliżającym się terminie odbioru opon: {expected_return_date}.\n\nPozdrawiamy,\n{self.company_name}"
                        self.send_email(client_email, subject, body)
        except Exception as e:
            logger.error(f"Błąd podczas wysyłania przypomnień: {e}")

    def send_email(self, to_address, subject, body):
        """Wysyła e-mail z przypomnieniem i zapisuje historię."""
        from_address = self.email_settings.get('email_address', '')
        password = self.email_settings.get('email_password', '')
        smtp_server = self.email_settings.get('smtp_server', '')
        smtp_port = int(self.email_settings.get('smtp_port', '465'))

        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = from_address
        msg['To'] = to_address

        try:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            server.login(from_address, password)
            server.sendmail(from_address, [to_address], msg.as_string())
            server.quit()
            logger.info(f"Wysłano e-mail do {to_address}")
            self.save_email_history(to_address, subject, body)
        except Exception as e:
            logger.error(f"Błąd podczas wysyłania e-maila: {e}")

    def send_email_to_client(self, deposit_id):
        """Otwiera okno wysyłania e-maila do klienta."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT clients.email, clients.name, deposits.expected_return_date
                FROM deposits
                INNER JOIN clients ON deposits.client_id = clients.id
                WHERE deposits.id = ?
            ''', (deposit_id,))
            result = cursor.fetchone()
            if result:
                email, client_name, expected_return_date = result
                if email:
                    dialog = SendEmailDialog(self.conn, email, client_name, expected_return_date, parent=self)
                    dialog.exec()
                else:
                    QMessageBox.warning(self, "Brak adresu e-mail", "Klient nie ma podanego adresu e-mail.")
            else:
                QMessageBox.warning(self, "Błąd", "Nie znaleziono depozytu.")
        except Exception as e:
            logger.error(f"Błąd podczas przygotowywania e-maila: {e}")

    def save_email_history(self, to_address, subject, body):
        """Zapisuje historię wysłanego e-maila."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO email_history (to_address, subject, body, sent_date)
                VALUES (?, ?, ?, ?)
            ''', (to_address, subject, body, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania historii e-maili: {e}")

    def get_logo_path():
        """Pobiera ścieżkę do logo z ustawień aplikacji."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = 'company_logo'")
        result = cursor.fetchone()
        return result[0] if result else None


    def load_settings(self):
        """Ładuje ustawienia z bazy danych."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT key, value FROM settings")
            settings = dict(cursor.fetchall())

            # Ustawienia aplikacji
            self.backup_folder = settings.get('backup_folder', 'backups')
            self.company_name = settings.get('company_name', '')
            self.company_address = settings.get('company_address', '')
            self.company_contact = settings.get('company_contact', '')
            self.company_logo = settings.get('company_logo', '')

            # Sprawdzanie poprawności ścieżki logo
            if self.company_logo and not os.path.exists(self.company_logo):
                logger.warning(f"Nie znaleziono pliku logo: {self.company_logo}. Ustawienie domyślne logo.")
                self.company_logo = "default_logo.png"  # Ścieżka do domyślnego logo
                if not os.path.exists(self.company_logo):
                    self.company_logo = ""

            self.default_location = settings.get('default_location', '')
            self.auto_print = settings.get('auto_print', 'False') == 'True'
            self.default_printer = settings.get('default_printer', '')
            self.label_printer = settings.get('label_printer', '')

            # Ustawienia e-mail
            self.email_settings = {
                'email_address': settings.get('email_address', ''),
                'email_password': settings.get('email_password', ''),
                'smtp_server': settings.get('smtp_server', ''),
                'smtp_port': settings.get('smtp_port', '465'),
            }

            # Logowanie poprawnego załadowania ustawień
            logger.info("Ustawienia zostały pomyślnie załadowane.")
        except Exception as e:
            logger.error(f"Błąd podczas ładowania ustawień: {e}")
            
            # Zainicjalizowanie domyślnych wartości, aby uniknąć dalszych błędów
            self.backup_folder = 'backups'
            self.company_name = ''
            self.company_address = ''
            self.company_contact = ''
            self.company_logo = ''
            self.default_location = ''
            self.auto_print = False
            self.default_printer = ''
            self.label_printer = ''
            self.email_settings = {
                'email_address': '',
                'email_password': '',
                'smtp_server': '',
                'smtp_port': 465,
            }

            # Logowanie domyślnych ustawień dla debugowania
            logger.info(f"Backup Folder: {self.backup_folder}")
            logger.info(f"Company Name: {self.company_name}")


    def load_window_settings(self):
        """Ładuje ustawienia okna."""
        settings = QSettings("TireDepositManager", "MainWindow")
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        state = settings.value("windowState")
        if state:
            self.restoreState(state)

    def closeEvent(self, event):
        """Zapisuje ustawienia okna przy zamykaniu."""
        settings = QSettings("TireDepositManager", "MainWindow")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        super().closeEvent(event)

    def handle_barcode_scanned(self):
        """Obsługuje zeskanowanie kodu kreskowego klienta."""
        barcode, ok = QInputDialog.getText(self, "Skanuj kartę", "Zeskanuj kod kreskowy klienta:")
        if ok and barcode:
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT id FROM clients WHERE barcode = ?", (barcode,))
                result = cursor.fetchone()
                if result:
                    client_id = result[0]
                    QMessageBox.information(self, "Sukces", f"Znaleziono klienta o ID: {client_id}")
                else:
                    QMessageBox.warning(self, "Nie znaleziono", "Nie znaleziono klienta z tym kodem kreskowym.")
            except Exception as e:
                logger.error(f"Błąd podczas wyszukiwania klienta: {e}")
                QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas wyszukiwania klienta:\n{e}")


    def view_logs(self):
        """Wyświetla logi aplikacji w oknie."""
        try:
            with open(LOG_FILE, "r", encoding="windows-1250") as file:
                logs = file.read()
            log_viewer = QDialog(self)
            log_viewer.setWindowTitle("Logi aplikacji")
            layout = QVBoxLayout()
            text_area = QTextEdit()
            text_area.setText(logs)
            text_area.setReadOnly(True)
            layout.addWidget(text_area)
            log_viewer.setLayout(layout)
            log_viewer.exec()
        except Exception as e:
            logger.error(f"Błąd podczas wyświetlania logów: {e}")
            QMessageBox.critical(self, "Błąd", "Nie udało się załadować logów aplikacji.")



    def manage_discounts(self):
        """Zarządza rabatami i promocjami."""
        # Implementacja zarządzania rabatami
        QMessageBox.information(self, "Rabaty i promocje", "Funkcja zarządzania rabatami nie została jeszcze zaimplementowana.")

    def manage_complaints(self):
        """Obsługuje reklamacje klientów."""
        # Implementacja obsługi reklamacji
        QMessageBox.information(self, "Reklamacje", "Funkcja obsługi reklamacji nie została jeszcze zaimplementowana.")

    def handle_barcode_scanned(self):
        """Obsługuje zeskanowanie kodu kreskowego klienta."""
        barcode, ok = QInputDialog.getText(self, "Skanuj kartę", "Zeskanuj kod kreskowy klienta:")
        if ok and barcode:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM clients WHERE barcode = ?", (barcode,))
            client = cursor.fetchone()
            if client:
                client_id = client[0]
                self.open_client_vehicles_dialog(client_id)
            else:
                QMessageBox.warning(self, "Nie znaleziono", "Nie znaleziono klienta z podanym kodem kreskowym.")

    def open_client_vehicles_dialog(self, client_id):
        """Otwiera okno z pojazdami i depozytami klienta."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM clients WHERE id = ?", (client_id,))
            result = cursor.fetchone()

            if not result:
                QMessageBox.warning(self, "Błąd", "Nie znaleziono klienta.")
                return

            client_name = result[0]
            dialog = ClientVehiclesDialog(self.conn, client_id, client_name, parent=self)
            dialog.exec()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Błąd", f"Błąd podczas otwierania okna pojazdów klienta: {e}")
            logger.error(f"Błąd podczas otwierania okna pojazdów klienta: {e}")

    def contact_client(self, deposit_id):
        """Otwiera okno dialogowe do kontaktu z klientem."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT clients.name, clients.phone_number, clients.email
                FROM deposits
                INNER JOIN clients ON deposits.client_id = clients.id
                WHERE deposits.id = ?
            ''', (deposit_id,))
            result = cursor.fetchone()
            if result:
                client_name, phone_number, email = result
                message = f"Klient: {client_name}\nTelefon: {phone_number}\nE-mail: {email}"
                QMessageBox.information(self, "Dane kontaktowe", message)
            else:
                QMessageBox.warning(self, "Błąd", "Nie znaleziono danych klienta.")
        except Exception as e:
            logger.error(f"Błąd podczas pobierania danych klienta: {e}")

    def view_deposit_details(self, deposit_id):
        """Wyświetla szczegóły depozytu."""
        try:
            dialog = DepositDetailsDialog(self.conn, deposit_id, parent=self)
            dialog.exec()
        except Exception as e:
            logger.error(f"Błąd podczas wyświetlania szczegółów depozytu: {e}")

class OrderDialog(QDialog):
    """Dialog do dodawania i edycji zamówień."""
    def __init__(self, conn, order_id=None, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.order_id = order_id
        self.setWindowTitle("Dodaj zamówienie" if order_id is None else "Edytuj zamówienie")
        self.resize(800, 600)  # Powiększenie rozmiaru okna

        self.layout = QVBoxLayout(self)

        self.form_layout = QFormLayout()
        self.client_field = QLineEdit()
        self.client_field.setPlaceholderText("Wpisz nazwę klienta...")
        self.client_completer = QCompleter(self.get_client_names())
        self.client_field.setCompleter(self.client_completer)
        self.form_layout.addRow("Klient:", self.client_field)
        self.add_client_button = QPushButton("Dodaj nowego klienta")
        self.add_client_button.clicked.connect(self.add_client)
        self.form_layout.addRow("", self.add_client_button)

        self.order_date_input = QDateEdit()
        self.order_date_input.setCalendarPopup(True)
        self.order_date_input.setDate(QDate.currentDate())
        self.form_layout.addRow("Data zamówienia:", self.order_date_input)

        self.expected_delivery_date_input = QDateEdit()
        self.expected_delivery_date_input.setCalendarPopup(True)
        self.expected_delivery_date_input.setDate(QDate.currentDate().addDays(1))  # 1 dzień roboczy
        self.form_layout.addRow("Oczekiwana dostawa:", self.expected_delivery_date_input)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["Aktywne", "Zakończone"])
        self.form_layout.addRow("Status:", self.status_combo)

        self.notes_input = QTextEdit()
        self.form_layout.addRow("Uwagi:", self.notes_input)

        self.layout.addLayout(self.form_layout)


        # Lista pozycji zamówienia
        self.items_label = QLabel("Pozycje zamówienia:")
        self.layout.addWidget(self.items_label)
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels(["Marka opon", "Rozmiar opon", "Cena /szt.", "Ilość", "Razem"])
        self.items_table.horizontalHeader().setStretchLastSection(True)
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.items_table.itemChanged.connect(self.update_totals)
        self.layout.addWidget(self.items_table)

        # Przyciski do zarządzania pozycjami
        items_button_layout = QHBoxLayout()
        self.add_item_button = QPushButton("Dodaj pozycję")
        self.add_item_button.clicked.connect(self.add_item)
        self.remove_item_button = QPushButton("Usuń pozycję")
        self.remove_item_button.clicked.connect(self.remove_item)
        items_button_layout.addWidget(self.add_item_button)
        items_button_layout.addWidget(self.remove_item_button)
        self.layout.addLayout(items_button_layout)

        # Dodanie domyślnej pozycji
        self.add_item(default_values=["-", "-", "0", "0", "0.00"])

        # Przyciski
        self.button_layout = QHBoxLayout()
        self.save_button = QPushButton("Zapisz")
        self.save_button.clicked.connect(self.save_order)
        self.cancel_button = QPushButton("Anuluj")
        self.cancel_button.clicked.connect(self.reject)
        self.button_layout.addWidget(self.save_button)
        self.button_layout.addWidget(self.cancel_button)
        self.layout.addLayout(self.button_layout)

        if order_id:
            self.load_order_data()

    def get_client_names(self):
        """Pobiera listę nazw klientów z bazy danych."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM clients")
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Błąd podczas pobierania klientów: {e}")
            return []

    def add_client(self):
        """Otwiera okno dialogowe do dodawania nowego klienta."""
        try:
            dialog = AddClientDialog(self.conn, parent=self)
            if dialog.exec() == QDialog.Accepted:
                self.load_clients()
        except Exception as e:
            error_code = traceback.format_exc()
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas dodawania klienta.\nKod błędu:\n{error_code}")
            logger.error(f"Błąd podczas dodawania klienta: {e}")

    def add_item(self, default_values=None):
        """Dodaje nowy wiersz do tabeli pozycji zamówienia."""
        row_count = self.items_table.rowCount()
        self.items_table.insertRow(row_count)

        # Wartości domyślne dla nowego wiersza
        default_values = default_values or ["", "", "0", "0", "0.00"]

        for col in range(5):
            item = QTableWidgetItem(default_values[col])
            item.setFlags(item.flags() | Qt.ItemIsEditable)  # Ustaw edytowalność
            self.items_table.setItem(row_count, col, item)

    def remove_item(self):
        """Usuwa zaznaczony wiersz z tabeli pozycji zamówienia."""
        selected_row = self.items_table.currentRow()
        if selected_row >= 0:
            self.items_table.removeRow(selected_row)
        else:
            QMessageBox.warning(self, "Błąd", "Nie wybrano wiersza do usunięcia.")

    def update_totals(self):
        """Aktualizuje kolumnę 'Razem' i całkowitą sumę zamówienia."""
        self.items_table.blockSignals(True)  # Odłącz sygnały, aby zapobiec rekurencji
        total = 0.0
        for row in range(self.items_table.rowCount()):
            try:
                # Pobierz komórki
                price_item = self.items_table.item(row, 2)
                quantity_item = self.items_table.item(row, 3)
                
                if price_item is None or quantity_item is None:
                    continue  # Jeśli komórka jest pusta, pomiń
                
                # Konwersja wartości
                price = float(price_item.text() or 0)
                quantity = int(quantity_item.text() or 0)
                total_price = price * quantity
                
                # Ustaw wartość w kolumnie 'Razem'
                self.items_table.setItem(row, 4, QTableWidgetItem(f"{total_price:.2f}"))
                total += total_price
            except ValueError:
                continue  # Ignoruj błędy konwersji

        self.items_table.blockSignals(False)  # Ponownie podłącz sygnały
        
        # Aktualizuj sumę w etykiecie
        self.items_label.setText(f"Pozycje zamówienia: (Suma: {total:.2f} PLN)")


    def load_order_data(self):
        """Ładuje dane zamówienia do formularza."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT client_id, order_date, expected_delivery_date, status, notes
            FROM orders WHERE id = ?
        ''', (self.order_id,))
        order = cursor.fetchone()
        if order:
            client_id = order[0]
            client_name = cursor.execute("SELECT name FROM clients WHERE id = ?", (client_id,)).fetchone()[0]
            self.client_field.setText(client_name)
            order_date = QDate.fromString(order[1], 'yyyy-MM-dd')
            self.order_date_input.setDate(order_date)
            expected_delivery_date = QDate.fromString(order[2], 'yyyy-MM-dd')
            self.expected_delivery_date_input.setDate(expected_delivery_date)
            self.status_combo.setCurrentText(order[3])
            self.notes_input.setPlainText(order[4])

            # Ładuj pozycje zamówienia
            cursor.execute('''
                SELECT tire_brand, tire_size, price, quantity
                FROM order_items WHERE order_id = ?
            ''', (self.order_id,))
            items = cursor.fetchall()
            self.items_table.setRowCount(len(items))
            for row_idx, item in enumerate(items):
                for col_idx, value in enumerate(item):
                    self.items_table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))
            self.update_totals()

    def save_order(self):
        """Zapisuje zamówienie do bazy danych."""
        try:
            client_name = self.client_field.text()
            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM clients WHERE name = ?", (client_name,))
            client = cursor.fetchone()
            if client:
                client_id = client[0]
            else:
                # Dodaj nowego klienta, jeśli nie istnieje
                cursor.execute("INSERT INTO clients (name) VALUES (?)", (client_name,))
                self.conn.commit()
                client_id = cursor.lastrowid

            order_date = self.order_date_input.date().toString('yyyy-MM-dd')
            expected_delivery_date = self.expected_delivery_date_input.date().toString('yyyy-MM-dd')
            status = self.status_combo.currentText()
            notes = self.notes_input.toPlainText()

            if self.order_id:
                cursor.execute('''
                    UPDATE orders
                    SET client_id = ?, order_date = ?, expected_delivery_date = ?, status = ?, notes = ?
                    WHERE id = ?
                ''', (client_id, order_date, expected_delivery_date, status, notes, self.order_id))
            else:
                cursor.execute('''
                    INSERT INTO orders (client_id, order_date, expected_delivery_date, status, notes)
                    VALUES (?, ?, ?, ?, ?)
                ''', (client_id, order_date, expected_delivery_date, status, notes))
                self.order_id = cursor.lastrowid

            # Zapisz pozycje zamówienia
            cursor.execute("DELETE FROM order_items WHERE order_id = ?", (self.order_id,))
            for row in range(self.items_table.rowCount()):
                tire_brand = self.items_table.item(row, 0).text()
                tire_size = self.items_table.item(row, 1).text()
                price = self.items_table.item(row, 2).text()
                quantity = self.items_table.item(row, 3).text()
                cursor.execute('''
                    INSERT INTO order_items (order_id, tire_brand, tire_size, price, quantity)
                    VALUES (?, ?, ?, ?, ?)
                ''', (self.order_id, tire_brand, tire_size, price, quantity))

            self.conn.commit()
            self.accept()
        except Exception as e:
            error_code = traceback.format_exc()
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas zapisywania zamówienia.\nKod błędu:\n{error_code}")
            logger.error(f"Błąd podczas zapisywania zamówienia: {e}")




class InventoryItemDialog(QDialog):
    def __init__(self, conn, inventory_id=None, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.inventory_id = inventory_id
        self.setWindowTitle("Dodaj oponę" if inventory_id is None else "Edytuj oponę")
        self.layout = QVBoxLayout(self)

        self.form_layout = QFormLayout()
        self.brand_model_input = QLineEdit()
        self.form_layout.addRow("Marka i model:", self.brand_model_input)

        self.size_input = QLineEdit()
        self.form_layout.addRow("Rozmiar:", self.size_input)

        self.quantity_input = QLineEdit()
        self.form_layout.addRow("Ilość:", self.quantity_input)

        self.price_input = QLineEdit()
        self.form_layout.addRow("Cena:", self.price_input)

        self.dot_input = QLineEdit()
        self.form_layout.addRow("DOT:", self.dot_input)

        self.season_type_combo = QComboBox()
        self.season_type_combo.addItems(["Letnia", "Zimowa", "Wielosezonowa"])
        self.form_layout.addRow("Typ sezonowy:", self.season_type_combo)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Wprowadź dodatkowe uwagi...")
        self.form_layout.addRow("Uwagi:", self.notes_input)

        self.layout.addLayout(self.form_layout)

        self.button_layout = QHBoxLayout()
        self.save_button = QPushButton("Zapisz")
        self.save_button.clicked.connect(self.save_inventory)
        self.cancel_button = QPushButton("Anuluj")
        self.cancel_button.clicked.connect(self.reject)
        self.button_layout.addWidget(self.save_button)
        self.button_layout.addWidget(self.cancel_button)
        self.layout.addLayout(self.button_layout)

        if inventory_id:
            self.load_inventory_data()

    def update_inventory_table(conn):
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(inventory)")
        columns = [column[1] for column in cursor.fetchall()]
        if "notes" not in columns:
            cursor.execute("ALTER TABLE inventory ADD COLUMN notes TEXT DEFAULT ''")
        if "season_type" not in columns:  # Dodaj inne brakujące kolumny, jeśli są potrzebne
            cursor.execute("ALTER TABLE inventory ADD COLUMN season_type TEXT DEFAULT 'Letnia'")
        conn.commit()

        

    def load_inventory_data(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT brand_model, size, quantity, price, dot, notes, season_type FROM inventory WHERE id = ?", (self.inventory_id,))
        item = cursor.fetchone()
        if item:
            self.brand_model_input.setText(item[0])
            self.size_input.setText(item[1])
            self.quantity_input.setText(str(item[2]))
            self.price_input.setText(str(item[3]))
            self.dot_input.setText(item[4])
            self.notes_input.setPlainText(item[5] if len(item) > 5 and item[5] else "")
            if len(item) > 6 and item[6]:
                index = self.season_type_combo.findText(item[6])
                if index >= 0:
                    self.season_type_combo.setCurrentIndex(index)


    def update_inventory_table(conn):
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(inventory)")
        columns = [column[1] for column in cursor.fetchall()]
        if "brand_model" not in columns:
            cursor.execute("ALTER TABLE inventory ADD COLUMN brand_model TEXT NOT NULL DEFAULT ''")
        if "notes" not in columns:
            cursor.execute("ALTER TABLE inventory ADD COLUMN notes TEXT DEFAULT ''")
        if "season_type" not in columns:
            cursor.execute("ALTER TABLE inventory ADD COLUMN season_type TEXT DEFAULT 'Letnia'")
        conn.commit()

    def save_inventory(self):
        """Zapisuje oponę do tabeli inventory."""
        try:
            brand_model = self.brand_model_input.text().strip()
            size = self.size_input.text().strip()
            quantity = self.quantity_input.text().strip()
            price = self.price_input.text().strip()
            dot = self.dot_input.text().strip()
            notes = self.notes_input.toPlainText().strip()
            season_type = self.season_type_combo.currentText()

            if not brand_model:
                QMessageBox.warning(self, "Błąd", "Pole 'Marka i model' jest wymagane.")
                return
            if not size:
                QMessageBox.warning(self, "Błąd", "Pole 'Rozmiar' jest wymagane.")
                return
            if not quantity.isdigit():
                QMessageBox.warning(self, "Błąd", "Pole 'Ilość' musi być liczbą.")
                return
            if not self.is_float(price):
                QMessageBox.warning(self, "Błąd", "Pole 'Cena' musi być liczbą.")
                return

            quantity = int(quantity)
            price = float(price)

            cursor = self.conn.cursor()
            if self.inventory_id:
                cursor.execute('''
                    UPDATE inventory
                    SET brand_model = ?, size = ?, quantity = ?, price = ?, dot = ?, notes = ?, season_type = ?
                    WHERE id = ?
                ''', (brand_model, size, quantity, price, dot, notes, season_type, self.inventory_id))
            else:
                cursor.execute('''
                    INSERT INTO inventory (brand_model, size, quantity, price, dot, notes, season_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (brand_model, size, quantity, price, dot, notes, season_type))
            self.conn.commit()

            QMessageBox.information(self, "Sukces", "Opona została zapisana.")
            self.accept()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Błąd", f"Błąd bazy danych: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas zapisywania opony: {e}")

    def is_float(self, value):
        """Sprawdza, czy wartość jest liczbą zmiennoprzecinkową."""
        try:
            float(value)
            return True
        except ValueError:
            return False








class OrderDetailsDialog(QDialog):
    """Dialog wyświetlający szczegóły zamówienia."""
    def __init__(self, conn, order_id, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.order_id = order_id
        self.setWindowTitle("Szczegóły Zamówienia")
        self.layout = QVBoxLayout(self)

        # Pobierz dane zamówienia
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT orders.*, clients.name, clients.phone_number, clients.email
            FROM orders
            INNER JOIN clients ON orders.client_id = clients.id
            WHERE orders.id = ?
        ''', (self.order_id,))
        order = cursor.fetchone()
        if order:
            order_info = {
                'ID': order[0],
                'Klient': order[-3],
                'Telefon': order[-2],
                'E-mail': order[-1],
                'Data zamówienia': order[2],
                'Oczekiwana dostawa': order[3],
                'Status': order[4],
                'Uwagi': order[5]
            }
            # Wyświetl dane w formularzu
            form_layout = QFormLayout()
            for key, value in order_info.items():
                form_layout.addRow(QLabel(f"<b>{key}:</b>"), QLabel(str(value)))
            self.layout.addLayout(form_layout)

            # Wyświetl pozycje zamówienia
            self.items_label = QLabel("Pozycje zamówienia:")
            self.layout.addWidget(self.items_label)
            self.items_table = QTableWidget()
            self.items_table.setColumnCount(4)
            self.items_table.setHorizontalHeaderLabels(["Marka opon", "Rozmiar opon", "Ilość", "Cena"])
            self.items_table.setEditTriggers(QTableWidget.NoEditTriggers)
            self.items_table.horizontalHeader().setStretchLastSection(True)
            self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.layout.addWidget(self.items_table)

            cursor.execute('''
                SELECT tire_brand, size, quantity, price
                FROM order_items WHERE order_id = ?
            ''', (self.order_id,))
            items = cursor.fetchall()
            self.items_table.setRowCount(len(items))
            for row_idx, item in enumerate(items):
                for col_idx, value in enumerate(item):
                    self.items_table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

            # Przyciski
            button_layout = QHBoxLayout()
            close_button = QPushButton("Zamknij")
            close_button.clicked.connect(self.close)
            button_layout.addWidget(close_button)
            self.layout.addLayout(button_layout)
        else:
            QMessageBox.warning(self, "Błąd", "Nie znaleziono danych zamówienia.")
            self.close()

class DepositDialog(QDialog):
    def __init__(self, conn, deposit_id=None, default_location='', parent=None):
        super().__init__(parent)
        self.conn = conn
        self.deposit_id = deposit_id
        self.default_location = default_location
        self.setWindowTitle("Dodaj depozyt" if deposit_id is None else "Edytuj depozyt")
        self.layout = QVBoxLayout(self)

        self.form_layout = QFormLayout()
        self.client_combo = QComboBox()
        self.load_clients()
        self.form_layout.addRow("Klient:", self.client_combo)
        self.add_client_button = QPushButton("Dodaj nowego klienta")
        self.add_client_button.clicked.connect(self.add_client)
        self.form_layout.addRow("", self.add_client_button)

        self.car_model_input = QLineEdit()
        self.form_layout.addRow("Model auta:", self.car_model_input)
        self.load_car_models()

        self.registration_number_input = QLineEdit()
        self.form_layout.addRow("Nr rejestracyjny*:", self.registration_number_input)
        self.load_registration_numbers()

        self.tire_brand_input = QLineEdit()
        self.form_layout.addRow("Marka opon:", self.tire_brand_input)
        self.load_tire_brands()

        self.tire_size_input = QLineEdit()
        self.form_layout.addRow("Rozmiar opon*:", self.tire_size_input)
        self.load_tire_sizes()

        self.quantity_input = QLineEdit("4")
        self.form_layout.addRow("Ilość*:", self.quantity_input)

        self.season_combo = QComboBox()
        self.season_combo.addItems(["Lato", "Zima", "Całoroczne"])
        self.form_layout.addRow("Sezon:", self.season_combo)

        self.location_input = QLineEdit()
        self.form_layout.addRow("Lokalizacja:", self.location_input)

        self.expected_return_date_input = QDateEdit()
        self.expected_return_date_input.setCalendarPopup(True)
        self.expected_return_date_input.setDate(QDate.currentDate().addMonths(6))
        self.form_layout.addRow("Oczekiwany zwrot:", self.expected_return_date_input)

        self.washing_combo = QComboBox()
        self.washing_combo.addItems(["Nie", "Tak"])
        self.form_layout.addRow("Mycie:", self.washing_combo)

        self.conservation_combo = QComboBox()
        self.conservation_combo.addItems(["Nie", "Tak"])
        self.form_layout.addRow("Konserwacja:", self.conservation_combo)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["Aktywny", "Wydany"])
        self.form_layout.addRow("Status:", self.status_combo)

        self.technical_condition_input = QLineEdit()
        self.form_layout.addRow("Stan techniczny:", self.technical_condition_input)

        self.storage_date_input = QDateEdit()
        self.storage_date_input.setCalendarPopup(True)
        self.storage_date_input.setDate(QDate.currentDate())
        self.form_layout.addRow("Data przechowywania:", self.storage_date_input)

        self.price_input = QLineEdit()
        self.form_layout.addRow("Cena:", self.price_input)

        self.layout.addLayout(self.form_layout)

        # Przyciski
        self.button_layout = QHBoxLayout()
        self.save_button = QPushButton("Zapisz")
        self.save_button.clicked.connect(self.save_deposit)
        self.cancel_button = QPushButton("Anuluj")
        self.cancel_button.clicked.connect(self.reject)
        self.button_layout.addWidget(self.save_button)
        self.button_layout.addWidget(self.cancel_button)
        self.layout.addLayout(self.button_layout)

        if deposit_id:
            self.load_deposit_data()
        else:
            if self.default_location:
                self.location_input.setText(self.default_location)

    def load_clients(self):
        """Ładuje listę klientów do pola wyboru."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name FROM clients")
        clients = cursor.fetchall()
        self.client_combo.clear()
        for client in clients:
            self.client_combo.addItem(client[1], client[0])

    def add_client(self):
        """Dodaje nowego klienta."""
        dialog = AddClientDialog(self.conn, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.load_clients()
            index = self.client_combo.findText(dialog.client_name)
            if index >= 0:
                self.client_combo.setCurrentIndex(index)

    def load_tire_sizes(self):
        """Ładuje listę rozmiarów opon do autouzupełniania."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT tire_size FROM deposits")
        sizes = [row[0] for row in cursor.fetchall() if row[0]]
        completer = QCompleter(sizes)
        self.tire_size_input.setCompleter(completer)

    def load_car_models(self):
        """Ładuje listę modeli aut do autouzupełniania."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT car_model FROM deposits")
        models = [row[0] for row in cursor.fetchall() if row[0]]
        completer = QCompleter(models)
        self.car_model_input.setCompleter(completer)

    def load_registration_numbers(self):
        """Ładuje listę numerów rejestracyjnych do autouzupełniania."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT registration_number FROM deposits")
        numbers = [row[0] for row in cursor.fetchall() if row[0]]
        completer = QCompleter(numbers)
        self.registration_number_input.setCompleter(completer)

    def load_tire_brands(self):
        """Ładuje listę marek opon do autouzupełniania."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT tire_brand FROM deposits")
        brands = [row[0] for row in cursor.fetchall() if row[0]]
        completer = QCompleter(brands)
        self.tire_brand_input.setCompleter(completer)

    def load_deposit_data(self):
        """Ładuje dane depozytu do formularza."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT client_id, car_model, registration_number, tire_brand, tire_size,
                   quantity, location, washing, conservation, status, season, expected_return_date,
                   technical_condition, storage_date, price
            FROM deposits WHERE id = ?
        ''', (self.deposit_id,))
        deposit = cursor.fetchone()
        if deposit:
            client_id = deposit[0]
            index = self.client_combo.findData(client_id)
            if index >= 0:
                self.client_combo.setCurrentIndex(index)
            self.car_model_input.setText(deposit[1])
            self.registration_number_input.setText(deposit[2])
            self.tire_brand_input.setText(deposit[3])
            self.tire_size_input.setText(deposit[4])
            self.quantity_input.setText(str(deposit[5]))
            self.location_input.setText(deposit[6])
            self.washing_combo.setCurrentText("Tak" if deposit[7] else "Nie")
            self.conservation_combo.setCurrentText("Tak" if deposit[8] else "Nie")
            self.status_combo.setCurrentText(deposit[9])
            self.season_combo.setCurrentText(deposit[10])
            if deposit[11]:
                date = QDate.fromString(deposit[11], 'yyyy-MM-dd')
                self.expected_return_date_input.setDate(date)
            self.technical_condition_input.setText(deposit[12])
            if deposit[13]:
                date = QDate.fromString(deposit[13], 'yyyy-MM-dd')
                self.storage_date_input.setDate(date)
            self.price_input.setText(str(deposit[14]))

    def save_deposit(self):
        """Zapisuje depozyt do bazy danych."""
        try:
            client_id = self.client_combo.currentData()
            car_model = self.car_model_input.text()
            registration_number = self.registration_number_input.text()
            tire_brand = self.tire_brand_input.text()
            tire_size = self.tire_size_input.text()
            quantity = self.quantity_input.text()
            location = self.location_input.text()
            washing = self.washing_combo.currentText() == "Tak"
            conservation = self.conservation_combo.currentText() == "Tak"
            status = self.status_combo.currentText()
            season = self.season_combo.currentText()
            expected_return_date = self.expected_return_date_input.date().toString('yyyy-MM-dd')
            technical_condition = self.technical_condition_input.text()
            storage_date = self.storage_date_input.date().toString('yyyy-MM-dd')
            price = self.price_input.text()

            # Walidacja danych
            if not client_id:
                QMessageBox.warning(self, "Błąd", "Musisz wybrać klienta.")
                return
            if not registration_number.strip():
                QMessageBox.warning(self, "Błąd", "Musisz podać numer rejestracyjny.")
                return
            if not tire_size.strip():
                QMessageBox.warning(self, "Błąd", "Musisz podać rozmiar opon.")
                return
            if not quantity.strip() or not quantity.isdigit():
                QMessageBox.warning(self, "Błąd", "Musisz podać poprawną ilość sztuk.")
                return
            if not price.strip() or not self.is_float(price):
                QMessageBox.warning(self, "Błąd", "Musisz podać poprawną cenę.")
                return

            quantity = int(quantity)
            price = float(price)

            cursor = self.conn.cursor()
            if self.deposit_id:
                cursor.execute('''
                    UPDATE deposits
                    SET client_id = ?, car_model = ?, registration_number = ?, tire_brand = ?, tire_size = ?,
                        quantity = ?, location = ?, washing = ?, conservation = ?, status = ?, season = ?, expected_return_date = ?,
                        technical_condition = ?, storage_date = ?, price = ?
                    WHERE id = ?
                ''', (
                    client_id, car_model, registration_number, tire_brand, tire_size,
                    quantity, location, washing, conservation, status, season, expected_return_date,
                    technical_condition, storage_date, price,
                    self.deposit_id
                ))
                self.record_history(self.deposit_id, "Zaktualizowano depozyt")
            else:
                cursor.execute('''
                    INSERT INTO deposits (
                        client_id, car_model, registration_number, tire_brand, tire_size,
                        quantity, location, washing, conservation, deposit_date, status, season, expected_return_date,
                        technical_condition, storage_date, price
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    client_id, car_model, registration_number, tire_brand, tire_size,
                    quantity, location, washing, conservation,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    status, season, expected_return_date,
                    technical_condition, storage_date, price
                ))
                deposit_id = cursor.lastrowid
                self.record_history(deposit_id, "Dodano nowy depozyt")
            self.conn.commit()
            self.accept()
        except Exception as e:
            error_code = traceback.format_exc()
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas zapisywania depozytu.\nKod błędu:\n{error_code}")
            logger.error(f"Błąd podczas zapisywania depozytu: {e}")

    def is_float(self, value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    def record_history(self, deposit_id, description):
        """Rejestruje zmianę w historii."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO history (deposit_id, change_date, user, description)
                VALUES (?, ?, ?, ?)
            ''', (
                deposit_id,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "Użytkownik",  # Możesz zastąpić to faktycznym użytkownikiem
                description
            ))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Błąd podczas rejestrowania historii: {e}")

class AddClientDialog(QDialog):
    def __init__(self, conn, client_id=None, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.client_id = client_id
        self.client_name = ""
        self.setWindowTitle("Dodaj klienta" if client_id is None else "Edytuj klienta")
        self.layout = QVBoxLayout(self)

        # Inicjalizacja formularza
        self.form_layout = QFormLayout()
        self.name_input = QLineEdit()
        self.form_layout.addRow("Nazwa klienta*:", self.name_input)

        self.phone_input = QLineEdit()
        self.form_layout.addRow("Numer telefonu:", self.phone_input)

        self.email_input = QLineEdit()
        self.form_layout.addRow("Adres e-mail:", self.email_input)

        self.discount_input = QLineEdit("0")
        self.form_layout.addRow("Rabat (%):", self.discount_input)

        self.additional_info_input = QLineEdit()
        self.form_layout.addRow("Dodatkowe informacje:", self.additional_info_input)

        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Skanuj kartę stałego klienta.")
        self.barcode_input.returnPressed.connect(self.handle_barcode_scanned)
        self.form_layout.addRow("Kod kreskowy:", self.barcode_input)

        self.layout.addLayout(self.form_layout)

        # Przyciski
        self.button_layout = QHBoxLayout()
        self.save_button = QPushButton("Zapisz")
        self.save_button.clicked.connect(self.save_client)
        self.cancel_button = QPushButton("Anuluj")
        self.cancel_button.clicked.connect(self.reject)
        self.button_layout.addWidget(self.save_button)
        self.button_layout.addWidget(self.cancel_button)
        self.layout.addLayout(self.button_layout)

        # Załaduj dane klienta, jeśli to edycja
        if client_id:
            self.load_client_data()

    def load_client_data(self):
        """Ładuje dane klienta do formularza."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT name, phone_number, email, discount, additional_info, barcode
                FROM clients WHERE id = ?
            ''', (self.client_id,))
            client = cursor.fetchone()
            if client:
                self.name_input.setText(client[0])
                self.phone_input.setText(client[1])
                self.email_input.setText(client[2])
                self.discount_input.setText(str(client[3]))
                self.additional_info_input.setText(client[4])
                self.barcode_input.setText(client[5])
        except Exception as e:
            logger.error(f"Błąd podczas ładowania danych klienta: {e}")

    def save_client(self):
        """Zapisuje nowego lub edytowanego klienta."""
        try:
            name = self.name_input.text().strip()
            phone_number = self.phone_input.text().strip()
            email = self.email_input.text().strip()
            discount = self.discount_input.text().strip()
            additional_info = self.additional_info_input.text().strip()
            barcode = self.barcode_input.text().strip()

            if not name:
                QMessageBox.warning(self, "Błąd", "Musisz podać nazwę klienta.")
                return
            if not discount or not self.is_float(discount):
                QMessageBox.warning(self, "Błąd", "Musisz podać poprawny rabat.")
                return

            discount = float(discount)

            cursor = self.conn.cursor()
            if self.client_id:
                cursor.execute('''
                    UPDATE clients
                    SET name = ?, phone_number = ?, email = ?, discount = ?, additional_info = ?, barcode = ?
                    WHERE id = ?
                ''', (name, phone_number, email, discount, additional_info, barcode, self.client_id))
            else:
                cursor.execute('''
                    INSERT INTO clients (name, phone_number, email, discount, additional_info, barcode)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (name, phone_number, email, discount, additional_info, barcode))
                self.client_id = cursor.lastrowid

            self.conn.commit()
            self.client_name = name
            self.accept()
        except Exception as e:
            error_code = traceback.format_exc()
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas zapisywania klienta.\nKod błędu:\n{error_code}")
            logger.error(f"Błąd podczas zapisywania klienta: {e}")

    def is_float(self, value):
        """Sprawdza, czy wartość może być przekonwertowana na float."""
        try:
            float(value)
            return True
        except ValueError:
            return False

    def handle_barcode_scanned(self):
        """Obsługuje zeskanowanie kodu kreskowego klienta."""
        barcode = self.barcode_input.text().strip()
        if barcode:
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT id, name FROM clients WHERE barcode = ?", (barcode,))
                result = cursor.fetchone()
                if result:
                    client_id, name = result
                    QMessageBox.information(self, "Sukces", f"Znaleziono klienta: {name} (ID: {client_id})")
                else:
                    QMessageBox.warning(self, "Nie znaleziono", "Nie znaleziono klienta z tym kodem kreskowym.")
            except Exception as e:
                logger.error(f"Błąd podczas wyszukiwania klienta: {e}")
                QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas wyszukiwania klienta:\n{e}")


class EditClientDialog(AddClientDialog):
    """Dialog do edycji klienta."""
    def __init__(self, conn, client_id, parent=None):
        super().__init__(conn, client_id, parent)

class ClientDepositsDialog(QDialog):
    """Dialog wyświetlający depozyty powiązane z klientem."""
    def __init__(self, conn, client_id, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.client_id = client_id
        self.setWindowTitle("Depozyty klienta")
        self.resize(1000, 600)  # Ustawienie większego rozmiaru okna
        self.layout = QVBoxLayout(self)

        self.table_deposits = QTableWidget()
        self.table_deposits.setColumnCount(18)
        self.table_deposits.setHorizontalHeaderLabels([
            "ID", "Model auta", "Nr rejestracyjny", "Marka opon", "Rozmiar opon",
            "Ilość", "Lokalizacja", "Mycie", "Konserwacja", "Data depozytu",
            "Data wydania", "Sezon", "Status", "Czas trwania (dni)",
            "Stan techniczny", "Data przechowywania", "Cena", "Historia"
        ])
        self.table_deposits.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_deposits.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_deposits.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_deposits.customContextMenuRequested.connect(self.open_context_menu)
        self.table_deposits.horizontalHeader().setStretchLastSection(True)
        self.table_deposits.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.table_deposits)

        self.load_deposits()
        self.adjust_table_headers()

    def adjust_table_headers(self):
        """Dostosowuje szerokość kolumn dla lepszej czytelności."""
        header = self.table_deposits.horizontalHeader()
        for i in range(self.table_deposits.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)

    def load_deposits(self):
        """Ładuje depozyty powiązane z klientem."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT id, car_model, registration_number, tire_brand, tire_size, quantity,
                       location, washing, conservation, deposit_date, issue_date, season, status, duration,
                       technical_condition, storage_date, price
                FROM deposits
                WHERE client_id = ?
                ORDER BY deposit_date DESC
            ''', (self.client_id,))
            rows = cursor.fetchall()

            self.table_deposits.setRowCount(len(rows))
            for row_idx, row in enumerate(rows):
                for col_idx, value in enumerate(row):
                    if col_idx == 7 or col_idx == 8:  # Kolumny Mycie i Konserwacja
                        value = "Tak" if value else "Nie"
                    if col_idx == 13:  # Czas trwania
                        value = str(int(value)) if value else "0"
                    item = QTableWidgetItem(str(value))
                    self.table_deposits.setItem(row_idx, col_idx, item)
                # Dodaj przycisk do historii
                history_button = QPushButton("Pokaż historię")
                history_button.clicked.connect(lambda checked, deposit_id=row[0]: self.show_history(deposit_id))
                self.table_deposits.setCellWidget(row_idx, 17, history_button)
        except Exception as e:
            error_code = traceback.format_exc()
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas ładowania depozytów klienta.\nKod błędu:\n{error_code}")
            logger.error(f"Błąd podczas ładowania depozytów klienta: {e}")

    def open_context_menu(self, position):
        """Obsługuje menu kontekstowe dla tabeli depozytów klienta."""
        try:
            menu = QMenu()
            edit_action = QAction("Edytuj depozyt", self)
            delete_action = QAction("Usuń depozyt", self)
            generate_label_action = QAction("Generuj etykietę", self)
            print_confirmation_action = QAction("Drukuj potwierdzenie", self)
            menu.addAction(edit_action)
            menu.addAction(generate_label_action)
            menu.addAction(print_confirmation_action)
            menu.addAction(delete_action)

            action = menu.exec(self.table_deposits.viewport().mapToGlobal(position))
            selected_row = self.table_deposits.currentRow()
            if selected_row < 0:
                return
            deposit_id = int(self.table_deposits.item(selected_row, 0).text())

            if action == edit_action:
                self.edit_deposit(deposit_id)
            elif action == delete_action:
                self.delete_deposit(deposit_id)
            elif action == generate_label_action:
                self.generate_label(deposit_id)
            elif action == print_confirmation_action:
                self.print_confirmation(deposit_id)
        except Exception as e:
            error_code = traceback.format_exc()
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas obsługi menu kontekstowego.\nKod błędu:\n{error_code}")
            logger.error(f"Błąd podczas obsługi menu kontekstowego: {e}")

    def edit_deposit(self, deposit_id):
        """Edytuje depozyt."""
        try:
            dialog = DepositDialog(self.conn, deposit_id, parent=self)
            if dialog.exec() == QDialog.Accepted:
                self.load_deposits()
        except Exception as e:
            error_code = traceback.format_exc()
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas edycji depozytu.\nKod błędu:\n{error_code}")
            logger.error(f"Błąd podczas edycji depozytu: {e}")

    def delete_deposit(self, deposit_id):
        """Usuwa depozyt."""
        try:
            reply = QMessageBox.question(
                self, "Usuń depozyt",
                "Czy na pewno chcesz usunąć ten depozyt?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM deposits WHERE id = ?", (deposit_id,))
                self.conn.commit()
                self.load_deposits()
        except Exception as e:
            error_code = traceback.format_exc()
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas usuwania depozytu.\nKod błędu:\n{error_code}")
            logger.error(f"Błąd podczas usuwania depozytu: {e}")

    def generate_label(self, deposit_id):
        """Generuje etykietę PDF z opcją drukowania, otwierania lub anulowania."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT deposits.id, clients.name, deposits.tire_brand, deposits.tire_size, deposits.quantity
                FROM deposits
                INNER JOIN clients ON deposits.client_id = clients.id
                WHERE deposits.id = ?
            ''', (deposit_id,))
            result = cursor.fetchone()

            if result:
                deposit_id, client_name, tire_brand, tire_size, quantity = result
                logo_path = get_file_path("logo.png")
                output_path = generate_pdf_label(deposit_id, client_name, tire_brand, tire_size, quantity, logo_path)

                message_box = QMessageBox(self)
                message_box.setWindowTitle("Etykieta wygenerowana")
                message_box.setText(f"Etykieta została wygenerowana: {output_path}\n\nCo chcesz zrobić?")
                open_button = message_box.addButton("Otwórz", QMessageBox.ActionRole)
                print_button = message_box.addButton("Drukuj", QMessageBox.ActionRole)
                cancel_button = message_box.addButton("Nie", QMessageBox.RejectRole)

                message_box.exec()

                if message_box.clickedButton() == open_button:
                    self.open_file(output_path)
                elif message_box.clickedButton() == print_button:
                    self.print_file(output_path)
            else:
                QMessageBox.warning(self, "Błąd", "Nie znaleziono danych dla tego depozytu.")
        except Exception as e:
            logger.error(f"Błąd podczas generowania etykiety: {e}")
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas generowania etykiety:\n{e}")




    def print_label(self, file_path):
        """Drukuje etykietę na drukarce Niimbot B1."""
        try:
            printer_name = self.label_printer  # Pobierz ustawioną drukarkę Niimbot
            if not printer_name:
                QMessageBox.warning(self, "Błąd", "Drukarka Niimbot B1 nie jest ustawiona w ustawieniach.")
                return

            # Komenda drukowania – możesz dostosować dla Niimbot B1
            # Użyj subprocess do wysłania pliku na drukarkę
            subprocess.run(["lp", "-d", printer_name, file_path], check=True)

            QMessageBox.information(self, "Sukces", "Etykieta została wydrukowana.")
        except Exception as e:
            logger.error(f"Błąd podczas drukowania etykiety: {e}")
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas drukowania etykiety:\n{e}")

    def open_file(self, file_path):
        """Otwiera wygenerowany plik PDF w domyślnej przeglądarce PDF."""
        try:
            if os.path.exists(file_path):
                logger.info(f"Otwieranie pliku PDF: {file_path}")
                if sys.platform == "win32":
                    os.startfile(file_path)  # Działa na Windows
                elif sys.platform == "darwin":
                    subprocess.run(["open", file_path])
                else:
                    subprocess.run(["xdg-open", file_path])
            else:
                logger.error(f"Plik PDF nie istnieje: {file_path}")
                QMessageBox.critical(self, "Błąd", f"Plik PDF nie istnieje: {file_path}")
        except Exception as e:
            logger.error(f"Błąd podczas otwierania pliku PDF: {e}")
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas otwierania pliku:\n{e}")



    def print_confirmation(self, deposit_id):
        """Generuje potwierdzenie PDF z opcją drukowania, otwierania lub anulowania."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT deposits.id, clients.name, deposits.car_model, deposits.registration_number,
                    deposits.tire_brand, deposits.tire_size, deposits.quantity, deposits.deposit_date
                FROM deposits
                INNER JOIN clients ON deposits.client_id = clients.id
                WHERE deposits.id = ?
            ''', (deposit_id,))
            result = cursor.fetchone()

            if result:
                deposit_id, client_name, car_model, registration_number, tire_brand, tire_size, quantity, deposit_date = result
                logo_path = get_file_path("logo.png")
                output_path = generate_pdf_confirmation(
                    deposit_id,
                    client_name,
                    [
                        f"Model Auta: {car_model}",
                        f"Nr Rejestracyjny: {registration_number}",
                        f"Marka Opon: {tire_brand}",
                        f"Rozmiar Opon: {tire_size}",
                        f"Ilość: {quantity}",
                        f"Data Przyjęcia: {deposit_date}",
                    ],
                    logo_path
                )

                message_box = QMessageBox(self)
                message_box.setWindowTitle("Potwierdzenie wygenerowane")
                message_box.setText(f"Potwierdzenie zostało wygenerowane: {output_path}\n\nCo chcesz zrobić?")
                open_button = message_box.addButton("Otwórz", QMessageBox.ActionRole)
                print_button = message_box.addButton("Drukuj", QMessageBox.ActionRole)
                cancel_button = message_box.addButton("Nie", QMessageBox.RejectRole)

                message_box.exec()

                if message_box.clickedButton() == open_button:
                    self.open_file(output_path)
                elif message_box.clickedButton() == print_button:
                    self.print_file(output_path)
            else:
                QMessageBox.warning(self, "Błąd", "Nie znaleziono danych dla tego depozytu.")
        except Exception as e:
            logger.error(f"Błąd podczas drukowania potwierdzenia: {e}")
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas drukowania potwierdzenia:\n{e}")

    def print_file(self, file_path):
        """Drukuje plik PDF za pomocą domyślnej drukarki."""
        try:
            logger.info(f"Drukowanie pliku: {file_path}")
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Plik nie istnieje: {file_path}")

            # Wykorzystaj Windows API do drukowania
            win32api.ShellExecute(0, "print", file_path, None, ".", 0)
            logger.info(f"Plik {file_path} został wysłany do drukarki.")
        except Exception as e:
            logger.error(f"Błąd podczas drukowania pliku: {e}")
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas drukowania pliku:\n{e}")




    def print_confirmation_file(self, file_path):
        """Drukuje potwierdzenie na domyślnej drukarce."""
        try:
            printer_name = self.default_printer  # Pobierz domyślną drukarkę z ustawień
            if not printer_name:
                QMessageBox.warning(self, "Błąd", "Domyślna drukarka nie jest ustawiona w ustawieniach.")
                return

            # Komenda drukowania
            subprocess.run(["lp", "-d", printer_name, file_path], check=True)

            QMessageBox.information(self, "Sukces", "Potwierdzenie zostało wydrukowane.")
        except Exception as e:
            logger.error(f"Błąd podczas drukowania potwierdzenia: {e}")
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas drukowania potwierdzenia:\n{e}")

    def show_history(self, deposit_id):
        """Wyświetla historię zmian dla danego depozytu."""
        dialog = HistoryDialog(self.conn, deposit_id, parent=self)
        dialog.exec()

class LocationManagerDialog(QDialog):
    """Dialog do zarządzania lokalizacjami przechowywania opon."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Zarządzaj Lokalizacjami")
        self.layout = QVBoxLayout(self)

        self.location_list = QListWidget()
        self.layout.addWidget(self.location_list)

        # Przyciski
        self.button_layout = QHBoxLayout()
        self.add_button = QPushButton("Dodaj")
        self.add_button.clicked.connect(self.add_location)
        self.edit_button = QPushButton("Edytuj")
        self.edit_button.clicked.connect(self.edit_location)
        self.delete_button = QPushButton("Usuń")
        self.delete_button.clicked.connect(self.delete_location)
        self.set_default_button = QPushButton("Ustaw jako domyślną")
        self.set_default_button.clicked.connect(self.set_default_location)
        self.button_layout.addWidget(self.add_button)
        self.button_layout.addWidget(self.edit_button)
        self.button_layout.addWidget(self.delete_button)
        self.button_layout.addWidget(self.set_default_button)
        self.layout.addLayout(self.button_layout)

        self.load_locations()

    def load_locations(self):
        """Ładuje listę lokalizacji z bazy danych."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM locations ORDER BY name")
            locations = cursor.fetchall()
            self.locations_list_widget.clear()
            for location in locations:
                self.locations_list_widget.addItem(QListWidgetItem(location[0]))
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas ładowania lokalizacji:\n{e}")
            logger.error(f"Błąd podczas ładowania lokalizacji: {e}")


    def add_location(self):
        """Dodaje nową lokalizację do listy."""
        location_name, ok = QInputDialog.getText(self, "Dodaj lokalizację", "Podaj nazwę lokalizacji:")
        if ok and location_name.strip():
            try:
                cursor = self.conn.cursor()
                cursor.execute("INSERT INTO locations (name) VALUES (?)", (location_name.strip(),))
                self.conn.commit()
                self.load_locations()  # Przeładuj listę lokalizacji
                QMessageBox.information(self, "Sukces", "Lokalizacja została dodana.")
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "Błąd", "Lokalizacja o tej nazwie już istnieje.")
            except Exception as e:
                QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas dodawania lokalizacji:\n{e}")
                logger.error(f"Błąd podczas dodawania lokalizacji: {e}")


    def edit_location(self):
        """Edytuje wybraną lokalizację."""
        selected_item = self.location_list.currentItem()
        if selected_item:
            old_name = selected_item.text()
            new_name, ok = QInputDialog.getText(self, "Edytuj Lokalizację", "Nowa nazwa lokalizacji:", text=old_name)
            if ok and new_name:
                cursor = self.parent().conn.cursor()
                try:
                    cursor.execute("UPDATE locations SET name = ? WHERE name = ?", (new_name, old_name))
                    self.parent().conn.commit()
                    self.load_locations()
                except sqlite3.IntegrityError:
                    QMessageBox.warning(self, "Błąd", "Lokalizacja o tej nazwie już istnieje.")

    def delete_location(self):
        """Usuwa wybraną lokalizację."""
        selected_item = self.location_list.currentItem()
        if selected_item:
            name = selected_item.text()
            reply = QMessageBox.question(self, "Usuń Lokalizację", f"Czy na pewno chcesz usunąć lokalizację '{name}'?", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                cursor = self.parent().conn.cursor()
                cursor.execute("DELETE FROM locations WHERE name = ?", (name,))
                self.parent().conn.commit()
                self.load_locations()

    def set_default_location(self):
        """Ustawia wybraną lokalizację jako domyślną."""
        selected_item = self.location_list.currentItem()
        if selected_item:
            name = selected_item.text()
            cursor = self.parent().conn.cursor()
            cursor.execute("UPDATE locations SET is_default = 0")
            cursor.execute("UPDATE locations SET is_default = 1 WHERE name = ?", (name,))
            self.parent().conn.commit()
            self.load_locations()

class ClientVehiclesDialog(QDialog):
    """Dialog do wyświetlania pojazdów i depozytów klienta z dodatkowymi funkcjami."""

    def __init__(self, conn, client_id, client_name, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.client_id = client_id
        self.client_name = client_name
        self.setWindowTitle(f"Pojazdy i depozyty klienta: {client_name}")
        self.resize(900, 600)  # Ustawienia początkowego rozmiaru okna

        # Główne rozmieszczenie elementów
        self.layout = QVBoxLayout(self)

        # Górny panel z nazwą klienta i przyciskiem edycji
        header_layout = QHBoxLayout()
        self.client_label = QLabel(f"Klient: {self.client_name}")
        self.client_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(self.client_label)

        self.edit_client_button = QPushButton("Edytuj klienta")
        self.edit_client_button.clicked.connect(self.edit_client)
        header_layout.addWidget(self.edit_client_button)
        header_layout.setAlignment(self.edit_client_button, Qt.AlignRight)
        self.layout.addLayout(header_layout)

        # Informacje o kliencie
        self.client_info_label = QLabel()
        self.client_info_label.setWordWrap(True)
        self.layout.addWidget(self.client_info_label)

        # Tabela z depozytami klienta
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Pojazd", "Rejestracja", "Marka opon", "Rozmiar", "Status"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.open_context_menu)
        self.layout.addWidget(self.table)

        self.load_client_info()
        self.load_data()

    def load_client_info(self):
        """Ładowanie szczegółowych informacji o kliencie."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT phone_number, email, discount, barcode, additional_info
                FROM clients
                WHERE id = ?
            ''', (self.client_id,))
            client_data = cursor.fetchone()
            if client_data:
                phone, email, discount, barcode, additional_info = client_data
                info = f"Telefon: {phone or 'Brak'}\n"
                info += f"Email: {email or 'Brak'}\n"
                info += f"Rabat: {discount or 0}%\n"
                info += f"Kod kreskowy: {barcode or 'Brak'}\n"
                info += f"Dodatkowe informacje: {additional_info or 'Brak'}"
                self.client_info_label.setText(info)
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Błąd", f"Błąd podczas ładowania danych klienta: {e}")
            logger.error(f"Błąd podczas ładowania danych klienta: {e}")

    def load_data(self):
        """Ładowanie danych pojazdów i depozytów klienta."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT d.id, d.car_model, d.registration_number, d.tire_brand, d.tire_size, d.status
                FROM deposits d
                WHERE d.client_id = ?
            ''', (self.client_id,))
            rows = cursor.fetchall()

            self.table.setRowCount(0)  # Wyczyszczenie tabeli
            for row_idx, row_data in enumerate(rows):
                self.table.insertRow(row_idx)
                for col_idx, col_data in enumerate(row_data):
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(col_data)))
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Błąd", f"Błąd podczas ładowania danych: {e}")
            logger.error(f"Błąd podczas ładowania danych pojazdów i depozytów: {e}")

    def open_context_menu(self, position):
        """Otwiera menu kontekstowe dla tabeli depozytów."""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Brak zaznaczenia", "Nie zaznaczono żadnej pozycji.")
            return

        deposit_id = int(self.table.item(selected_row, 0).text())

        menu = QMenu(self)

        toggle_status_action = QAction("Oznacz jako aktywny" if self.table.item(selected_row, 5).text() == "Wydany" else "Oznacz jako wydany", self)
        toggle_status_action.triggered.connect(lambda: self.toggle_deposit_status(deposit_id))
        menu.addAction(toggle_status_action)

        edit_action = QAction("Edytuj depozyt", self)
        edit_action.triggered.connect(lambda: self.edit_deposit(deposit_id))
        menu.addAction(edit_action)

        delete_action = QAction("Usuń depozyt", self)
        delete_action.triggered.connect(lambda: self.delete_deposit(deposit_id))
        menu.addAction(delete_action)

        generate_label_action = QAction("Generuj etykietę", self)
        generate_label_action.triggered.connect(lambda: self.generate_label(deposit_id))
        menu.addAction(generate_label_action)

        generate_confirmation_action = QAction("Generuj potwierdzenie", self)
        generate_confirmation_action.triggered.connect(lambda: self.generate_confirmation(deposit_id))
        menu.addAction(generate_confirmation_action)

        menu.exec(self.table.viewport().mapToGlobal(position))

    def toggle_deposit_status(self, deposit_id):
        """Przełącza status depozytu między 'Aktywny' a 'Wydany'."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT status FROM deposits WHERE id = ?", (deposit_id,))
            current_status = cursor.fetchone()[0]
            new_status = "Aktywny" if current_status == "Wydany" else "Wydany"

            cursor.execute("UPDATE deposits SET status = ? WHERE id = ?", (new_status, deposit_id))
            self.conn.commit()

            QMessageBox.information(self, "Sukces", f"Status depozytu został zmieniony na: {new_status}")
            self.load_data()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Błąd", f"Błąd podczas zmiany statusu: {e}")
            logger.error(f"Błąd podczas zmiany statusu depozytu: {e}")

    def generate_label(self, deposit_id):
        """Generuje etykietę dla depozytu."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT car_model, registration_number, tire_brand, tire_size
                FROM deposits
                WHERE id = ?
            ''', (deposit_id,))
            deposit = cursor.fetchone()
            if not deposit:
                QMessageBox.warning(self, "Błąd", "Nie znaleziono depozytu.")
                return

            label_content = f"Etykieta depozytu:\n\nPojazd: {deposit[0]}\nRejestracja: {deposit[1]}\nMarka opon: {deposit[2]}\nRozmiar opon: {deposit[3]}"
            file_path = QFileDialog.getSaveFileName(self, "Zapisz etykietę", "", "Pliki PDF (*.pdf)")[0]
            if file_path:
                generate_pdf(file_path, label_content)
                QMessageBox.information(self, "Sukces", f"Etykieta została zapisana w: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd podczas generowania etykiety: {e}")
            logger.error(f"Błąd podczas generowania etykiety: {e}")

    def generate_confirmation(self, deposit_id):
        """Generuje potwierdzenie dla depozytu."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT car_model, registration_number, tire_brand, tire_size, status
                FROM deposits
                WHERE id = ?
            ''', (deposit_id,))
            deposit = cursor.fetchone()
            if not deposit:
                QMessageBox.warning(self, "Błąd", "Nie znaleziono depozytu.")
                return

            confirmation_content = f"Potwierdzenie depozytu:\n\nPojazd: {deposit[0]}\nRejestracja: {deposit[1]}\nMarka opon: {deposit[2]}\nRozmiar opon: {deposit[3]}\nStatus: {deposit[4]}"
            file_path = QFileDialog.getSaveFileName(self, "Zapisz potwierdzenie", "", "Pliki PDF (*.pdf)")[0]
            if file_path:
                generate_pdf(file_path, confirmation_content)
                QMessageBox.information(self, "Sukces", f"Potwierdzenie zostało zapisane w: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd podczas generowania potwierdzenia: {e}")
            logger.error(f"Błąd podczas generowania potwierdzenia: {e}")
    def edit_deposit(self, deposit_id):
        """Edytuje depozyt."""
        dialog = DepositDialog(self.conn, deposit_id=deposit_id, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.load_data()

    def delete_deposit(self, deposit_id):
        """Usuwa depozyt."""
        confirmation = QMessageBox.question(self, "Potwierdzenie usunięcia", "Czy na pewno chcesz usunąć ten depozyt?")
        if confirmation == QMessageBox.Yes:
            try:
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM deposits WHERE id = ?", (deposit_id,))
                self.conn.commit()
                QMessageBox.information(self, "Sukces", "Depozyt został usunięty.")
                self.load_data()
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Błąd", f"Błąd podczas usuwania depozytu: {e}")
                logger.error(f"Błąd podczas usuwania depozytu: {e}")

    def edit_client(self):
        """Edytuje dane klienta."""
        dialog = EditClientDialog(self.conn, client_id=self.client_id, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.load_client_info()
            QMessageBox.information(self, "Sukces", "Dane klienta zostały zaktualizowane.")

class HistoryDialog(QDialog):
    """Dialog wyświetlający historię zmian dla depozytu."""
    def __init__(self, conn, deposit_id, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.deposit_id = deposit_id
        self.setWindowTitle("Historia depozytu")
        self.resize(600, 400)
        self.layout = QVBoxLayout(self)

        self.table_history = QTableWidget()
        self.table_history.setColumnCount(4)
        self.table_history.setHorizontalHeaderLabels(["Data zmiany", "Użytkownik", "Opis", "ID"])
        self.table_history.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_history.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_history.horizontalHeader().setStretchLastSection(True)
        self.table_history.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.table_history)

        self.load_history()

    def load_history(self):
        """Ładuje historię zmian dla depozytu."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT change_date, user, description, id
                FROM history
                WHERE deposit_id = ?
                ORDER BY change_date DESC
            ''', (self.deposit_id,))
            rows = cursor.fetchall()

            self.table_history.setRowCount(len(rows))
            for row_idx, row in enumerate(rows):
                for col_idx, value in enumerate(row):
                    item = QTableWidgetItem(str(value))
                    self.table_history.setItem(row_idx, col_idx, item)
        except Exception as e:
            error_code = traceback.format_exc()
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas ładowania historii.\nKod błędu:\n{error_code}")
            logger.error(f"Błąd podczas ładowania historii: {e}")

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Ustawienia Aplikacji")
        self.layout = QVBoxLayout(self)

        self.form_layout = QFormLayout()

        # Kopia zapasowa
        self.backup_button = QPushButton("Utwórz kopię zapasową")
        self.backup_button.clicked.connect(self.parent.create_backup)
        self.form_layout.addRow("Kopia zapasowa:", self.backup_button)

        self.import_backup_button = QPushButton("Importuj kopię zapasową")
        self.import_backup_button.clicked.connect(self.import_backup)
        self.form_layout.addRow("Import kopii zapasowej:", self.import_backup_button)

        # Folder kopii zapasowych
        self.backup_folder_input = QLineEdit()
        self.backup_folder_input.setText(self.parent.backup_folder)
        self.form_layout.addRow("Folder kopii zapasowych:", self.backup_folder_input)

        # Domyślna lokalizacja
        self.default_location_input = QLineEdit()
        self.form_layout.addRow("Domyślna lokalizacja:", self.default_location_input)

        # Nazwa firmy
        self.company_name_input = QLineEdit()
        self.form_layout.addRow("Nazwa firmy:", self.company_name_input)

        # Adres firmy
        self.company_address_input = QLineEdit()
        self.form_layout.addRow("Adres firmy:", self.company_address_input)

        # Kontakt firmy
        self.company_contact_input = QLineEdit()
        self.form_layout.addRow("Kontakt firmy:", self.company_contact_input)

        # Logo firmy
        self.company_logo_input = QLineEdit()
        self.form_layout.addRow("Logo firmy:", self.company_logo_input)
        self.logo_button = QPushButton("Wybierz logo")
        self.logo_button.clicked.connect(self.choose_logo)
        self.form_layout.addRow("", self.logo_button)

        # Automatyczny wydruk
        self.auto_print_checkbox = QComboBox()
        self.auto_print_checkbox.addItems(["Nie", "Tak"])
        self.form_layout.addRow("Automatyczny wydruk:", self.auto_print_checkbox)

        # Edycja szablonów
        self.edit_templates_button = QPushButton("Edytuj szablony")
        self.edit_templates_button.clicked.connect(self.edit_templates)
        self.form_layout.addRow("Szablony:", self.edit_templates_button)

        self.layout.addLayout(self.form_layout)

        # Przyciski akcji
        self.button_layout = QHBoxLayout()
        self.save_button = QPushButton("Zapisz")
        self.save_button.clicked.connect(self.save_settings)
        self.cancel_button = QPushButton("Anuluj")
        self.cancel_button.clicked.connect(self.reject)
        self.button_layout.addWidget(self.save_button)
        self.button_layout.addWidget(self.cancel_button)
        self.layout.addLayout(self.button_layout)

        self.load_settings()

    def choose_logo(self):
        """Wybiera logo firmy."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Wybierz logo", "", "Images (*.png *.jpg *.jpeg)")
        if file_path:
            self.company_logo_input.setText(file_path)

    def edit_templates(self):
        """Otwiera okno do edycji szablonów."""
        dialog = TemplatesEditorDialog(self)
        dialog.exec()

    def load_settings(self):
        """Ładuje ustawienia z bazy danych."""
        cursor = self.parent.conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        settings = dict(cursor.fetchall())

        self.company_name_input.setText(settings.get('company_name', ''))
        self.company_address_input.setText(settings.get('company_address', ''))
        self.company_contact_input.setText(settings.get('company_contact', ''))
        self.company_logo_input.setText(settings.get('company_logo', ''))
        self.default_location_input.setText(settings.get('default_location', ''))
        self.auto_print_checkbox.setCurrentText("Tak" if settings.get('auto_print', 'False') == 'True' else "Nie")

    def save_settings(self):
        """Zapisuje ustawienia aplikacji."""
        company_name = self.company_name_input.text()
        company_address = self.company_address_input.text()
        company_contact = self.company_contact_input.text()
        company_logo = self.company_logo_input.text()
        default_location = self.default_location_input.text()
        backup_folder = self.backup_folder_input.text().strip()
        auto_print = self.auto_print_checkbox.currentText() == "Tak"

        # Upewnienie się, że default_printer i label_printer są poprawnie zainicjalizowane
        default_printer = getattr(self.parent, 'default_printer', '')
        label_printer = getattr(self.parent, 'label_printer', '')

        try:
            cursor = self.parent.conn.cursor()
            settings = {
                'company_name': company_name,
                'company_address': company_address,
                'company_contact': company_contact,
                'company_logo': company_logo,
                'default_location': default_location,
                'backup_folder': backup_folder,
                'auto_print': str(auto_print),
                'default_printer': default_printer,
                'label_printer': label_printer,
            }

            for key, value in settings.items():
                cursor.execute('''
                    INSERT INTO settings (key, value)
                    VALUES (?, ?)
                    ON CONFLICT(key) DO UPDATE SET value=excluded.value
                ''', (key, value))

            self.parent.conn.commit()
            self.parent.load_settings()
            QMessageBox.information(self, "Ustawienia", "Ustawienia zostały zaktualizowane.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas zapisywania ustawień aplikacji.\nKod błędu:\n{e}")
            logger.error(f"Błąd podczas zapisywania ustawień aplikacji: {e}")

    def import_backup(self):
        """Importuje kopię zapasową bazy danych."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Wybierz plik kopii zapasowej", "", "Baza danych (*.db)")
        if file_path:
            try:
                confirm = QMessageBox.question(
                    self,
                    "Potwierdzenie importu",
                    "Czy na pewno chcesz zastąpić obecną bazę danych wybraną kopią zapasową?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if confirm == QMessageBox.Yes:
                    current_db_path = self.parent.conn.database
                    self.parent.conn.close()
                    shutil.copy(file_path, current_db_path)
                    self.parent.conn = sqlite3.connect(current_db_path)
                    self.parent.load_settings()
                    QMessageBox.information(self, "Sukces", "Kopia zapasowa została zaimportowana pomyślnie.")
            except Exception as e:
                QMessageBox.critical(self, "Błąd", f"Nie udało się zaimportować kopii zapasowej:\n{e}")
                logger.error(f"Błąd podczas importu kopii zapasowej: {e}")



class TemplatesEditorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edycja Szablonów")
        self.resize(800, 600)
        self.layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        self.label_template_editor = QTextEdit()
        self.confirmation_template_editor = QTextEdit()

        self.load_templates()

        self.tabs.addTab(self.label_template_editor, "Szablon Etykiety")
        self.tabs.addTab(self.confirmation_template_editor, "Szablon Potwierdzenia")

        # Przyciski
        self.button_layout = QHBoxLayout()
        self.save_button = QPushButton("Zapisz szablony")
        self.save_button.clicked.connect(self.save_templates)
        self.cancel_button = QPushButton("Anuluj")
        self.cancel_button.clicked.connect(self.reject)
        self.button_layout.addWidget(self.save_button)
        self.button_layout.addWidget(self.cancel_button)
        self.layout.addLayout(self.button_layout)

    def load_templates(self):
        """Wczytuje zawartość szablonów."""
        label_template_path = resource_path(os.path.join("templates", "label_template.html"))
        confirmation_template_path = resource_path(os.path.join("templates", "confirmation_template.html"))

        if os.path.exists(label_template_path):
            with open(label_template_path, 'r', encoding='utf-8') as f:
                self.label_template_editor.setPlainText(f.read())
        else:
            self.label_template_editor.setPlainText("")

        if os.path.exists(confirmation_template_path):
            with open(confirmation_template_path, 'r', encoding='utf-8') as f:
                self.confirmation_template_editor.setPlainText(f.read())
        else:
            self.confirmation_template_editor.setPlainText("")

    def save_templates(self):
        """Zapisuje zmiany w szablonach."""
        label_template_path = resource_path(os.path.join("templates", "label_template.html"))
        confirmation_template_path = resource_path(os.path.join("templates", "confirmation_template.html"))

        with open(label_template_path, 'w', encoding='utf-8') as f:
            f.write(self.label_template_editor.toPlainText())

        with open(confirmation_template_path, 'w', encoding='utf-8') as f:
            f.write(self.confirmation_template_editor.toPlainText())

        QMessageBox.information(self, "Szablony", "Szablony zostały zapisane.")
        self.accept()

class LogViewerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Podgląd Logów")
        self.resize(800, 600)
        self.layout = QVBoxLayout(self)

        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.layout.addWidget(self.log_text)

        self.load_logs()

    def load_logs(self):
        """Wczytuje zawartość pliku logów."""
        log_file_path = os.path.join(APP_DATA_DIR, "application.log")
        if not os.path.exists(log_file_path):
            self.logs_view.setPlainText("Brak logów do wyświetlenia.")
            return

        try:
            with open(log_file_path, "r", encoding="utf-8") as log_file:
                self.logs_view.setPlainText(log_file.read())
        except Exception as e:
            logger.error(f"Błąd podczas wczytywania logów: {e}")
            self.logs_view.setPlainText(f"Błąd podczas wczytywania logów:\n{e}")


    def show_logs(self):
        log_file_path = LOG_FILE  # Upewnij się, że LOG_FILE jest poprawnie zdefiniowany
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r', encoding='utf-8') as log_file:
                logs = log_file.read()
            self.logs_text_edit.setPlainText(logs)  # Upewnij się, że `logs_text_edit` jest poprawnie zainicjalizowany
        else:
            self.logs_text_edit.setPlainText("Brak logów do wyświetlenia.")


class SendEmailDialog(QDialog):
    """Dialog do wysyłania e-maila do klienta."""
    def __init__(self, conn, email, client_name, expected_return_date, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.email = email
        self.client_name = client_name
        self.expected_return_date = expected_return_date
        self.setWindowTitle("Wyślij e-mail do klienta")
        self.resize(600, 400)
        self.layout = QVBoxLayout(self)

        self.form_layout = QFormLayout()
        self.email_input = QLineEdit(email)
        self.form_layout.addRow("Do:", self.email_input)

        self.template_combo = QComboBox()
        self.load_templates()
        self.template_combo.currentIndexChanged.connect(self.load_template)
        self.form_layout.addRow("Szablon:", self.template_combo)

        self.subject_input = QLineEdit()
        self.form_layout.addRow("Temat:", self.subject_input)

        self.body_input = QTextEdit()
        self.form_layout.addRow("Treść:", self.body_input)

        self.layout.addLayout(self.form_layout)

        # Przyciski
        self.button_layout = QHBoxLayout()
        self.send_button = QPushButton("Wyślij")
        self.send_button.clicked.connect(self.send_email)
        self.cancel_button = QPushButton("Anuluj")
        self.cancel_button.clicked.connect(self.reject)
        self.button_layout.addWidget(self.send_button)
        self.button_layout.addWidget(self.cancel_button)
        self.layout.addLayout(self.button_layout)

    def load_templates(self):
        """Ładuje listę szablonów e-mail."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM email_templates")
        templates = cursor.fetchall()
        self.template_combo.clear()
        self.template_combo.addItem("Brak szablonu")
        for template in templates:
            self.template_combo.addItem(template[0])

    def load_template(self):
        """Ładuje wybrany szablon e-mail."""
        template_name = self.template_combo.currentText()
        if template_name == "Brak szablonu":
            self.subject_input.clear()
            self.body_input.clear()
            return
        cursor = self.conn.cursor()
        cursor.execute("SELECT subject, body FROM email_templates WHERE name = ?", (template_name,))
        template = cursor.fetchone()
        if template:
            subject = template[0].replace("{client_name}", self.client_name).replace("{expected_return_date}", self.expected_return_date)
            body = template[1].replace("{client_name}", self.client_name).replace("{expected_return_date}", self.expected_return_date)
            self.subject_input.setText(subject)
            self.body_input.setPlainText(body)

    def send_email(self):
        """Wysyła e-mail do klienta."""
        to_address = self.email_input.text()
        subject = self.subject_input.text()
        body = self.body_input.toPlainText()

        # Implementacja wysyłania e-maila
        try:
            settings = self.parent().email_settings
            from_address = settings['email_address']
            password = settings['email_password']
            smtp_server = settings['smtp_server']
            smtp_port = settings['smtp_port']

            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = from_address
            msg['To'] = to_address

            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            server.login(from_address, password)
            server.sendmail(from_address, [to_address], msg.as_string())
            server.quit()

            # Zapisanie historii e-maili
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO email_history (to_address, subject, body, sent_date)
                VALUES (?, ?, ?, ?)
            ''', (to_address, subject, body, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            self.conn.commit()

            QMessageBox.information(self, "E-mail", "E-mail został wysłany.")
            self.accept()
        except Exception as e:
            logger.error(f"Błąd podczas wysyłania e-maila: {e}")
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd podczas wysyłania e-maila.\n{e}")

class EmailSettingsDialog(QDialog):
    """Dialog do ustawień e-mail."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ustawienia E-mail")
        self.layout = QVBoxLayout(self)

        self.form_layout = QFormLayout()
        self.email_address_input = QLineEdit()
        self.form_layout.addRow("Adres e-mail:", self.email_address_input)

        self.email_password_input = QLineEdit()
        self.email_password_input.setEchoMode(QLineEdit.Password)
        self.form_layout.addRow("Hasło e-mail:", self.email_password_input)

        self.smtp_server_input = QLineEdit()
        self.form_layout.addRow("Serwer SMTP:", self.smtp_server_input)

        self.smtp_port_input = QLineEdit("465")
        self.form_layout.addRow("Port SMTP:", self.smtp_port_input)

        self.layout.addLayout(self.form_layout)

        # Przyciski
        self.button_layout = QHBoxLayout()
        self.save_button = QPushButton("Zapisz")
        self.save_button.clicked.connect(self.save_email_settings)
        self.cancel_button = QPushButton("Anuluj")
        self.cancel_button.clicked.connect(self.reject)
        self.button_layout.addWidget(self.save_button)
        self.button_layout.addWidget(self.cancel_button)
        self.layout.addLayout(self.button_layout)

        self.load_email_settings()

    def load_email_settings(self):
        """Ładuje ustawienia e-mail."""
        settings = self.parent().email_settings
        self.email_address_input.setText(settings.get('email_address', ''))
        self.email_password_input.setText(settings.get('email_password', ''))
        self.smtp_server_input.setText(settings.get('smtp_server', ''))
        self.smtp_port_input.setText(settings.get('smtp_port', '465'))

    def save_email_settings(self):
        """Zapisuje ustawienia e-mail."""
        email_address = self.email_address_input.text()
        email_password = self.email_password_input.text()
        smtp_server = self.smtp_server_input.text()
        smtp_port = self.smtp_port_input.text()

        cursor = self.parent().conn.cursor()
        settings = {
            'email_address': email_address,
            'email_password': email_password,
            'smtp_server': smtp_server,
            'smtp_port': smtp_port
        }
        for key, value in settings.items():
            cursor.execute('''
                INSERT INTO settings (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
            ''', (key, value))
        self.parent().conn.commit()
        self.parent().email_settings = settings
        QMessageBox.information(self, "Ustawienia e-mail", "Ustawienia e-mail zostały zapisane.")
        self.accept()

    def create_default_email_template(conn):
        """Tworzy domyślny szablon e-mail, jeśli nie istnieje."""
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM email_templates")
            count = cursor.fetchone()[0]
            if count == 0:
                cursor.execute('''
                    INSERT INTO email_templates (name, subject, body)
                    VALUES (?, ?, ?)
                ''', (
                    "Przypomnienie o zwrocie",
                    "Przypomnienie o zwrocie opon",
                    "Szanowny/a {client_name},\n\nPrzypominamy o oczekiwanym zwrocie opon do dnia {expected_return_date}.\n\nPozdrawiamy,\n{company_name}"
                ))
                conn.commit()
                logger.info("Dodano domyślny szablon e-mail.")
        except Exception as e:
            logger.error(f"Błąd podczas tworzenia domyślnego szablonu e-mail: {e}")

class EmailHistoryDialog(QDialog):
    """Dialog do wyświetlania historii wysłanych e-maili."""
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.setWindowTitle("Historia wysłanych e-maili")
        self.resize(800, 600)
        self.layout = QVBoxLayout(self)

        self.table_emails = QTableWidget()
        self.table_emails.setColumnCount(4)
        self.table_emails.setHorizontalHeaderLabels([
            "Data wysłania", "Adresat", "Temat", "Treść"
        ])
        self.table_emails.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_emails.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_emails.horizontalHeader().setStretchLastSection(True)
        self.table_emails.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.table_emails)

        self.load_email_history()

    def load_email_history(self):
        """Ładuje historię wysłanych e-maili."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT sent_date, to_address, subject, body
                FROM email_history
                ORDER BY sent_date DESC
            ''')
            rows = cursor.fetchall()

            self.table_emails.setRowCount(len(rows))
            for row_idx, row in enumerate(rows):
                for col_idx, value in enumerate(row):
                    item = QTableWidgetItem(str(value))
                    self.table_emails.setItem(row_idx, col_idx, item)
        except Exception as e:
            logger.error(f"Błąd podczas ładowania historii e-maili: {e}")

class EmailTemplateManagerDialog(QDialog):
    """Dialog do zarządzania szablonami e-mail i SMS."""
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.setWindowTitle("Szablony wiadomości")
        self.resize(600, 400)
        self.layout = QVBoxLayout(self)

        self.template_list = QListWidget()
        self.template_list.itemClicked.connect(self.load_template)
        self.layout.addWidget(self.template_list)

        self.form_layout = QFormLayout()
        self.template_name_input = QLineEdit()
        self.form_layout.addRow("Nazwa szablonu:", self.template_name_input)

        self.subject_input = QLineEdit()
        self.form_layout.addRow("Temat:", self.subject_input)

        self.body_input = QTextEdit()
        self.form_layout.addRow("Treść:", self.body_input)

        self.layout.addLayout(self.form_layout)

        # Przyciski
        self.button_layout = QHBoxLayout()
        self.save_button = QPushButton("Zapisz")
        self.save_button.clicked.connect(self.save_template)
        self.delete_button = QPushButton("Usuń")
        self.delete_button.clicked.connect(self.delete_template)
        self.button_layout.addWidget(self.save_button)
        self.button_layout.addWidget(self.delete_button)
        self.layout.addLayout(self.button_layout)

        self.load_templates()

    def load_templates(self):
        """Ładuje listę szablonów."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM email_templates")
        templates = cursor.fetchall()
        self.template_list.clear()
        for template in templates:
            self.template_list.addItem(template[0])

    def load_template(self, item):
        """Ładuje wybrany szablon do formularza."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT subject, body FROM email_templates WHERE name = ?", (item.text(),))
        template = cursor.fetchone()
        if template:
            self.template_name_input.setText(item.text())
            self.subject_input.setText(template[0])
            self.body_input.setPlainText(template[1])

    def save_template(self):
        """Zapisuje szablon do bazy danych."""
        name = self.template_name_input.text()
        subject = self.subject_input.text()
        body = self.body_input.toPlainText()
        if not name:
            QMessageBox.warning(self, "Błąd", "Musisz podać nazwę szablonu.")
            return
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO email_templates (name, subject, body)
            VALUES (?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET subject=excluded.subject, body=excluded.body
        ''', (name, subject, body))
        self.conn.commit()
        self.load_templates()
        QMessageBox.information(self, "Szablony", "Szablon został zapisany.")

    def delete_template(self):
        """Usuwa wybrany szablon."""
        name = self.template_name_input.text()
        if not name:
            QMessageBox.warning(self, "Błąd", "Musisz wybrać szablon do usunięcia.")
            return
        reply = QMessageBox.question(self, "Usuń szablon", f"Czy na pewno chcesz usunąć szablon '{name}'?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM email_templates WHERE name = ?", (name,))
            self.conn.commit()
            self.load_templates()
            self.template_name_input.clear()
            self.subject_input.clear()
            self.body_input.clear()
            QMessageBox.information(self, "Szablony", "Szablon został usunięty.")

class PrinterSettingsDialog(QDialog):
    """Dialog do ustawień drukarki."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ustawienia Drukarki")
        self.layout = QVBoxLayout(self)

        self.form_layout = QFormLayout()
        self.default_printer_input = QLineEdit()
        self.form_layout.addRow("Domyślna drukarka:", self.default_printer_input)

        self.label_printer_input = QLineEdit()
        self.form_layout.addRow("Drukarka etykiet Niimbot B1:", self.label_printer_input)

        self.layout.addLayout(self.form_layout)

        # Przyciski
        self.button_layout = QHBoxLayout()
        self.save_button = QPushButton("Zapisz")
        self.save_button.clicked.connect(self.save_printer_settings)
        self.cancel_button = QPushButton("Anuluj")
        self.cancel_button.clicked.connect(self.reject)
        self.button_layout.addWidget(self.save_button)
        self.button_layout.addWidget(self.cancel_button)
        self.layout.addLayout(self.button_layout)

        self.load_printer_settings()

    def load_printer_settings(self):
        """Ładuje ustawienia drukarki."""
        settings = self.parent().email_settings  # Możesz dostosować to do swoich potrzeb
        self.default_printer_input.setText(settings.get('default_printer', ''))
        self.label_printer_input.setText(settings.get('label_printer', ''))

    def save_printer_settings(self):
        """Zapisuje ustawienia drukarki."""
        default_printer = self.default_printer_input.text()
        label_printer = self.label_printer_input.text()

        cursor = self.parent().conn.cursor()
        settings = {
            'default_printer': default_printer,
            'label_printer': label_printer
        }
        for key, value in settings.items():
            cursor.execute('''
                INSERT INTO settings (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
            ''', (key, value))
        self.parent().conn.commit()
        self.accept()

class DepositDetailsDialog(QDialog):
    """Dialog wyświetlający szczegóły depozytu."""
    def __init__(self, conn, deposit_id, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.deposit_id = deposit_id
        self.setWindowTitle("Szczegóły Depozytu")
        self.layout = QVBoxLayout(self)

        # Pobierz dane depozytu
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT deposits.*, clients.name, clients.phone_number, clients.email
            FROM deposits
            INNER JOIN clients ON deposits.client_id = clients.id
            WHERE deposits.id = ?
        ''', (self.deposit_id,))
        deposit = cursor.fetchone()
        if deposit:
            deposit_info = {
                'ID': deposit[0],
                'Klient': deposit[-3],
                'Telefon': deposit[-2],
                'E-mail': deposit[-1],
                'Model auta': deposit[2],
                'Nr rejestracyjny': deposit[3],
                'Marka opon': deposit[4],
                'Rozmiar opon': deposit[5],
                'Ilość': deposit[6],
                'Lokalizacja': deposit[7],
                'Mycie': 'Tak' if deposit[8] else 'Nie',
                'Konserwacja': 'Tak' if deposit[9] else 'Nie',
                'Data depozytu': deposit[10],
                'Data wydania': deposit[11],
                'Status': deposit[12],
                'Czas trwania (dni)': deposit[13],
                'Sezon': deposit[14],
                'Oczekiwany zwrot': deposit[15],
                'Stan techniczny': deposit[16],
                'Data przechowywania': deposit[17],
                'Cena': deposit[18],
            }
            # Wyświetl dane w formularzu
            form_layout = QFormLayout()
            for key, value in deposit_info.items():
                form_layout.addRow(QLabel(f"<b>{key}:</b>"), QLabel(str(value)))
            self.layout.addLayout(form_layout)

            # Przyciski
            button_layout = QHBoxLayout()
            close_button = QPushButton("Zamknij")
            close_button.clicked.connect(self.close)
            button_layout.addWidget(close_button)
            self.layout.addLayout(button_layout)
        else:
            QMessageBox.warning(self, "Błąd", "Nie znaleziono danych depozytu.")
            self.close()


# Główna pętla aplikacji
if __name__ == "__main__":
    ensure_database_exists()
    deposit_manager = DepositManager()
    deposit_manager.show()
    sys.exit(app.exec())
