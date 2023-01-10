# QT5_PDF_OCR_Tool_Rev_

import sys
import os
import pytesseract
import ghostscript as gs

from PyQt5.QtCore import Qt, QUrl, QFileInfo, QThread, pyqtSignal, pyqtSlot, QEventLoop, QTimer
from PyQt5.QtGui import QImage, QPixmap, QPalette, QPainter
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
from PyQt5.QtWidgets import QLabel, QSizePolicy, QScrollArea, QMessageBox, QMainWindow, QMenu, QAction
from PyQt5.QtWidgets import QApplication, qApp, QFileDialog, QListWidget, QSplitter, QTextEdit, QFileSystemModel
# from pdf2image import convert_from_path
from multiprocessing import Pool
from PIL import Image

# example of using QfilesystemModel
class FileExplorer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('File Explorer')
        self.setGeometry(300, 300, 350, 300)
        self.model = QFileSystemModel()
        self.model.setRootPath('C:/')
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index('C:/'))
        self.tree.clicked.connect(self.onClicked)
        self.setCentralWidget(self.tree)

    def onClicked(self, index):
        QMessageBox.information(self, "QTreeView", "You clicked: " + self.model.fileName(index))




def os_path_join(arg1, arg2):
    osjoiner = '/'
    if '/' not in os.path.join('C:','test'):
        osjoiner = '\\'

    return os.path.join(arg1, arg2).replace('/', osjoiner)


def extractImage_fz(report):
    report_file = os_path_join(report.filepath, report.filename)
    ifile = os.path.splitext(report.filename)[0] +'.png'

    image_file = os_path_join(report.filepath, ifile)
    if os.path.exists(image_file):
        return

    print  ("Extracting Images in ", report_file, image_file)
    if True:
        # images = convert_from_path(report_file, 1000, first_page=1, last_page=1, fmt='png')
        # modify method to use ghostscript instead of pdf2image

        # gs_args = ['-sDEVICE=png16m', '-dFirstPage=1', '-dLastPage=1', '-r1000', '-o', image_file, report_file]
        # gs.Ghostscript(*gs_args)
        # using a os shell command instead of ghostscript
        mygs = 'gswin64c.exe '
        print(mygs +'-sDEVICE=png16m -dFirstPage=1 -dLastPage=1 -r1000 -o ' + image_file + ' ' + report_file)
        os.system(mygs + '-sDEVICE=png16m -dFirstPage=1 -dLastPage=1 -r1000 -o ' + image_file + ' ' + report_file)

        #image = images[0]
        # iwidth = image.width    # image width
        # iheight_t = 0  # round(image.height/ 6)  # image height
        # iheight_b = round(image.height/ 3)  # image height
        #
        # print ("Image size: ", iwidth, iheight_t, iheight_b)
        # image = image.crop((0,iheight_t,iwidth, iheight_b))
        # image = image.crop()

        # image.save(image_file)
    else:

    #except:
        print("Error in extracting image from ", report_file)
        report.newname = report.filename
    return

class reportData:
    def __init__(self, filename=None, image=None, newname=None, filepath=None):
        self.filename = filename
        self.image = image
        self.newname = newname
        self.filepath = filepath
        self.list = []
        self.index = 0

    def add(self, reportDataItem):
        if self.list != None:
            reportDataItem.index = len(self.list)
        else:
            reportDataItem.index = 0

        self.list.append(reportDataItem)

    def get(self, index):
        return self.list[index]

    def length(self):
        return len(self.list)

    def clear(self):
        self.list.clear()

    def remove(self, index):
        self.list.pop(index)

    def get_list(self):
        return self.list

    def set_list(self, list):
        self.list = list

    def update(self, index, value):
        self.list[index] = value

    def renameReports(self):
        for record in range(self.length()):
            report = self.get(record)
            if report.image != None and report.newname != None and report.filename != None and report.filepath != None :
                source = os_path_join(report.filepath, report.filename)
                destination = os_path_join(report.filepath, report.newname)
                mypix = os_path_join(report.filepath, report.image)
                newpix = report.newname
                mynewpix = os_path_join(report.filepath, newpix.replace('.pdf', '.png'))

                try:   # rename if file exists and isn't conflicted with another file
                    if os.path.exists(source) and not os.path.exists(destination) and source != destination:
                        os.rename(source, destination)
                        report.filename = report.newname
                        print("Renamed ", source, " to ", destination)

                    if os.path.exists(mypix) and not os.path.exists(mynewpix) and mypix != mynewpix:
                        os.rename(mypix, mynewpix)
                        report.image = newpix.replace('.pdf', '.png')
                        print("Renamed ", mypix, " to ", mynewpix)

                    self.update(record, report)

                except:
                    print("Error in renaming ", source, destination)

        print ("Renaming reports >> ", self.length () , " reports processed"  )


class QImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.MyReports = reportData()
        self.MyHomePath = os.path.expanduser("~")
        self.CurrentPath = self.MyHomePath
        self.RenderPix = False
        self.printer = QPrinter()
        self.scaleFactor = 0.0

        self.setHomePath()
        self.createWidgets()
        self.createLayouts()
        self.createActions()
        self.createMenus()

        self.fileList.setEnabled(True)
        self.autoScanAct.setEnabled(True)

        self.setWindowTitle("Image Viewer")
        self.resize(1200, 800)

        self.populateDirectoryList('')
        self.populateReportList(self.MyHomePath)
        self.populateFileList(self.MyHomePath)

    def setHomePath(self):
        try:
            self.MyHomePath = os.environ['Home']
            if not os.path.exists(self.MyHomePath):
                raise KeyError
        except KeyError:
            print("Home environment variable not found, using home folder of current user")
            self.MyHomePath = os.path.expanduser("~")
            os.environ['Home'] = self.MyHomePath

    def createWidgets(self):
        self.imageLabel = QLabel()
        self.imageLabel.setBackgroundRole(QPalette.Base)
        self.imageLabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.imageLabel.setScaledContents(True)

        self.scrollArea = QScrollArea()
        self.scrollArea.setBackgroundRole(QPalette.Dark)
        self.scrollArea.setWidget(self.imageLabel)
        self.scrollArea.setVisible(False)

        self.directoryList = QListWidget()
        self.directoryList.doubleClicked.connect(self.selectDirectory)

        self.fileList = QListWidget(self)
        self.fileList.setSelectionMode(QListWidget.SingleSelection)
        self.fileList.setEnabled(False)
        self.fileList.itemClicked.connect(self.listopen)

        self.reportList = QListWidget(self)
        self.reportList.setSelectionMode(QListWidget.SingleSelection)
        self.reportList.setEnabled(False)
        self.reportList.itemClicked.connect(self.listConvert)

        self.groupList = QListWidget(self)
        self.groupList.setSelectionMode(QListWidget.SingleSelection)
        self.groupList.setEnabled(False)
        self.groupList.itemClicked.connect(self.listProcess)

        self.textEdit = QTextEdit()
        self.textEdit.setReadOnly(True)

        self.imageName = QTextEdit()
        self.imageName.setAlignment(Qt.AlignCenter)
        self.imageName.setReadOnly(True)

        self.imageTag = QTextEdit()
        self.imageTag.setAlignment(Qt.AlignCenter)
        self.imageTag.setReadOnly(False)

    def createLayouts(self):
        E_splitter = QSplitter(Qt.Horizontal)
        E_splitter.addWidget(self.imageName)
        E_splitter.addWidget(self.imageTag)

        V_splitter = QSplitter(Qt.Vertical)
        V_splitter.addWidget(E_splitter)
        V_splitter.addWidget(self.scrollArea)
        V_splitter.addWidget(self.textEdit)
        V_splitter.setSizes([5, 450, 150])

        H_splitter = QSplitter(Qt.Horizontal)
        H_splitter.addWidget(self.directoryList)
        H_splitter.addWidget(self.reportList)
        H_splitter.addWidget(self.fileList)
        H_splitter.addWidget(self.groupList)

        # combine the two splitters
        H_splitter.addWidget(V_splitter)
        H_splitter.setSizes([0, 130, 130, 260, 700])

        self.setCentralWidget(H_splitter)
        timer = QTimer()

    def timerEvent(self, event):
        if event.timerId() == self.timer.timerId():
            self.timer.stop()
            if self.autoScanAct.isChecked():
                self.doRescan()
        else:
            super(QImageViewer, self).timerEvent(event)

    def startTimer(self, interval: int):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.timerEvent)
        self.timer.start(interval)

    def chooseFolder(self):
        directory = QFileDialog.getExistingDirectory(self, "Choose Directory")
        self.MyHomePath = directory
        self.CurrentPath = directory
        self.setWindowTitle("Image Viewer : " + directory)
        self.populateDirectoryList(directory)
        self.populateFileList(directory)
        os.environ['HOME'] = self.MyHomePath

    def populateDirectoryList(self, new_path):
        if new_path == "":
            new_path = self.MyHomePath

        self.directoryList.clear()
        self.directoryList.addItem(new_path)
        self.CurrentPath = new_path
        self.directoryList.addItem("..")

        # store the directory information in a list to be sorted
        dir_list = os.listdir(new_path)
        dir_list.sort()

        for this_dir in dir_list:
            # filter out the files and hidden directories - only show directories
            if os.path.isdir(os_path_join(new_path, this_dir)) and not this_dir.startswith('.'):
                self.directoryList.addItem(new_path + "/" + this_dir)


    def selectDirectory(self, item):
        self.fileList.clear()
        directory = self.directoryList.currentItem().text()
        # print (directory)

        if directory == "..":
            directory = os.path.dirname(self.MyHomePath)
            if os.path.exists(directory):
                self.CurrentPath = directory
            else:
                directory = os.path.expanduser("~")

        if os.path.exists(directory):
            self.setWindowTitle("Image Viewer : " + directory)
            self.populateDirectoryList(directory)
            self.populateFileList(directory)

    def populateFileList(self, directory):
        self.fileList.clear()

        for file in os.listdir(directory):
            if file.endswith('.png') or file.endswith('.jpg') or file.endswith('.jpeg') or file.endswith(
                    '.bmp') or file.endswith('.gif'):
                self.fileList.addItem(file)
        self.fileList.sortItems( Qt.AscendingOrder )

        self.RenderPix = True
        self.doAutoScanOCR

    def doAutoScanOCR(self):
    # routine to update the MyReportList with the latest OCR results
        doAutoScanOCR = self.autoScanAct.isChecked()
        if doAutoScanOCR:
            for file in self.fileList:
                reportName = file.replace('.png', '.pdf')
                for record in self.MyReports.get_list():
                    if record.filename == reportName:
                        if record.filename == record.newname:
                            ipath = os.path.pathsep (file)
                            newtext = self.readImage (file, ipath)
                            newserial = self.readSerial (file, ipath)
                            if not ('<' in newserial):
                                self.imageTag.setText(newserial)
                                record.image = file
                                record.newname = newserial + '.pdf'
                                self.MyReports.update_record (record.index, record)


    def populateReportList(self, directory):
        doAutoScanOCR = False
        if self.autoScanAct is not None:
            doAutoScanOCR = self.autoScanAct.isChecked()

        if not doAutoScanOCR:
            self.groupList.clear()
            self.MyReports.clear()
        self.reportList.clear()

        for file in os.listdir(directory):
            if file.endswith('.pdf'):
                self.reportList.addItem(file)
                image_file = file.replace('.pdf', '.png')
                NewReport = reportData(filename=file,  image=image_file ,filepath=directory)
                self.MyReports.add(NewReport)

        if self.RenderPix == True:
            with Pool(4) as p:
                if self.MyReports.length() > 0:
                    p.map(extractImage_fz, self.MyReports.get_list())
                    self.populateFileList(directory) # refresh the image file list

        self.reportList.sortItems( Qt.AscendingOrder )
        self.populateGroupList()
        self.reportList.setEnabled(True)
        self.groupList.setEnabled(True)

    def listConvert(self, item):
        pass

    def listProcess(self, item):
        pass

    def listopen(self):
        self.open("list")

    def open(self, file_name):
        options = QFileDialog.Options()
        current_path = self.CurrentPath

        # fileName = QFileDialog.getOpenFileName(self, "Open File", QDir.currentPath())
        try:
            if file_name == "list":
                file_name = self.fileList.currentItem().text()
                # print('List File Select ', file_name)
                file_name = os_path_join(current_path, self.fileList.currentItem().text())
            else:
                file_name = self.MyHomePath
                fileName, _ = QFileDialog.getOpenFileName(self, 'File Dialog - Select Image File Name', file_name,
                                                          'Images (*.png *.jpeg *.jpg *.bmp *.gif)', options=options)
        except:
            # print('Error File Select ', file_name)
            file_name = self.MyHomePath
            fileName, _ = QFileDialog.getOpenFileName(self, 'File Dialog - Select Image File Name', file_name,
                                                      'Images (*.png *.jpeg *.jpg *.bmp *.gif)', options=options)

        if file_name != self.MyHomePath:
            fileName = file_name

        if fileName:
            self.textEdit.clear()
            self.imageName.setPlainText(fileName)
            self.setNewName.setEnabled(True)

            image = QImage(fileName)
            if image.isNull():
                QMessageBox.information(self, "Image Viewer", "Cannot load %s." % fileName)
                return
            self.imageLabel.setPixmap(QPixmap.fromImage(image))

            self.scaleFactor = 1.0

            self.scrollArea.setVisible(True)
            self.printAct.setEnabled(True)
            self.fitToWidthAct.setEnabled(True)
            self.fitToWindowAct.setEnabled(True)
            self.readImageAct.setEnabled(True)
            self.updateActions()

            if not self.fitToWindowAct.isChecked():
                self.fitToWidth()

    def print_(self):
        dialog = QPrintDialog(self.printer, self)
        if dialog.exec_():
            painter = QPainter(self.printer)
            rect = painter.viewport()
            size = self.imageLabel.pixmap().size()
            size.scale(rect.size(), Qt.KeepAspectRatio)
            painter.setViewport(rect.x(), rect.y(), size.width(), size.height())
            painter.setWindow(self.imageLabel.pixmap().rect())
            painter.drawPixmap(0, 0, self.imageLabel.pixmap())

    def zoomIn(self):
        self.scaleImage(1.25)

    def zoomOut(self):
        self.scaleImage(0.8)

    def normalSize(self):
        self.imageLabel.adjustSize()
        self.scaleFactor = 1.0
        self.scaleImage(1.0)

    def fitToWidth(self):
        if self.scrollArea.width() > 0 and self.imageLabel.pixmap().width() > 0:
            zoomfactor = self.scrollArea.width() / self.imageLabel.pixmap().width()
        else:
            zoomfactor = 1

        self.imageLabel.adjustSize()
        self.scaleFactor = zoomfactor
        self.scaleImage(1.0)

        self.updateActions()

    def fitToWindow(self):
        fitToWindow = self.fitToWindowAct.isChecked()
        self.scrollArea.setWidgetResizable(fitToWindow)
        if not fitToWindow:
            self.normalSize()

        self.updateActions()

    def readImage(self, ifile=None, ipath=None):
        if ifile is None or not ifile:
            text = '<>'
        else:
            text = '<' + ifile + '>'

        if ifile == None or ipath == None:
            file_name = self.imageName.toPlainText()
            # ipath = os.path.dirname(file_name)
            ifile = os.path.basename(file_name)
        else:
            file_name = os_path_join(ipath, ifile)

        self.imageTag.setPlainText("<<Processing Image : " + file_name + '>>')

        if file_name:
            # Load the image file into a pillow object
            try:
                image = Image.open(file_name)
            except:
                return '<' + ifile + '>'

            iwidth = image.width  # image width
            if image.height < 3870:
                iheight_b = round(image.height )
                iheight_t = 0

            else:
                iheight_b = 3870
                iheight_t = round(iheight_b / 2)


            new_image = image.crop((0, iheight_t, iwidth, iheight_b))

            if new_image.mode == 'RGBA':
                new_image = new_image.convert('RGB')

            if new_image.mode == 'RGB':
                engine = pytesseract.image_to_string(new_image, lang='eng')

                text = engine
                serialNumber = self.extractSerialNumber(text)

                self.imageTag.clear()
                self.imageTag.setPlainText(serialNumber)
                self.textEdit.setPlainText(text)

            else:
                QMessageBox.information(self, "OCR Text", "Image is not in RGB format")
            return text

    def extractSerialNumber(self, text):
        lines = text.split('\n')
        search_terms = ['ITCS', 'RSE', 'PME', 'R3L', 'WBS', 'ECA', 'ECB', 'VR', 'RMS']
        for i, line in enumerate(lines, 1):
            if '/' in line:
                for search_term in search_terms:
                    if search_term in line:
                        serial_number_line = lines[i - 1]

                        serial_number_parts = serial_number_line.split(search_term)
                        if len(serial_number_parts) >= 2:
                            serial_number_text = search_term + serial_number_parts[1].strip()
                            serial_info = serial_number_text.split('/')
                            if len(serial_info) >= 2:
                                serial_data = serial_info[0].strip() + '-' + serial_info[1].strip()
                                return serial_data.replace(' ', '')

        return '<Serial Number Not Found>'

    def about(self):
        QMessageBox.about(self, "About Image Viewer",
                          "<p>The <b>Image Viewer</b> example shows how to combine "
                          "QLabel and QScrollArea to display an image. QLabel is "
                          "typically used for displaying text, but it can also display "
                          "an image. QScrollArea provides a scrolling view around "
                          "another widget. If the child widget exceeds the size of the "
                          "frame, QScrollArea automatically provides scroll bars.</p>"
                          "<p>The example demonstrates how QLabel's ability to scale "
                          "its contents (QLabel.scaledContents), and QScrollArea's "
                          "ability to automatically resize its contents "
                          "(QScrollArea.widgetResizable), can be used to implement "
                          "zooming and scaling features.</p>"
                          "<p>In addition the example shows how to use QPainter to "
                          "print an image.</p>")

    def createActions(self):
        self.chooseFolderAct = QAction("&Home Dir...", self, shortcut="Ctrl+O", triggered=self.chooseFolder)
        self.doReloadAct = QAction("&Reload", self, shortcut="Ctrl+R", triggered=self.doReload)
        self.openAct = QAction("&Open...", self, shortcut="Ctrl+O", triggered=self.open)
        self.printAct = QAction("&Print...", self, shortcut="Ctrl+P", enabled=False, triggered=self.print_)
        self.exitAct = QAction("E&xit", self, shortcut="Ctrl+Q", triggered=self.close)
        self.zoomInAct = QAction("Zoom &In (25%)", self, shortcut="Ctrl++", enabled=False, triggered=self.zoomIn)
        self.zoomOutAct = QAction("Zoom &Out (25%)", self, shortcut="Ctrl+-", enabled=False, triggered=self.zoomOut)
        self.normalSizeAct = QAction("&Normal Size", self, shortcut="Ctrl+S", enabled=False, triggered=self.normalSize)
        self.fitToWidthAct = QAction("Fit to &Width", self, shortcut="Ctrl+w", enabled=False, triggered=self.fitToWidth)
        self.fitToWindowAct = QAction("&Fit to Window", self, enabled=False, checkable=True, shortcut="Ctrl+F",
                                      triggered=self.fitToWindow)
        self.readImageAct = QAction("&Decode Image", self, shortcut="Ctrl+d", enabled=False, triggered=self.readImage)
        self.aboutAct = QAction("&About", self, triggered=self.about)
        self.aboutQtAct = QAction("About &Qt", self, triggered=qApp.aboutQt)
        self.setNewName = QAction("Set &New Name", self, shortcut="Ctrl+n", enabled=False, triggered=self.imageTagChanged)
        self.updateGroupList = QAction("Update &Group List", self, shortcut="Ctrl+g", enabled=True, triggered=self.populateGroupList)
        self.renameAllReports = QAction("Rename &All Reports", self, shortcut="Ctrl+r", enabled=True, triggered=self.renameAllReports)
        self.autoScanAct = QAction("Auto &Scan", self, shortcut="Ctrl+a", enabled=False, checkable=True, triggered=self.autoScan)

    def createMenus(self):
        self.fileMenu = QMenu("&File", self)
        self.fileMenu.addAction(self.chooseFolderAct)
        self.fileMenu.addAction(self.doReloadAct)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.printAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.viewMenu = QMenu("&View", self)
        self.viewMenu.addAction(self.zoomInAct)
        self.viewMenu.addAction(self.zoomOutAct)
        self.viewMenu.addAction(self.normalSizeAct)
        self.viewMenu.addAction(self.fitToWidthAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.fitToWindowAct)

        self.ocrMenu = QMenu("&OCR", self)
        self.ocrMenu.addAction(self.readImageAct)
        self.ocrMenu.addAction(self.setNewName)
        self.ocrMenu.addAction(self.updateGroupList)
        self.ocrMenu.addAction(self.renameAllReports)
        self.ocrMenu.addAction(self.autoScanAct)

        self.helpMenu = QMenu("&Help", self)
        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addAction(self.aboutQtAct)

        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.viewMenu)
        self.menuBar().addMenu(self.ocrMenu)
        self.menuBar().addMenu(self.helpMenu)

    def updateActions(self):
        self.zoomInAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.zoomOutAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.fitToWidthAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.normalSizeAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.readImageAct.setEnabled(not self.fitToWindowAct.isChecked())

    def scaleImage(self, factor):
        self.scaleFactor *= factor
        self.imageLabel.resize(self.scaleFactor * self.imageLabel.pixmap().size())

        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), factor)
        self.repaint()

        self.zoomInAct.setEnabled(self.scaleFactor < 3.0)
        self.zoomOutAct.setEnabled(self.scaleFactor > 0.333)

    def adjustScrollBar(self, scrollBar, factor):
        scrollBar.setValue(int(factor * scrollBar.value()
                               + ((factor - 1) * scrollBar.pageStep() / 2)))

    def populateimageList(self, directory):
        self.imageList.clear()
        for file in os.listdir(directory):
            if file.endswith('.png') or file.endswith('.jpg') or file.endswith('.jpeg') or file.endswith(
                    '.bmp') or file.endswith('.gif'):
                self.imageList.addItem(file)

    def imageTagChanged(self):
        file_name = self.imageName.toPlainText()
        ipath = os.path.dirname(file_name)
        ifile = os.path.basename(file_name)

        print ("Image file : " , ifile  )

        serialNumber = self.imageTag.toPlainText()
        newname = serialNumber.replace(' ', '')
        newname = newname.replace('/', '_')

        print('Serial number is: ' , serialNumber)

        success = "Failed"
        if len(serialNumber) > 4:
            teststring = ifile.replace(' ', '')
            # identify the source pdf in myreports and store the serial number text in newname field
            for report in self.MyReports.get_list():
                if report.image == teststring:
                    report.newname = newname + '.pdf'
                    self.MyReports.update(report.index, report)
                    success = "Success"
                    break
        print (success)
        # self.textEdit.setText("Image Tag Updated " & file_name & " " & serialNumber & " >> " & success)

        self.populateGroupList()

    def populateGroupList(self):
        self.groupList.clear()
        for report in self.MyReports.get_list():
            if report.newname != '' and report.newname != None:
                self.groupList.addItem(report.filename + ' == ' + report.newname)
            else:
                self.groupList.addItem(report.filename + ' == ' + report.filename)

        self.groupList.sortItems( Qt.AscendingOrder)

    def doReload(self):
        print ("Reloading reports for " + self.CurrentPath)
        self.directoryList.clear()
        self.reportList.clear()
        self.fileList.clear()
        self.groupList.clear()

        self.populateDirectoryList(self.CurrentPath)
        self.populateReportList(self.CurrentPath)
        self.populateFileList(self.CurrentPath)
        self.populateGroupList()

    def renameAllReports(self):
        current_folder = self.CurrentPath
        self.MyReports.renameReports()
        self.populateGroupList()
        self.populateFileList( current_folder)
        self.populateReportList( current_folder)

    def autoScan(self):
        # once a directory is selected, scan the directory for pdf files starting with "CCF_"
        # it should be possible to stop the autoscan at any time by pressing the stop button

        current_folder = self.CurrentPath
        autoScan = self.autoScanAct.isChecked()
        autoScanOff = not autoScan

        self.fileMenu.setEnabled(autoScanOff)
        self.viewMenu.setEnabled(autoScanOff)
        # self.helpMenu.setEnabled(autoScanOff)
        # self.ocrMenu.setEnabled(autoScanOff)

        # enable the timer to periodically scan the report directory
        # sets the timer to scan every 60 seconds
        if autoScan:
            self.timer.start(60000)
        else:
            self.timer.stop()

    # set a timed routine to launch the populateReportList function
    def timerEvent(self, event):
        current_folder = self.CurrentPath
        self.populateReportList( current_folder)
        self.populateFileList( current_folder)
        self.populateGroupList()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    imageViewer = QImageViewer()
    imageViewer.show()
    sys.exit(app.exec_())





