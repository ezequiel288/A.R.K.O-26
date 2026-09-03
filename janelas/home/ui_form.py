# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'form.ui'
##
## Created by: Qt User Interface Compiler version 6.11.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QLineEdit, QPushButton,
    QSizePolicy, QWidget)

class Ui_Widget(object):
    def setupUi(self, Widget):
        if not Widget.objectName():
            Widget.setObjectName(u"Widget")
        Widget.resize(800, 600)
        self.checkBox = QCheckBox(Widget)
        self.checkBox.setObjectName(u"checkBox")
        self.checkBox.setGeometry(QRect(210, 60, 91, 20))
        self.checkBox.setChecked(False)
        self.pushButton = QPushButton(Widget)
        self.pushButton.setObjectName(u"pushButton")
        self.pushButton.setGeometry(QRect(90, 50, 91, 24))
        self.pushButton.setStyleSheet(u"")
        self.nome = QLineEdit(Widget)
        self.nome.setObjectName(u"nome")
        self.nome.setGeometry(QRect(200, 300, 113, 22))
        self.btn_nome = QPushButton(Widget)
        self.btn_nome.setObjectName(u"btn_nome")
        self.btn_nome.setGeometry(QRect(340, 300, 75, 24))

        self.retranslateUi(Widget)

        QMetaObject.connectSlotsByName(Widget)
    # setupUi

    def retranslateUi(self, Widget):
        Widget.setWindowTitle(QCoreApplication.translate("Widget", u"Widget", None))
        self.checkBox.setText(QCoreApplication.translate("Widget", u"CheckBox", None))
        self.pushButton.setText(QCoreApplication.translate("Widget", u"PushButton", None))
        self.btn_nome.setText(QCoreApplication.translate("Widget", u"Nome", None))
    # retranslateUi

