from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QPlainTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from mdt_configurator.devices.md400t import MD400T
from mdt_configurator.protocol.definitions import PID_DEFINITIONS, get_pid
from mdt_configurator.protocol.packet import MID_BLDC, MID_MMI, Packet
from mdt_configurator.services.session import Session, TrafficEvent
from mdt_configurator.transport.serial_transport import list_serial_ports


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MDT Linux Configurator — MD400T / MDH250")

        self.session = Session()
        self.device = MD400T(self.session)
        self.session.add_listener(self._traffic)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        for name, tab in (
            ("Connection", self._build_connection_tab()),
            ("Motor Setup", self._build_setup_tab()),
            ("Control", self._build_control_tab()),
            ("Monitor", self._build_monitor_tab()),
            ("Protocol", self._build_protocol_tab()),
            ("Log", self._build_log_tab()),
        ):
            self.tabs.addTab(tab, name)

        self.monitor_timer = QTimer(self)
        self.monitor_timer.setInterval(500)
        self.monitor_timer.timeout.connect(self._poll_monitor)
        self.statusBar().showMessage("Disconnected")

    def closeEvent(self, event) -> None:  # noqa: N802
        self.monitor_timer.stop()
        self.session.disconnect()
        super().closeEvent(event)

    def _build_connection_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        group = QGroupBox("RS485 connection")
        form = QFormLayout(group)

        self.port_combo = QComboBox()
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["19200", "9600", "38400", "57600", "115200"])
        self.driver_id = QSpinBox()
        self.driver_id.setRange(0, 253)
        self.driver_id.setValue(1)

        buttons = QHBoxLayout()
        refresh = QPushButton("Refresh ports")
        connect = QPushButton("Connect")
        disconnect = QPushButton("Disconnect")
        refresh.clicked.connect(self._refresh_ports)
        connect.clicked.connect(self._connect)
        disconnect.clicked.connect(self._disconnect)
        buttons.addWidget(refresh)
        buttons.addWidget(connect)
        buttons.addWidget(disconnect)

        self.connection_state = QLabel("● Disconnected")
        form.addRow("Serial port", self.port_combo)
        form.addRow("Baud rate", self.baud_combo)
        form.addRow("Driver ID", self.driver_id)
        form.addRow(buttons)
        form.addRow("Status", self.connection_state)

        layout.addWidget(group)
        layout.addStretch()
        self._refresh_ports()
        return w

    def _build_setup_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        profile = QGroupBox("MDH250 profile")
        grid = QGridLayout(profile)
        values = [
            ("Driver", "MD400T"),
            ("Motor", "MDH250"),
            ("Voltage", "24–48 VDC"),
            ("Rated current", "8 A"),
            ("Poles", "30"),
            ("Hall DATA", "15"),
            ("Encoder", "4096 PPR"),
            ("Rated speed", "200 rpm"),
            ("Maximum speed", "300 rpm"),
        ]
        for row, (key, value) in enumerate(values):
            grid.addWidget(QLabel(key), row, 0)
            grid.addWidget(QLabel(value), row, 1)

        actions = QHBoxLayout()
        read = QPushButton("Read from driver")
        apply_btn = QPushButton("Apply safe profile subset")
        read.clicked.connect(self._read_setup)
        apply_btn.clicked.connect(self._apply_setup)
        actions.addWidget(read)
        actions.addWidget(apply_btn)

        self.setup_output = QPlainTextEdit()
        self.setup_output.setReadOnly(True)
        self.setup_output.setPlaceholderText(
            "Read compares Hall type, max RPM, encoder parameter, and PID 17.\n"
            "Apply writes only Hall1/Hall2 and Max RPM1/Max RPM2. Encoder PPR is intentionally not auto-written."
        )

        layout.addWidget(profile)
        layout.addLayout(actions)
        layout.addWidget(self.setup_output)
        return w

    def _build_control_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        safety = QGroupBox("Safety interlock")
        safety_layout = QVBoxLayout(safety)
        self.arm_box = QCheckBox(
            "I confirm the wheels/mechanism are secured, the area is clear, and a hardware stop is available."
        )
        safety_layout.addWidget(self.arm_box)
        safety_layout.addWidget(QLabel("Start at 20–30 rpm. Positive rpm = CCW and negative rpm = CW per the communication manual."))

        control = QGroupBox("Signed RPM control")
        grid = QGridLayout(control)
        self.rpm1 = QSpinBox()
        self.rpm2 = QSpinBox()
        for spin in (self.rpm1, self.rpm2):
            spin.setRange(-300, 300)
            spin.setValue(30)

        run1 = QPushButton("Run Motor 1")
        run2 = QPushButton("Run Motor 2")
        stop = QPushButton("FREE STOP / TQ OFF")
        run1.clicked.connect(lambda: self._run_motor(1))
        run2.clicked.connect(lambda: self._run_motor(2))
        stop.clicked.connect(self._free_stop)

        grid.addWidget(QLabel("Motor 1 target rpm"), 0, 0)
        grid.addWidget(self.rpm1, 0, 1)
        grid.addWidget(run1, 0, 2)
        grid.addWidget(QLabel("Motor 2 target rpm"), 1, 0)
        grid.addWidget(self.rpm2, 1, 1)
        grid.addWidget(run2, 1, 2)
        grid.addWidget(stop, 2, 0, 1, 3)

        layout.addWidget(safety)
        layout.addWidget(control)
        layout.addStretch()
        return w

    def _build_monitor_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        buttons = QHBoxLayout()
        self.monitor_toggle = QPushButton("Start polling")
        self.monitor_toggle.setCheckable(True)
        self.monitor_toggle.toggled.connect(self._toggle_monitor)
        once = QPushButton("Read once")
        once.clicked.connect(self._poll_monitor)
        buttons.addWidget(self.monitor_toggle)
        buttons.addWidget(once)

        self.monitor_table = QTableWidget(2, 7)
        self.monitor_table.setHorizontalHeaderLabels(
            ["Motor", "RPM", "Current (A)", "Output", "State", "Position", "DI"]
        )
        self.monitor_table.setItem(0, 0, QTableWidgetItem("Motor 1 / PID 196"))
        self.monitor_table.setItem(1, 0, QTableWidgetItem("Motor 2 / PID 201"))

        self.monitor_note = QLabel("Monitor data is decoded according to PID 196/201. Current = raw × 0.1 A.")
        layout.addLayout(buttons)
        layout.addWidget(self.monitor_table)
        layout.addWidget(self.monitor_note)
        layout.addStretch()
        return w

    def _build_protocol_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        top = QHBoxLayout()
        self.pid_combo = QComboBox()
        for pid, info in sorted(PID_DEFINITIONS.items()):
            self.pid_combo.addItem(f"{pid:3d} / 0x{pid:02X} — {info.name}", pid)
        self.pid_combo.currentIndexChanged.connect(self._update_protocol_preview)

        self.protocol_data = QPlainTextEdit()
        self.protocol_data.setMaximumHeight(55)
        self.protocol_data.setPlaceholderText("DATA bytes in hex, e.g. 0f or 2c 01")
        preview = QPushButton("Build packet")
        preview.clicked.connect(self._update_protocol_preview)
        request = QPushButton("Request selected PID")
        request.clicked.connect(self._request_selected_pid)

        top.addWidget(QLabel("PID"))
        top.addWidget(self.pid_combo, 1)
        top.addWidget(preview)
        top.addWidget(request)

        self.pid_description = QLabel()
        self.pid_description.setWordWrap(True)
        self.packet_table = QTableWidget(2, 7)
        self.packet_table.setHorizontalHeaderLabels(["RMID", "TMID", "ID", "PID", "LEN", "DATA", "CHK"])
        self.packet_table.setVerticalHeaderLabels(["Name", "Hex"])

        self.raw_packet = QPlainTextEdit()
        self.raw_packet.setReadOnly(True)
        self.raw_packet.setMaximumHeight(80)
        self.raw_packet.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))

        layout.addLayout(top)
        layout.addWidget(self.pid_description)
        layout.addWidget(self.packet_table)
        layout.addWidget(QLabel("Raw packet"))
        layout.addWidget(self.raw_packet)
        layout.addStretch()
        self._update_protocol_preview()
        return w

    def _build_log_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))
        clear = QPushButton("Clear")
        clear.clicked.connect(self.log_output.clear)
        layout.addWidget(clear)
        layout.addWidget(self.log_output)
        return w

    def _refresh_ports(self) -> None:
        current = self.port_combo.currentText()
        self.port_combo.clear()
        ports = list_serial_ports()
        self.port_combo.addItems(ports)
        if current in ports:
            self.port_combo.setCurrentText(current)
        if not ports:
            self.port_combo.addItem("/dev/ttyUSB0")

    def _connect(self) -> None:
        try:
            self.session.connect(
                self.port_combo.currentText(),
                int(self.baud_combo.currentText()),
                self.driver_id.value(),
            )
            version = self.session.request_pid(1)
            self.connection_state.setText(
                f"● Connected — PID_VER raw: {version.data.hex(' ') or '(empty)'}"
            )
            self.statusBar().showMessage("Connected")
        except Exception as exc:
            self.session.disconnect()
            self.connection_state.setText("● Disconnected")
            QMessageBox.critical(self, "Connection failed", str(exc))

    def _disconnect(self) -> None:
        self.monitor_timer.stop()
        self.monitor_toggle.setChecked(False)
        self.session.disconnect()
        self.connection_state.setText("● Disconnected")
        self.statusBar().showMessage("Disconnected")

    def _require_connection(self) -> bool:
        if self.session.connected:
            return True
        QMessageBox.warning(self, "Not connected", "Connect to the MD400T first.")
        return False

    def _read_setup(self) -> None:
        if not self._require_connection():
            return
        try:
            data = self.device.read_key_setup()
            expected = {
                "limit_switch": "(wiring-dependent; not changed automatically)",
                "hall1": "15 for MDH250",
                "hall2": "15 for MDH250",
                "max_rpm1": "300",
                "max_rpm2": "300",
                "enc_ppr": "4096 expected from motor manual; verify scaling",
            }
            lines = ["Driver configuration", "--------------------"]
            for key, hint in expected.items():
                lines.append(f"{key:14s}: {data.get(key, 'n/a')}    [{hint}]")
            self.setup_output.setPlainText("\n".join(lines))
        except Exception as exc:
            QMessageBox.critical(self, "Read failed", str(exc))

    def _apply_setup(self) -> None:
        if not self._require_connection():
            return
        reply = QMessageBox.question(
            self,
            "Write MDH250 setup?",
            "This writes Hall type 15 to Motor 1/2 and max RPM 300 to Motor 1/2.\n\n"
            "It does NOT write encoder PPR and does NOT change PID 17. Continue?",
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self.device.apply_mdh250_safe_subset()
            self.setup_output.appendPlainText(
                "\nWrote: PID21=15, PID65=15, PID121=300, PID122=300.\n"
                "Read back the driver values before motor testing."
            )
        except Exception as exc:
            QMessageBox.critical(self, "Write failed", str(exc))

    def _run_motor(self, motor: int) -> None:
        if not self._require_connection():
            return
        if not self.arm_box.isChecked():
            QMessageBox.warning(self, "Control is disarmed", "Confirm the safety acknowledgement first.")
            return
        rpm = self.rpm1.value() if motor == 1 else self.rpm2.value()
        try:
            self.device.command_velocity(motor, rpm)
        except Exception as exc:
            QMessageBox.critical(self, "Command failed", str(exc))

    def _free_stop(self) -> None:
        if not self._require_connection():
            return
        try:
            self.device.torque_off()
        except Exception as exc:
            QMessageBox.critical(self, "Stop failed", str(exc))

    def _toggle_monitor(self, checked: bool) -> None:
        if checked:
            if not self._require_connection():
                self.monitor_toggle.setChecked(False)
                return
            self.monitor_toggle.setText("Stop polling")
            self.monitor_timer.start()
            self._poll_monitor()
        else:
            self.monitor_toggle.setText("Start polling")
            self.monitor_timer.stop()

    def _poll_monitor(self) -> None:
        if not self.session.connected:
            return
        try:
            for row, motor in enumerate((1, 2)):
                data = self.device.read_monitor(motor)
                state = ", ".join(data.state_flags) if data.state_flags else "NORMAL"
                values = [
                    str(data.rpm),
                    f"{data.current_a:.1f}",
                    str(data.output),
                    f"0x{data.state:02X} {state}",
                    str(data.position),
                    "n/a" if data.digital_inputs is None else f"0x{data.digital_inputs:02X}",
                ]
                for col, value in enumerate(values, start=1):
                    self.monitor_table.setItem(row, col, QTableWidgetItem(value))
        except Exception as exc:
            self.monitor_timer.stop()
            self.monitor_toggle.setChecked(False)
            self.monitor_note.setText(f"Monitor error: {exc}")

    def _update_protocol_preview(self) -> None:
        pid = int(self.pid_combo.currentData())
        info = get_pid(pid)
        text = self.protocol_data.toPlainText().strip()
        try:
            data = bytes.fromhex(text) if text else b""
            packet = Packet(MID_BLDC, MID_MMI, self.driver_id.value(), pid, data)
            raw = packet.encode()
        except Exception as exc:
            self.raw_packet.setPlainText(f"Invalid DATA: {exc}")
            return

        if info:
            self.pid_description.setText(
                f"<b>{info.name}</b> [{info.access}] — {info.description}"
                + (f"<br><i>{info.notes}</i>" if info.notes else "")
            )

        fields = [
            ("Motor driver", f"{raw[0]:02X}"),
            ("PC/MMI", f"{raw[1]:02X}"),
            ("Driver ID", f"{raw[2]:02X}"),
            (info.name if info else "PID", f"{raw[3]:02X}"),
            ("Data bytes", f"{raw[4]:02X}"),
            ("Payload", " ".join(f"{b:02X}" for b in data) or "—"),
            ("Checksum", f"{raw[-1]:02X}"),
        ]
        for col, (name, value) in enumerate(fields):
            self.packet_table.setItem(0, col, QTableWidgetItem(name))
            self.packet_table.setItem(1, col, QTableWidgetItem(value))
        self.raw_packet.setPlainText(" ".join(f"{b:02X}" for b in raw))

    def _request_selected_pid(self) -> None:
        if not self._require_connection():
            return
        pid = int(self.pid_combo.currentData())
        try:
            response = self.session.request_pid(pid)
            self.raw_packet.appendPlainText(
                f"\nRX PID {response.pid}: {response.data.hex(' ') or '(no data)'}"
            )
        except Exception as exc:
            QMessageBox.critical(self, "Request failed", str(exc))

    def _traffic(self, event: TrafficEvent) -> None:
        if not hasattr(self, "log_output"):
            return
        packet = event.packet
        pid_text = f"PID={packet.pid:3d}" if packet else "PID=???"
        info = get_pid(packet.pid) if packet else None
        name = info.name if info else ""
        self.log_output.appendPlainText(
            f"{event.timestamp:%H:%M:%S.%f}"[:-3]
            + f" {event.direction:2s} {pid_text} {name:20s} | {event.hex}"
        )
