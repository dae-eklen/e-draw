#!/usr/bin/env python

#############################################################################
##
## Copyright (C) 2010 Riverbank Computing Limited.
## Copyright (C) 2010 Nokia Corporation and/or its subsidiary(-ies).
## All rights reserved.
##
## This file is part of the examples of PyQt.
##
## $QT_BEGIN_LICENSE:BSD$
## You may use this file under the terms of the BSD license as follows:
##
## "Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are
## met:
##   * Redistributions of source code must retain the above copyright
##     notice, this list of conditions and the following disclaimer.
##   * Redistributions in binary form must reproduce the above copyright
##     notice, this list of conditions and the following disclaimer in
##     the documentation and/or other materials provided with the
##     distribution.
##   * Neither the name of Nokia Corporation and its Subsidiary(-ies) nor
##     the names of its contributors may be used to endorse or promote
##     products derived from this software without specific prior written
##     permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
## "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
## LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
## A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
## OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
## SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
## LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
## DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
## THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
## (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
## OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
## $QT_END_LICENSE$
##
#############################################################################

# These are only needed for Python v2 but are harmless for Python v3
import sip
sip.setapi('QString', 2)
sip.setapi('QVariant', 2)

import sys
import time
import os
from PyQt4 import QtCore, QtGui, uic
import log

import resource.res
from History import Point, History

PATH_TEMP = os.path.join('.', 'temp')
FORMAT = 'jpeg'


