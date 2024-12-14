import os
import sqlite3
from PySide6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton
from niimprint.printer import PrinterClient
from niimprint import SerialTransport
from PIL import Image, ImageDraw, ImageFont
from PySide6.QtGui import QPixmap
import logging

logger = logging.getLogger("TireDepositManager")

class NiimbotPrinterManager:
    def __init__(self, db_path, serial_port='COM3'):
        self.conn = sqlite3.connect(db_path)
        self.serial_port = serial_port

    def print_label_with_niimbot(self, file_path):
        """Drukuje etykietę za pomocą drukarki Niimbot."""
        try:
            transport = SerialTransport(port=self.serial_port)
            client = PrinterClient(transport)
            image = Image.open(file_path)

            client.set_dimension(image.width, image.height)
            client.print_image(image)
            client.end_print()

            QMessageBox.information(None, "Sukces", "Etykieta została wydrukowana na drukarce Niimbot.")
        except Exception as e:
            logger.error(f"Błąd podczas drukowania etykiety Niimbot: {e}")
            QMessageBox.critical(None, "Błąd", f"Wystąpił błąd podczas drukowania etykiety Niimbot:\n{e}")

    def generate_label_image(self, text, output_file="label.png", width=384, height=640):
        """
        Generuje obraz etykiety z tekstem w pionowej orientacji.
        """
        try:
            # Tworzymy pusty obraz w orientacji pionowej
            image = Image.new("RGB", (width, height), "white")
            draw = ImageDraw.Draw(image)

            # Ustawienia czcionki
            font_size = 30  # Dostosuj rozmiar czcionki
            font_path = "arial.ttf"  # Upewnij się, że plik czcionki jest dostępny
            font = ImageFont.truetype(font_path, font_size)

            # Rysowanie tekstu linia po linii
            text_lines = text.split("\n")
            x_margin = 20  # Margines poziomy
            y_margin = 20  # Margines pionowy
            line_spacing = font_size + 10  # Odstęp między liniami

            y_position = y_margin
            for line in text_lines:
                draw.text((x_margin, y_position), line, fill="black", font=font)
                y_position += line_spacing

            # Zapisujemy obraz jako plik PNG
            image.save(output_file)
            logger.info(f"Etykieta wygenerowana jako {output_file}")
            logger.info(f"Wymiary wygenerowanego obrazu: {image.size}")
            return output_file
        except Exception as e:
            logger.error(f"Błąd podczas generowania obrazu etykiety: {e}")
            raise


    def show_preview_and_print(self, label_content):
        """Wyświetla okno podglądu etykiety z opcją drukowania."""
        try:
            output_file = self.generate_label_image(label_content)

            class PreviewDialog(QDialog):
                def __init__(self, image_path, print_callback, parent=None):
                    super().__init__(parent)
                    self.setWindowTitle("Podgląd etykiety")
                    self.layout = QVBoxLayout()

                    # Wyświetlenie podglądu etykiety
                    self.image_label = QLabel()
                    self.image_label.setPixmap(QPixmap(image_path))
                    self.layout.addWidget(self.image_label)

                    # Przyciski akcji
                    self.print_button = QPushButton("Drukuj")
                    self.cancel_button = QPushButton("Anuluj")

                    self.print_button.clicked.connect(print_callback)
                    self.cancel_button.clicked.connect(self.reject)

                    self.layout.addWidget(self.print_button)
                    self.layout.addWidget(self.cancel_button)
                    self.setLayout(self.layout)

            def print_action():
                self.print_label_with_niimbot(output_file)

            dialog = PreviewDialog(output_file, print_action)
            dialog.exec()

        except Exception as e:
            logger.error(f"Błąd podczas wyświetlania podglądu etykiety: {e}")
            QMessageBox.critical(None, "Błąd", f"Wystąpił błąd podczas wyświetlania podglądu etykiety:\n{e}")


# Przykład użycia
if __name__ == "__main__":
    db_path = "tire_deposits.db"
    printer_manager = NiimbotPrinterManager(db_path=db_path, serial_port="COM3")
    label_text = (
        "Klient: Jan Kowalski\n"
        "Marka: Michelin\n"
        "Rozmiar: 205/55 R16\n"
        "Ilość: 4"
    )
    printer_manager.show_preview_and_print(label_text)
