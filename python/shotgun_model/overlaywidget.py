# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

from tank.platform.qt import QtCore, QtGui

# load resources
from .ui import resources_rc

class OverlayWidget(QtGui.QWidget):
    """
    This class is part of the internals of the Shotgun Utils framework and 
    should not be used directly.
    
    Overlay widget that can be placed on top over any other widget. 
    This is used by the Shotgun model to indicate when data is being loaded in;
    Whenever data is fetched, the overlay widget is added on top of the specified
    QWidget so that the model can gracefully indicate that data is being fetched.
    
    The caller does not need to worry about anything - all they need to do is 
    to pass a widget to the model constructor and this widget will get the overlay
    added on top. (This widget is typically, not does not have to be, the associated view).  

    The overlay is also used by the model to report any errors that may occur as part 
    of data management.
    """
    
    MODE_OFF = 0
    MODE_SPIN = 1
    MODE_ERROR = 2
    MODE_INFO_TEXT = 3
    MODE_INFO_PIXMAP = 4
    
    def __init__(self, parent=None):
        """
        Constructor
        """
        
        QtGui.QWidget.__init__(self, parent)
        
        self._parent = parent
        
        # hook up a listener to the parent window so we 
        # can resize the overlay at the same time as the parent window
        # is being resized.
        filter = ResizeEventFilter(self._parent)
        filter.resized.connect(self._on_parent_resized)
        self._parent.installEventFilter(filter)
        
        # make it transparent
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        
        # turn off the widget
        self.setVisible(False)
        self._mode = OverlayWidget.MODE_OFF
        
        # setup spinner timer
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self.on_animation)
        self._spin_angle = 0
        
        self._message_pixmap = None
        self._message = None
        self._sg_icon = QtGui.QPixmap(":/tk_framework_shotgunutils.shotgun_model/sg_logo.png")
 
    def _on_parent_resized(self):
        """
        Special slot hooked up to the event filter.
        When associated widget is resized this slot is being called.
        """
        # resize overlay
        self.resize(self._parent.size())
    
    def on_animation(self):
        """
        Spinner async callback to help animate the progress spinner.
        """
        self._spin_angle += 1
        if self._spin_angle == 90:
            self._spin_angle = 0
        self.repaint()
 
    def paintEvent(self, event):
        """
        Render the UI.
        """
        if self._mode == OverlayWidget.MODE_OFF:
            return
        
        painter = QtGui.QPainter()
        painter.begin(self)
        try:
            # set up semi transparent backdrop
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            overlay_color = QtGui.QColor("#1B1B1B")
            painter.setBrush( QtGui.QBrush(overlay_color))
            painter.setPen(QtGui.QPen(overlay_color))
            painter.drawRect(0, 0, painter.device().width(), painter.device().height())

            # now draw different things depending on mode
            if self._mode == OverlayWidget.MODE_SPIN:
                
                # show the spinner
                painter.translate((painter.device().width() / 2) - 40, 
                                  (painter.device().height() / 2) - 40)
                
                pen = QtGui.QPen(QtGui.QColor("#424141"))
                pen.setWidth(3)
                painter.setPen(pen)
                painter.drawPixmap( QtCore.QPoint(8, 24), self._sg_icon)
    
                r = QtCore.QRectF(0.0, 0.0, 80.0, 80.0)
                start_angle = (0 + self._spin_angle) * 4 * 16
                span_angle = 340 * 16 
    
                painter.drawArc(r, start_angle, span_angle)
            
            elif self._mode == OverlayWidget.MODE_INFO_TEXT:
                # show text in the middle
                pen = QtGui.QPen(QtGui.QColor("#888888"))
                painter.setPen(pen)            
                text_rect = QtCore.QRect(0, 0, painter.device().width(), painter.device().height())
                text_flags = QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter | QtCore.Qt.TextWordWrap
                painter.drawText(text_rect, text_flags, self._message)            
                
            elif self._mode == OverlayWidget.MODE_ERROR:
                # show error text in the center
                pen = QtGui.QPen(QtGui.QColor("#C8534A"))
                painter.setPen(pen)            
                text_rect = QtCore.QRect(0, 0, painter.device().width(), painter.device().height())
                text_flags = QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter | QtCore.Qt.TextWordWrap
                painter.drawText(text_rect, text_flags, self._message)            

            elif self._mode == OverlayWidget.MODE_INFO_PIXMAP:
                # draw image
                painter.translate((painter.device().width() / 2) - (self._message_pixmap.width()/2), 
                                  (painter.device().height() / 2) - (self._message_pixmap.height()/2) )
                
                painter.drawPixmap( QtCore.QPoint(0, 0), self._message_pixmap)
                
            
        finally:
            painter.end()
        
        
        
    ############################################################################################
    # public interface
    
    def start_spin(self):
        """
        Turn on spinning
        """
        self._timer.start(40)
        self.setVisible(True)
        self._mode = OverlayWidget.MODE_SPIN

    def show_error_message(self, msg):
        """
        Display an error message
        """
        self._timer.stop()
        self.setVisible(True)
        self._message = msg
        self._mode = OverlayWidget.MODE_ERROR
        self.repaint()
 
    def show_message(self, msg):
        """
        Show an info message
        """
        self._timer.stop()
        self.setVisible(True)
        self._message = msg
        self._mode = OverlayWidget.MODE_INFO_TEXT
        self.repaint()
        
    def show_message_pixmap(self, pixmap):
        """
        Show an info message in the form of a pixmap
        """
        self._timer.stop()
        self.setVisible(True)
        self._message_pixmap = pixmap
        self._mode = OverlayWidget.MODE_INFO_PIXMAP
        self.repaint()

    def hide(self):
        """
        Hide the overlay
        """
        self._timer.stop()
        self._mode = OverlayWidget.MODE_OFF
        self.setVisible(False)
 
        
        
class ResizeEventFilter(QtCore.QObject):
    """
    Event filter which emits a resized signal whenever
    the monitored widget resizes. This is so that the overlay wrapper
    class can be informed whenever the Widget gets a resize event.
    """
    resized = QtCore.Signal()

    def eventFilter(self,  obj,  event):
        # peek at the message
        if event.type() == QtCore.QEvent.Resize:
            # re-broadcast any resize events
            self.resized.emit()
        # pass it on!
        return False
        