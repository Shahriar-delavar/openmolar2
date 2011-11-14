#! /usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
##                                                                           ##
##  Copyright 2010, Neil Wallace <rowinggolfer@googlemail.com>               ##
##                                                                           ##
##  This program is free software: you can redistribute it and/or modify     ##
##  it under the terms of the GNU General Public License as published by     ##
##  the Free Software Foundation, either version 3 of the License, or        ##
##  (at your option) any later version.                                      ##
##                                                                           ##
##  This program is distributed in the hope that it will be useful,          ##
##  but WITHOUT ANY WARRANTY; without even the implied warranty of           ##
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            ##
##  GNU General Public License for more details.                             ##
##                                                                           ##
##  You should have received a copy of the GNU General Public License        ##
##  along with this program.  If not, see <http://www.gnu.org/licenses/>.    ##
##                                                                           ##
###############################################################################


from PyQt4 import QtCore, QtGui, QtWebKit
import logging

class Browser(QtWebKit.QWebView):
    '''
    A browser which is aware of some of the shortcuts offered by the server.
    '''
    shortcut_clicked = QtCore.pyqtSignal(object)

    def __init__(self, parent=None):
        QtWebKit.QWebView.__init__(self, parent)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.linkClicked.connect(self._link_clicked)

    def setHtml(self, html):
        QtWebKit.QWebView.setHtml(self, html)
        self.page().setLinkDelegationPolicy(QtWebKit.QWebPage.DelegateAllLinks)

    def _link_clicked(self, url):
        logging.debug("admin browser link clicked '%s'"% url)
        self.shortcut_clicked.emit(url.toString())

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    app = QtGui.QApplication([])
    dl = QtGui.QDialog()
    dl.setMinimumSize(400,200)

    def sig_catcher(*args):
        print args

    browser = Browser()
    browser.setHtml("hello<br /><a href='url'>click here</a>")

    browser.shortcut_clicked.connect(sig_catcher)

    layout = QtGui.QVBoxLayout(dl)
    layout.addWidget(browser)

    dl.exec_()