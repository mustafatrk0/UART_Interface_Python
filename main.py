# Author   : MUSTAFA ERGÜL

import asyncio
import time
import serial
from typing import Iterator, Tuple
from serial.tools.list_ports import comports
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QWidget, QLabel, QComboBox, QGridLayout, \
    QPushButton, QMessageBox, QApplication, QLineEdit, QPlainTextEdit
from PyQt5.QtGui import QCloseEvent, QIcon, QPixmap, QFont
from quamash import QEventLoop
from datetime import datetime
from PyQt5 import QtCore

kayit = open("kayit.txt", "a")

# Object for access to the serial port
ser = serial.Serial(timeout=0)
SER_BAUDRATE = 115200

# Setting constants
SETTING_PORT_NAME = 'port_name'
SETTING_MESSAGE = 'message'



def gen_serial_ports() -> Iterator[Tuple[str, str]]:
    """Mevcut tüm seri bağlantı noktalarını çalıştır."""
    ports = comports()
    return ((p.description, p.device) for p in ports)


def send_serial_async(msg: str) -> None:
    """Seri bağlantı noktasına (async) bir mesaj gönderin."""
    ser.write(msg.encode())


# noinspection PyArgumentList
class RemoteWidget(QWidget):
    """Main Widget."""

    def __init__(self, parent: QWidget=None) -> None:
        super().__init__(parent)

        # Port Combobox
        self.port_label = QLabel(self.tr('COM Port:'))
        self.port_combobox = QComboBox()
        self.port_label.setBuddy(self.port_combobox)
        self.update_com_ports()
        self.port_combobox.setFont(QFont('Arial', 14))

        self.setWindowIcon(QIcon("iconvolt.jpg"))

        self.labelImage = QLabel(self)
        pixmap = QPixmap("voltay.jpeg")
        self.labelImage.setPixmap(pixmap)
        self.labelImage.setAlignment(QtCore.Qt.AlignCenter)



        # Connect and Disconnect Buttons
        self.connect_btn = QPushButton(self.tr('Bağlan'))
        self.disconnect_btn = QPushButton(self.tr('Bağlantı Kapat'))
        self.connect_btn.setFont(QFont('Arial', 14))
        self.disconnect_btn.setFont(QFont('Arial', 14))
        self.disconnect_btn.setVisible(False)
        self.connect_btn.pressed.connect(self.on_connect_btn_pressed)
        self.disconnect_btn.pressed.connect(self.on_disconnect_btn_pressed)

        # message line edit
        self.msg_label = QLabel(self.tr('Mesaj:'))
        self.msg_lineedit = QLineEdit()
        self.msg_label.setBuddy(self.msg_label)
        self.msg_lineedit.setEnabled(False)
        self.msg_lineedit.returnPressed.connect(self.on_send_btn_pressed)

        # send message button
        self.send_btn = QPushButton(self.tr('Gönder'))
        self.send_btn.setEnabled(False)
        self.send_btn.pressed.connect(self.on_send_btn_pressed)


        # received messages
        self.received_label = QLabel(self.tr('Alınan Veri:'))
        self.received_textedit = QPlainTextEdit()
        self.received_textedit.setReadOnly(True)
        self.received_label.setBuddy(self.received_textedit)

        self.vlt_label = QLabel(self.tr('VOLTA TEAM'))
        self.data_label = QLabel(self.tr('|     Saat     | Toplam Süre (ms) | Hız(km/h | Batarya Sıcaklığı(°C) | Batarya Gerilimi(V) | Kalan Enerji(Wh) |'))
        self.data_label.setFont(QFont('Arial', 14))

        # Arrange Layout
        layout = QGridLayout()
        layout.addWidget(self.labelImage, 0,0,1,3)
        layout.addWidget(self.port_label, 1, 0)
        layout.addWidget(self.port_combobox, 1, 0,1,2)
        layout.addWidget(self.connect_btn, 1, 2)
        layout.addWidget(self.disconnect_btn, 1, 2)
        #layout.addWidget(self.msg_label, 2, 0)
        #layout.addWidget(self.msg_lineedit, 2, 1)
        #layout.addWidget(self.send_btn, 2, 2)
        layout.addWidget(self.data_label, 2, 0, 1, 3)
        #layout.addWidget(self.received_label, 4, 0)
        layout.addWidget(self.received_textedit, 3, 0, 1, 3)
        layout.addWidget(self.vlt_label,4,2,1,3)


        self.vlt_label.setFont(QFont('Arial', 14))

        self.setLayout(layout)
        self._load_settings()

    def _load_settings(self) -> None:
        """Başlangıçtaki ayarları yükleyin."""
        settings = QSettings()

        # port name
        port_name = settings.value(SETTING_PORT_NAME)
        if port_name is not None:
            index = self.port_combobox.findData(port_name)
            if index > -1:
                self.port_combobox.setCurrentIndex(index)

        # last message
        msg = settings.value(SETTING_MESSAGE)
        if msg is not None:
            self.msg_lineedit.setText(msg)

    def _save_settings(self) -> None:
        """Kapatırken ayarları kaydedin."""
        settings = QSettings()
        settings.setValue(SETTING_PORT_NAME, self.port)
        settings.setValue(SETTING_MESSAGE, self.msg_lineedit.text())

    def show_error_message(self, msg: str) -> None:
        """Hata mesajını içeren bir Mesaj Kutusu gösterin."""
        QMessageBox.critical(self, QApplication.applicationName(), str(msg))

    def update_com_ports(self) -> None:
        """Update COM Port list in GUI."""
        for name, device in gen_serial_ports():
            self.port_combobox.addItem(name, device)

    @property
    def port(self) -> str:
        """Geçerli seri bağlantı noktasını çalıştırın."""
        return self.port_combobox.currentData()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Widget'ın kapatma olayını ele alın."""
        if ser.is_open:
            ser.close()

        self._save_settings()

        event.accept()

    def on_connect_btn_pressed(self) -> None:
        """Belirtilen bağlantı noktasına seri bağlantıyı açın."""
        if ser.is_open:
            ser.close()
        ser.port = self.port
        ser.baudrate = SER_BAUDRATE

        try:
            ser.open()
        except Exception as e:
            self.show_error_message(str(e))

        if ser.is_open:
            self.connect_btn.setVisible(False)
            self.disconnect_btn.setVisible(True)
            self.port_combobox.setDisabled(True)
            self.msg_lineedit.setEnabled(True)
            self.send_btn.setEnabled(True)
            loop.create_task(self.receive_serial_async())

    def on_disconnect_btn_pressed(self) -> None:
        """Mevcut seri bağlantıyı kapatın."""
        if ser.is_open:
            ser.close()

        if not ser.is_open:
            self.connect_btn.setVisible(True)
            self.disconnect_btn.setVisible(False)
            self.port_combobox.setEnabled(True)
            self.msg_lineedit.setEnabled(False)
            self.send_btn.setEnabled(False)

    def on_send_btn_pressed(self) -> None:
        """Arabaya mesaj gönderin."""
        msg = self.msg_lineedit.text() + '\r\n'
        loop.call_soon(send_serial_async, msg)

    async def receive_serial_async(self) -> None:
        a = 0
        """Gelen verileri bekleyin, metne dönüştürün ve Textedit'e ekleyin."""
        while True:
            time.sleep(27/1000)
            a = a+27
            msg = ser.readline()
            if msg != b'':
                text = msg.decode().strip()
                saat = datetime.now().strftime('%H:%M:%S.%f')[:-4]
                self.received_textedit.appendPlainText(saat+",\t" + str(a)+",\t"+ text)
                self.received_textedit.setFont(QFont('Arial', 13))
                kayit.write(str(a)+",\t"+ text+"\n")
            await asyncio.sleep(0)


if __name__ == '__main__':
    app = QApplication([])
    loop = QEventLoop()
    asyncio.set_event_loop(loop)

    app.setOrganizationName('VoltaTEAM')
    app.setApplicationName('VoltaCAR UART Interface')
    w = RemoteWidget()
    w.show()

    with loop:
        loop.run_forever()