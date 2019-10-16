from qgis.PyQt.QtWidgets import QApplication
from qgis.PyQt.QtGui import QCursor
from qgis.PyQt.QtCore import Qt, QCoreApplication

from qgis.core import QgsMessageOutput

from qgis.gui import QgsMessageBar

class MessageBar(QgsMessageBar):
    pass

def execute(func):
    QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
    try:
        return func()
    finally:
        QApplication.restoreOverrideCursor()
        QCoreApplication.processEvents()

def showHtmlMessage(msg):
    dlg = QgsMessageOutput.createMessageOutput()
    dlg.setTitle("Layer metadata")
    dlg.setMessage(html, QgsMessageOutput.MessageHtml)
    dlg.showMessage()

