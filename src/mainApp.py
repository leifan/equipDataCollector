# encoding: utf-8

import sys, os, configparser
from base64 import b64encode, b64decode
import time, io, traceback
import logging
from logging.handlers import RotatingFileHandler

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.Qt import Qt

from clAlch import HtDac
import app_rc


class Config:
    default_data = {
        'host': '60.205.223.184', # '60.205.223.184'
        'port':'9001', 
        'com':'COM3', 
        'timeout':'1'
    }
    def __init__(self, fname):
        self.fullname = os.path.join(os.getcwd(), fname)
        conf = configparser.SafeConfigParser(defaults=self.default_data, default_section='DATABASE')
        try:
            with open(self.fullname, 'r') as fp:
                conf.read_file(fp)
        except:
            pass
        self.parser = conf

    def get_option(self, name):
        return self.parser.get(self.parser.default_section, name)

    def set_option(self, name, value):
        try:
            self.parser.set(self.parser.default_section, name, value)
        except:
            pass

    def changed(self, vals):
        try:
            return any([self.get_option(k)!=vals.get(k, '') for k in self.default_data.keys()])
        except:
            pass
        return True

    def save(self):
        try:
            with open(self.fullname, 'w') as fp:
                self.parser.write(fp)
        except:
            pass

def excepthook(etype, value, tb):
    try:
        tbinfofile = io.StringIO()
        traceback.print_exception(etype, value, tb, file=tbinfofile)
        tbinfofile.seek(0)
        tbinfo = tbinfofile.read()

        logging.error(tbinfo)
    except Exception as e:
        pass

class GuiLogger(QtWidgets.QPlainTextEdit):
    newmsg = QtCore.pyqtSignal(str)

    def __init__(self, parent=None, maxLines=5000):
        super().__init__(parent)
        #self.setAcceptRichText(True)
        self.setReadOnly(True)
        self.setMinimumHeight(50)
        self.setMaximumBlockCount(maxLines)

        # The frame especification
        self.frame_style = {'shape': self.frameShape(),
            'shadow': self.frameShadow(),
            'lwidth': self.lineWidth(),
            'foreground': self.palette().color(QtGui.QPalette.Active,
                QtGui.QPalette.WindowText)}

        # Connect signals to slots
        self.newmsg.connect(self.appendPlainText)

    def write(self, text):
        if text not in ['\n', '\r\n']:
            self.newmsg.emit(text)

    def flush(self):
        pass


