#! /usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
##                                                                           ##
##  Copyright 2011, Neil Wallace <rowinggolfer@googlemail.com>               ##
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

'''
Provides a Class for printing on an A4 Sheet
'''

from PyQt4 import QtCore, QtGui

class PrintedForm(object):
    '''
    a class to set up and print an a4 form
    '''
    testing_mode = False 
    
    print_background = False
    BACKGROUND_IMAGE = ""
    
    rects = {}
    off_set = QtCore.QPoint(0,0)
        
    def __init__(self):
   
        self.printer = QtGui.QPrinter()
        self.printer.setPageSize(QtGui.QPrinter.A4)
        self.printer.setPaperSource(QtGui.QPrinter.Middle)  #set bin 2
    
    def setOffset(self, x, y):
        '''
        offsets all printing by x,y
        '''
        self.off_set = QtCore.QPointF(x,y)
        
    def set_skip_dialog(self, skip=True):
        '''
        call this function to skip a dialog box when printing
        '''
        self.skip_dialog = skip
        
    def controlled_print(self):
        '''
        raise a dialog before printing
        '''
        dialog = QtGui.QPrintDialog(self.printer)
        if dialog.exec_():
            return self.print_()
        
    def print_(self, painter=None):
        '''
        print the background and any rects if in testing_mode
        
        note - this functions return the active painter so that classes which
        inherit from PrintedForm can finalise the printing.
        '''
        if painter is None:
            painter = QtGui.QPainter(self.printer)
        
        if self.print_background:
            painter.save()
            painter.translate(
                -self.printer.pageRect().x(), 
                -self.printer.pageRect().y() 
                )
                
            pm = QtGui.QPixmap(self.BACKGROUND_IMAGE)
            if pm.isNull():
                print "unable to load pixmap from '%s'"% self.BACKGROUND_IMAGE
            painter.drawPixmap(self.printer.paperRect(), pm, pm.rect())

            painter.restore()

        painter.translate(self.off_set)
        
        if self.testing_mode:
            painter.save()
            painter.setPen(QtGui.QPen(QtCore.Qt.black,1))
            for rect in self.rects.values():
                painter.drawRect(rect)
            painter.restore()
            
        return painter    
            
if __name__ == "__main__":
    app = QtGui.QApplication([])
    form = PrintedForm()
    form.controlled_print()
    