class ScribbleArea(QtGui.QWidget):
	"""
	class adds canvas area to MainWindow, overrides parent's event functions
	"""
	def __init__(self, parent = None):
		QtGui.QWidget.__init__(self, parent)
		
		self.parent = parent
		
		self.usersScribbleHistory = None

		self.setAttribute(QtCore.Qt.WA_StaticContents)
		self.modified = False
		self.scribbling = False
		self.myPenWidth = 2
		self.myPenColor = QtGui.QColor(0, 170, 255)
		imageSize = QtCore.QSize()
		self.image = QtGui.QImage(imageSize, QtGui.QImage.Format_RGB32)
		self.lastPoint = QtCore.QPoint()
		"""
		self.scrollArea = QtGui.QScrollArea()
		self.scrollArea.setBackgroundRole(QtGui.QPalette.Dark)
		self.scrollArea.setWidget(self.scribbleArea)
		"""		
		self.history = History()

	def saveImage(self, fileName, fileFormat):
		visibleImage = self.image
		#self.resizeImage(visibleImage, self.size())

		if visibleImage.save(fileName, fileFormat):
			self.modified = False
			return True
		else:
			return False

	def setPenColor(self, newColor):
		self.myPenColor = newColor

	def setPenWidth(self, newWidth):
		self.myPenWidth = newWidth
		
	def draw(self, d, stroke, stroke_width):
		color = stroke.split(" ")
		points = d.split()
		lastP = None
		painter = QtGui.QPainter()
		painter.begin(self.image)
		painter.setPen(QtGui.QPen(QtGui.QColor(int(color[0]), int(color[1]), int(color[2])), int(stroke_width),
										  QtCore.Qt.SolidLine, QtCore.Qt.RoundCap,
										  QtCore.Qt.RoundJoin))	  
		for i in range(0, len(points), 2):
			p = QtCore.QPoint(int(points[i]), int(points[i+1]))
			if lastP is not None:
				
				painter.drawLine(QtCore.QPoint(lastP), QtCore.QPoint(p))
				rad = int(stroke_width) / 2
				self.update(QtCore.QRect(lastP, p).normalized()
										 .adjusted(-rad, -rad, +rad, +rad))
			lastP = p		
		painter.end()

	def mousePressEvent(self, event):
		if event.button() == QtCore.Qt.LeftButton:
			self.lastPoint = event.pos()
			self.scribbling = True
			self.history.newStroke(event.x(), event.y(), self.myPenWidth, \
				self.myPenColor.red(), self.myPenColor.green(), \
				self.myPenColor.blue())
			#self.history.printXEP113()

	def mouseMoveEvent(self, event):
		if (event.buttons() & QtCore.Qt.LeftButton) and self.scribbling:
			self.drawLineTo(event.pos())
			self.history.newPoint(event.x(), event.y(), self.myPenWidth, \
				self.myPenColor.red(), self.myPenColor.green(), \
				self.myPenColor.blue())
				
	def redraw(self):
		# used for undo
		
		# clear canvas
		self.image.fill(QtGui.qRgb(255, 255, 255))
		self.modified = False
		self.update()
		
		# redraw
		painter = QtGui.QPainter()
		
		for stroke in self.history.history:
			startX = -1
			startY = -1
			for point in stroke:
				x = point.getX()
				y = point.getY()
				w = point.getW()
				cR = point.getCR()
				cG = point.getCG()
				cB = point.getCB()
				
				if startX == -1 and startY == -1:
					startX = x
					startY = y
					continue
					
				painter.begin(self.image)		
				painter.setPen(QtGui.QPen(QtGui.QColor(cR, cG, cB), w,
										  QtCore.Qt.SolidLine, QtCore.Qt.RoundCap,
										  QtCore.Qt.RoundJoin))
				painter.drawLine(QtCore.QPoint(startX, startY), QtCore.QPoint(x, y))		
				painter.end()
				rad = self.myPenWidth / 2
				self.update(QtCore.QRect(QtCore.QPoint(startX, startY), QtCore.QPoint(x, y))
					.normalized().adjusted(-rad, -rad, +rad, +rad))	
					
				startX = x
				startY = y						 

	def mouseReleaseEvent(self, event):
		if event.button() == QtCore.Qt.LeftButton and self.scribbling:
			self.drawLineTo(event.pos())
			self.scribbling = False
			
			d, stroke, stroke_width = self.history.getLastXEP113()

	def paintEvent(self, event):	 
		painter = QtGui.QPainter()
		painter.begin(self)
		painter.drawImage(QtCore.QPoint(0, 0), self.image)
		painter.end()

	def resizeEvent(self, event):
		if self.width() > self.image.width() or self.height() > self.image.height():
			newWidth = max(self.width() + 128, self.image.width())
			newHeight = max(self.height() + 128, self.image.height())
			self.resizeImage(self.image, QtCore.QSize(newWidth, newHeight))
			self.update()

		QtGui.QWidget.resizeEvent(self, event)

	def drawLineTo(self, endPoint):
		painter = QtGui.QPainter()
		painter.begin(self.image)
		painter.setPen(QtGui.QPen(self.myPenColor, self.myPenWidth,
								  QtCore.Qt.SolidLine, QtCore.Qt.RoundCap,
								  QtCore.Qt.RoundJoin))
		
		painter.drawLine(self.lastPoint, endPoint)
		painter.end()
		self.modified = True

		rad = self.myPenWidth / 2
		self.update(QtCore.QRect(self.lastPoint, endPoint).normalized()
										 .adjusted(-rad, -rad, +rad, +rad))
		self.lastPoint = QtCore.QPoint(endPoint)

	def resizeImage(self, image, newSize):
		if image.size() == newSize:
			return

		newImage = QtGui.QImage(newSize, QtGui.QImage.Format_RGB32)
		newImage.fill(QtGui.qRgb(255, 255, 255))
		painter = QtGui.QPainter()
		painter.begin(newImage)
		painter.drawImage(QtCore.QPoint(0, 0), image)
		painter.end()
		self.image = newImage
	
	def isModified(self):
		return self.modified

	def penColor(self):
		return self.myPenColor

	def penWidth(self):
		return self.myPenWidth
	
	def clearImage(self):
		# triggered on pressing 'Clear' (Shift+X)
		if self.modified == True:
			reply = QtGui.QMessageBox.question(self, "Clear", 
				"Are you sure to clear the canvas?", 
				QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, 
				QtGui.QMessageBox.No)
			
			if reply == QtGui.QMessageBox.Yes:
				# clears image
				self.image.fill(QtGui.qRgb(255, 255, 255))
				self.modified = False
				self.update()
				self.history.clear()


