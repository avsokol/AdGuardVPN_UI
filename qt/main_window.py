import os
import re

from AsyncioPySide6 import AsyncioPySide6
from PySide6 import QtCore, QtGui
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import QMainWindow, QInputDialog, QLineEdit, QTableView, QAbstractItemView

from lib.vpn_cli_wrapper import VpnCliWrapper
from qt.main_layout import Ui_MainWindow


class MainWindow(QMainWindow, Ui_MainWindow):

    CLI_BACKEND = 'cli'
    REST_BACKEND = 'rest'
    BACKENDS = [CLI_BACKEND, REST_BACKEND]

    def __init__(self, parent=None):
        QMainWindow.__init__(self)
        self.parent = parent
        self.setupUi(self)

        self.set_signals()

        self.cli_agent = VpnCliWrapper()
        self.model = QStandardItemModel(parent=self.parent)

        self.locations_tableView.setSelectionBehavior(QTableView.SelectRows)
        self.locations_tableView.setSelectionMode(QAbstractItemView.SingleSelection)

        self.current_location = None

    async def init_app(self):
        vpn_status, vpn_location = await self._status_vpn()
        self.update_connection_elements_state(vpn_status, vpn_location)
        await self._refresh_connections(vpn_location)
        self.show()
        self.update()
        self.repaint()

    def set_signals(self):
        self.refresh_toolButton.clicked.connect(self.refresh_connections)
        self.connect_pushButton.clicked.connect(self.connect_vpn)
        self.disconnect_pushButton.clicked.connect(self.disconnect_vpn)

    def on_location_select(self):
        indexes = self.locations_tableView.selectionModel().selectedIndexes()
        if len(indexes):
            location_index = indexes[0]
            self.current_location = location_index.data()
            self.connect_pushButton.setEnabled(True)

        else:
            self.current_location = None
            self.connect_pushButton.setEnabled(False)

    async def _refresh_connections(self, current_location=None):
        locations = await self.cli_agent.list_locations()

        self.model.setHorizontalHeaderLabels(['ISO', 'COUNTRY', 'CITY', 'PING'])

        self.locations_tableView.setModel(self.model)
        self.locations_tableView.hideColumn(1)
        self.locations_tableView.setColumnWidth(0, 32)
        self.locations_tableView.setColumnWidth(1, 80)
        self.locations_tableView.setColumnWidth(2, 140)
        self.locations_tableView.setColumnWidth(3, 20)
        self.locations_tableView.setAlternatingRowColors(True)
        self.locations_tableView.setSelectionBehavior(QTableView.SelectRows)
        self.locations_tableView.selectionModel().selectionChanged.connect(self.on_location_select)

        self.locations_tableView.horizontalHeader().setStretchLastSection(True)

        for location in locations.splitlines():
            parts = re.split(r"\s\s+", location)
            iso = parts[0].strip()
            country = parts[1].strip()
            city = parts[2].strip()
            ping = parts[3].strip()

            items = [QStandardItem(iso), QStandardItem(country), QStandardItem(city), QStandardItem(ping)]
            for item in items:
                item.setEditable(False)

            self.model.appendRow(items)

        if current_location:
            matches = self.model.findItems(current_location, QtCore.Qt.MatchFlag.MatchContains, column=2)
            row_indexes = sorted(list(set([row.row() for row in matches])))
            for match in matches:
                if current_location.lower() == match.text().lower():
                    self.locations_tableView.selectRow(row_indexes[0])

    def refresh_connections(self):
        AsyncioPySide6.runTask(self._refresh_connections())

    def update_connection_elements_state(self, status, location=None):
        if not status:
            return

        if status == 'Disconnected':
            self.connected_to_label.setText(f'Disconnected')
            self.disconnect_pushButton.setVisible(False)
            self.connect_pushButton.setVisible(True)
            if self.current_location:
                self.connect_pushButton.setEnabled(True)

            else:
                self.connect_pushButton.setEnabled(False)

            self.logo_label.setPixmap(
                QtGui.QPixmap(os.path.join(os.path.dirname(os.path.realpath(__file__)), "img/adguard_s.png"))
            )

        if status == 'Connected':
            self.connected_to_label.setText(f'Connected to: {location}')
            self.connect_pushButton.setVisible(False)
            self.disconnect_pushButton.setVisible(True)

            self.logo_label.setPixmap(
                QtGui.QPixmap(os.path.join(os.path.dirname(os.path.realpath(__file__)), "img/adguard_t.png"))
            )

    async def _status_vpn(self):
        result = await self.cli_agent.vpn_status()
        if result in ['VPN is disconnected']:
            status = 'Disconnected'
            location = None

        elif result.startswith('Connected to'):
            status = 'Connected'
            location = result.split()[2].strip(VpnCliWrapper.BOLD_START).strip(VpnCliWrapper.BOLD_END)

        else:
            raise Exception(f'Unexpected VPN Status: {result}')

        return status, location

    def status_vpn(self):
        return AsyncioPySide6.runTask(self._status_vpn())

    def disconnect_vpn(self):
        async def _disconnect_vpn():
            await self.cli_agent.vpn_stop()
            vpn_status, vpn_location = await self._status_vpn()
            self.update_connection_elements_state(vpn_status, vpn_location)

        AsyncioPySide6.runTask(_disconnect_vpn())

    def connect_vpn(self):
        if not self.current_location:
            return

        async def _connect_vpn():
            password, res = QInputDialog.getText(
                self.parent, 'Password', 'Enter sudo password:', echo=QLineEdit.EchoMode.Password
            )

            if res:
                await self.cli_agent.vpn_start(self.current_location, password)
                vpn_status, vpn_location = await self._status_vpn()
                self.update_connection_elements_state(vpn_status, vpn_location)

        AsyncioPySide6.runTask(_connect_vpn())