class MainWindow(QtWidgets.QDialog):

    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)
        self.cfg = Config("config.ini")

        self.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)
        self.setWindowState(Qt.WindowNoState)
        self.console = GuiLogger(self)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.console)
        self.setLayout(layout)

        font = QtGui.QFont('consolas', 10)
        self.console.setFont(font)

        self.createActions()
        self.createTrayIcon()
        self.trayIcon.activated.connect(self.iconActivated)
        self.trayIcon.show()
        self.setWindowTitle(self.tr("数据采集"))
        self.setWindowIcon(QtGui.QIcon(':/images/active.png'))

        self.startCl()

        self.timer = QtCore.QTimer()
        self.timer.setInterval(20*1000)
        self.timer.start()
        self.timer.timeout.connect(self.monitorWorkers)

        self.resize(800, 400)

    def event(self, evt):
       if evt.type() == QtCore.QEvent.User+1:
           self.restartCl()
           return True
       return super(MainWindow, self).event(evt)

    def closeEvent(self, event):
        if self.trayIcon.isVisible():
            self.hide()
            event.ignore()

    def createActions(self):
        #self.minimizeAction = QtWidgets.QAction(self.tr("&Minimize"), self, triggered=self.hide)
        #self.maximizeAction = QtWidgets.QAction("Ma&ximize", self,
        #        triggered=self.showMaximized)
        #self.toggleCl = QtWidgets.QAction(self.tr(""), self, triggered=self.hide)
        self.restoreAction = QtWidgets.QAction(self.tr("&设置"), self,
                triggered=self.showSettings)
        self.quitAction = QtWidgets.QAction(self.tr("&退出"), self,
                triggered=QtWidgets.QApplication.instance().quit)

    def createTrayIcon(self):
         self.trayIconMenu = QtWidgets.QMenu(self)
         self.trayIconMenu.addAction(self.restoreAction)
         self.trayIconMenu.addSeparator()
         self.trayIconMenu.addAction(self.quitAction)

         self.trayIcon = QtWidgets.QSystemTrayIcon(self)
         self.trayIcon.setIcon(QtGui.QIcon(':/images/active.png'))
         self.trayIcon.setToolTip(self.tr('数据采集'))
         self.trayIcon.setContextMenu(self.trayIconMenu)

    def iconActivated(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.Trigger:
            self.setVisible(not self.isVisible())

    def showSettings(self):
        settingswnd = SettingsWindow(self, self.cfg)
        settingswnd.exec_()

    def _get_info(self):
        host = self.cfg.get_option('host')
        port = self.cfg.get_option('port')
        com = self.cfg.get_option('com')
        timeout = self.cfg.get_option('timeout')
        return (host, port, com, timeout)

    @QtCore.pyqtSlot()
    def startCl(self):
        info = self._get_info()
        self.dac = HtDac(info)
        self.dac.startDac()

    @QtCore.pyqtSlot()
    def endThreads(self):
        if self.dac:
            self.dac.endDac()
            self.dac = None

    def restartCl(self):
       self.endThreads()
       self.startCl()

    @QtCore.pyqtSlot()
    def monitorWorkers(self):
        if self.dac:
            self.dac.monitor()



class SettingsWindow(QtWidgets.QDialog):
    def __init__(self, parent, cfg):
        super(SettingsWindow, self).__init__(parent)
        self.cfg = cfg
        self.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint | Qt.Tool |
                            Qt.WindowStaysOnTopHint)

        self.createMessageGroupBox()
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.messageGroupBox)
        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok |
                                                    QtWidgets.QDialogButtonBox.Cancel
                                                    , self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText(self.tr('保存'))
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText(self.tr('退出'))

        mainLayout.addWidget(self.buttonBox)
        self.setLayout(mainLayout)
        self.setWindowTitle(self.tr("系统设置"))
        self.resize(560, 260)

    def accept(self):
        conf = self.cfg
        vals = {'host': self.hostEdit.text(),
                'port': self.portEdit.text(),
                'com': self.comEdit.text(),
                'timeout': self.timeoutEdit.text() }
        if conf.changed(vals):
            for k, v in vals.items():
                conf.set_option(k, v)
            conf.save()
            QtWidgets.qApp.postEvent(self.parent(), QtCore.QEvent(QtCore.QEvent.User+1))
        super(SettingsWindow, self).accept()

    def reject(self):
        super(SettingsWindow, self).reject()

    def createMessageGroupBox(self):
        conf = self.cfg
        self.messageGroupBox = QtWidgets.QGroupBox(self.tr("通讯设置"))

        hostLabel = QtWidgets.QLabel(self.tr("服务器:"))
        self.hostEdit = QtWidgets.QLineEdit(conf.get_option('host'))

        portLabel = QtWidgets.QLabel(self.tr("端口:"))
        self.portEdit = QtWidgets.QLineEdit(conf.get_option('port'))

        comLabel = QtWidgets.QLabel(self.tr("通讯串口:"))
        self.comEdit = QtWidgets.QLineEdit(conf.get_option('com'))

        timeoutLabel = QtWidgets.QLabel(self.tr("超时时间:"))
        self.timeoutEdit = QtWidgets.QLineEdit(conf.get_option('timeout'))


        messageLayout = QtWidgets.QGridLayout()
        messageLayout.addWidget(hostLabel, 0, 0)
        messageLayout.addWidget(self.hostEdit, 0, 1)

        messageLayout.addWidget(portLabel, 1, 0)
        messageLayout.addWidget(self.portEdit, 1, 1)

        messageLayout.addWidget(comLabel, 2, 0)
        messageLayout.addWidget(self.comEdit, 2, 1)

        messageLayout.addWidget(timeoutLabel, 3, 0)
        messageLayout.addWidget(self.timeoutEdit, 3, 1)

        self.messageGroupBox.setLayout(messageLayout)

class MainApp(QtWidgets.QApplication):
    def __init__(self, argv):
        super(MainApp, self).__init__(argv)
        self.singular = QtCore.QSharedMemory('htscada', self)

    def lock(self):
        if self.singular.attach(QtCore.QSharedMemory.ReadOnly):
            self.singular.detach()
            return False
        if self.singular.create(1):
            return True
        return False

def main(args):
    if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
        QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)

    app = MainApp(args)
    if not app.lock():
        sys.exit(1)

    dlg = MainWindow()
    app.aboutToQuit.connect(dlg.endThreads)

    if not QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
        QtWidgets.QMessageBox.critical(None, app.tr("采集程序"),
                app.tr("I couldn't detect any system tray on this system."))
        sys.exit(1)

    QtWidgets.QApplication.setQuitOnLastWindowClosed(False)

    # Setup top level logger using command line options
    logger = logging.getLogger()

    UI_FORMAT = '%(levelname)-8s: %(message)s'
    uFormatter = logging.Formatter(UI_FORMAT)
    guiHandler = logging.StreamHandler(dlg.console)
    guiHandler.setFormatter(uFormatter)
    guiHandler.setLevel(logging.INFO)
    logger.addHandler(guiHandler)

    LOG_FORMAT = '%(asctime)s %(filename)s:%(lineno)d %(levelname)-8s: %(message)s'
    formatter = logging.Formatter(LOG_FORMAT)
    log_filename = os.path.join(os.path.dirname(__file__), 'run_log.log')
    fHandler = RotatingFileHandler(log_filename, maxBytes=1024*1024*6, encoding='cp936')
    fHandler.setFormatter(formatter)
    fHandler.setLevel(logging.INFO)
    logger.addHandler(fHandler)

    #stdHandler = logging.StreamHandler()
    #stdHandler.setLevel(logging.DEBUG)
    #logger.addHandler(stdHandler)

    logger.setLevel(logging.DEBUG)

    dlg.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    sys.excepthook = excepthook
    main(sys.argv)