class MainWindow(QtGui.QMainWindow):	
	"""
	class for loading and extending .ui file generated in Qt Designer;
	has basic functionality of interface
	"""
	def __init__(self, parent=None):
		super(MainWindow, self).__init__(parent)
		
		self.saveAsActs = []
		
		# loading .ui
		uic.loadUi('project.ui', self)        

		# ading canvas
		self.scribbleArea = ScribbleArea(self)
		self.vlt_top.addWidget(self.scribbleArea)

		# connect functions
		self.act_clear.triggered.connect(self.clearImage)
		self.act_color.triggered.connect(self.penColor)
		self.act_width.triggered.connect(self.penWidth)
		self.act_undo.triggered.connect(self.undo)
		self.act_add.triggered.connect(self.add)
		
		self.act_help.triggered.connect(self.showHelp)
		self.act_about.triggered.connect(self.showAbout)
		
		# extend menu bar
		self.addActions()
		
		logs.write_log('', verbosity = 'DEBUG', comment = 'initialization done...')

	def penColor(self):
		# opens dialog to change pen color
		newColor = QtGui.QColorDialog.getColor(self.scribbleArea.penColor())
		if newColor.isValid():
			self.scribbleArea.setPenColor(newColor)
			logs.write_log(newColor, verbosity = 'DEBUG', comment = 'new color')

	def penWidth(self):
		# opens dialog to change pen width
		newWidth, ok = QtGui.QInputDialog.getInteger(self, "e-draw",
			app.translate("wnd_main","Select pen width:"), 
			self.scribbleArea.penWidth(), 1, 50, 1)
		if ok:
			self.scribbleArea.setPenWidth(newWidth)
			logs.write_log(newWidth, verbosity = 'DEBUG', comment = 'new width')
			
	def undo(self):
		if not self.scribbleArea.history.removeLast(): pass #print 'empty history'
		self.scribbleArea.redraw()
		
	def add(self):
		if not os.path.exists(PATH_TEMP):
			try: 
				os.makedirs(PATH_TEMP)
			except:
				QMessageBox.critical(self.parent, "Error occured", "Cannot create directory " + PATH_TEMP +
					" to save session data, please check writing permissions.", QMessageBox.Ok)	
		return self.scribbleArea.saveImage(os.path.join(PATH_TEMP, str(time.time()) + '.' + FORMAT), FORMAT)
			
	def clearImage(self):
		# triggered on pressing 'Clear' (Shift+X)
		if self.scribbleArea.modified == True:
			reply = QtGui.QMessageBox.question(self, app.translate("wnd_main", "Clear"),
				app.translate("wnd_main", "Do you want to clear the canvas?"), 
				QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, 
				QtGui.QMessageBox.No)
			
			if reply == QtGui.QMessageBox.Yes:
				# clears image
				self.scribbleArea.image.fill(QtGui.qRgb(255, 255, 255))
				self.scribbleArea.modified = False
				self.scribbleArea.update()
				
				logs.write_log('', verbosity = 'DEBUG', comment = 'image cleared...')
				logs.write_log(self.scribbleArea.modified, verbosity = 'DEBUG', comment = 'self.scribbleArea.modified')
			else: 
				pass
		
	def saveFile(self):
		# opens dialog to save file with selected file type
		fileFormat = self.sender().data()
		initialPath = QtCore.QDir.currentPath() + '/untitled.' + fileFormat
		fileName = QtGui.QFileDialog.getSaveFileName(self, 
			app.translate("wnd_main", "Save As..."), initialPath,
			".%s Files (*.%s);;All Files (*)" % (fileFormat.lower(), fileFormat))
		if fileName:
			return self.scribbleArea.saveImage(fileName, fileFormat)
		return False
        
	def addActions(self):
		# creates sub menus for Save As...
		for format in QtGui.QImageWriter.supportedImageFormats():
			format = str(format)

			text = "." + format.lower()

			action = QtGui.QAction(text, self, triggered=self.saveFile)
			action.setData(format)
			
			self.saveAsActs.append(action)
			
		for action in self.saveAsActs:
			self.act_saveas.addAction(action)
		
	def showHelp(self):
		# opens help dialog
		logs.write_log('', verbosity = 'DEBUG', comment = 'help showed...')
		
		QtGui.QDialog.__init__(self)
		self.helpForm = uic.loadUi('help.ui')
		self.helpForm.show()
		
		self.connect(self.helpForm.btn_back, QtCore.SIGNAL('clicked()'), 
			self.helpForm.tbr_help, QtCore.SLOT("backward()"))
		self.connect(self.helpForm.btn_home, QtCore.SIGNAL('clicked()'), 
			self.helpForm.tbr_help, QtCore.SLOT("home()"))
		self.connect(self.helpForm.tbr_help, QtCore.SIGNAL("sourceChanged(QUrl)"), 
			self.updatePageTitle)
			
		self.helpForm.tbr_help.setSource((QtCore.QUrl.fromLocalFile("../docs/help/index.html")))
		
	def showAbout(self):
		# opens about dialog
		QtGui.QMessageBox.about(self, app.translate("wnd_main", "About"), 
                """<p>The <b>e-draw</b> is a small Paint-like cross platform program
                that has the most basic functionality including localization, undo, 
				quick saves and brush settings. The program has shortcuts for each action.</p>
                
                <p>It is an open source project; you can always find the latest
                version of code at <a href="https://github.com/dae-eklen/e-draw">github</a>
                page.</p> 
                
                <p>Current version: 1.0</p>
                """)
			
	def updatePageTitle(self):
		# used to update label for title (helpForm.lab_title) in help dialog
		self.helpForm.lab_title.setText(self.helpForm.tbr_help.documentTitle())  
					
	def closeEvent(self, event):
		# called on close (Ctrl+Q)
		reply = QtGui.QMessageBox.question(self, app.translate("wnd_main", "Exit"),
			app.translate("wnd_main", "Are you sure to quit?"), 
			QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, 
			QtGui.QMessageBox.No)
			
		if reply == QtGui.QMessageBox.Yes:
			logs.write_log('', verbosity = 'DEBUG', comment = 'quiting...')
			
			try:
				sys.exit(self.helpForm)
			except AttributeError:
				pass
			event.accept()
		else:
			event.ignore() 


if __name__ == "__main__":
	logs = log.Log(fileName = 'test.log', writeVerbosity = 'DEBUG')
	logs.write_log('', verbosity = 'DEBUG', comment = 'starting...')
	
	app = QtGui.QApplication(sys.argv)
	
	# i18n	
	translator_my = QtCore.QTranslator()
	translator_my.load('i18n/i18n_' + QtCore.QLocale.system().name() + '.qm')
	#translator_my.load('i18n/i18n_ru_Ru.qm')
	app.installTranslator(translator_my)
	
	translator_qt = QtCore.QTranslator()
	translator_qt.load('i18n/qt_' + QtCore.QLocale.system().name()[:2] + '.qm')	
	#translator_qt.load('i18n/qt_ru.qm')
	app.installTranslator(translator_qt)
	
	translator_help = QtCore.QTranslator()
	translator_help.load('i18n/help_' + QtCore.QLocale.system().name() + '.qm')	
	#translator_help.load('i18n/help_ru_Ru.qm')
	app.installTranslator(translator_help)
	
	logs.write_log(QtCore.QLocale.system().name(), verbosity = 'DEBUG', comment = 'language set...')
	
	# show	
	myApp = MainWindow()
	myApp.show()
	
	sys.exit(app.exec_())
