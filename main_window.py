import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QTextEdit, QPushButton, QLabel, QSplitter, 
                           QStatusBar, QAction, QFileDialog, QMessageBox,
                           QPlainTextEdit)
from PyQt5.QtGui import QFont, QColor, QPainter, QTextFormat
from PyQt5.QtCore import Qt, QSize, QRect, pyqtSlot

from syntax_highlighter import CppSyntaxHighlighter
from lexer import Lexer
from parser import Parser
from analyzer import SemanticAnalyzer
from error_handler import ErrorHandler

# Line number area widget
class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.codeEditor = editor

    def sizeHint(self):
        return QSize(self.codeEditor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)

# Code editor with line numbers
class CodeEditorWithLineNumbers(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lineNumberArea = LineNumberArea(self)
        
        # Connect signals
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        #self.cursorPositionChanged.connect(self.highlightCurrentLine)
        
        # Initialize
        self.updateLineNumberAreaWidth(0)
        #self.highlightCurrentLine()
        
        # Set font for code editor
        font = QFont("Courier New", 10)
        self.setFont(font)
        
        # Set placeholder text
        self.setPlaceholderText("Enter your C++ code here...")

    def lineNumberAreaWidth(self):
        digits = 1
        max_value = max(1, self.blockCount())
        while max_value >= 10:
            max_value //= 10
            digits += 1
            
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), QColor(Qt.lightGray).lighter(120))

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(QColor(Qt.darkGray))
                painter.drawText(0, top, self.lineNumberArea.width() - 2, 
                                self.fontMetrics().height(),
                                Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            blockNumber += 1

    """def highlightCurrentLine(self):
        extraSelections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            lineColor = QColor(Qt.yellow).lighter(180)
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)

        self.setExtraSelections(extraSelections)"""

# Main window class
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        # Set window properties
        self.setWindowTitle("QuadPals Code Compiler-Validator")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create splitter for code and output panels
        splitter = QSplitter(Qt.Vertical)
        
        # Code editor with line numbers
        self.code_editor = CodeEditorWithLineNumbers()
        
        # Apply syntax highlighting
        self.highlighter = CppSyntaxHighlighter(self.code_editor.document())
        
        # Output panel
        self.output_panel = QTextEdit()
        self.output_panel.setFont(QFont("Courier New", 10))
        self.output_panel.setReadOnly(True)
        
        # Add widgets to splitter
        splitter.addWidget(self.code_editor)
        splitter.addWidget(self.output_panel)
        splitter.setSizes([int(self.height() * 0.7), int(self.height() * 0.3)])
        
        # Add splitter to main layout
        main_layout.addWidget(splitter)
        
        # Create button layout
        button_layout = QHBoxLayout()
        
        # Validate button
        self.validate_button = QPushButton("Validate Code")
        self.validate_button.clicked.connect(self.validate_code)
        button_layout.addWidget(self.validate_button)
        
        # Clear button
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_fields)
        button_layout.addWidget(self.clear_button)
        
        # Add button layout to main layout
        main_layout.addLayout(button_layout)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Create menu bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")
        
        # Open file action
        open_action = QAction("Open", self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        # Save file action
        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Initialize analysis modules
        self.error_handler = ErrorHandler()
        
    def validate_code(self):
        code = self.code_editor.toPlainText()
        self.output_panel.clear()
        
        if not code.strip():
            self.output_panel.append("Error: No code to validate.")
            return
        
        self.status_bar.showMessage("Validating code...")
        
        # Step 1: Lexical Analysis
        try:
            lexer = Lexer(code)
            tokens = lexer.tokenize()
            self.output_panel.append("Lexical Analysis: Completed")
            self.output_panel.append(f"Tokens identified: {len(tokens)}")
        except Exception as e:
            self.output_panel.append(f"Lexical Analysis Error: {str(e)}")
            self.status_bar.showMessage("Validation failed at lexical analysis")
            return
        
        # Step 2: Syntax Analysis
        try:
            parser = Parser(tokens)
            syntax_result = parser.parse()
            if syntax_result['valid']:
                self.output_panel.append("Syntax Analysis: Completed")
            else:
                self.output_panel.append("Syntax Analysis: Failed")
                for error in syntax_result['errors']:
                    self.output_panel.append(f"  - {error}")
                self.status_bar.showMessage("Validation failed at syntax analysis")
                return
        except Exception as e:
            self.output_panel.append(f"Syntax Analysis Error: {str(e)}")
            self.status_bar.showMessage("Validation failed at syntax analysis")
            return
        
        # Step 3: Semantic Analysis
        try:
            semantic_analyzer = SemanticAnalyzer(syntax_result['ast'])
            semantic_result = semantic_analyzer.analyze()
            if semantic_result['valid']:
                self.output_panel.append("Semantic Analysis: Completed")
            else:
                self.output_panel.append("Semantic Analysis: Failed")
                for error in semantic_result['errors']:
                    self.output_panel.append(f"  - {error}")
                self.status_bar.showMessage("Validation failed at semantic analysis")
                return
        except Exception as e:
            self.output_panel.append(f"Semantic Analysis Error: {str(e)}")
            self.status_bar.showMessage("Validation failed at semantic analysis")
            return
        
        # All validations passed
        self.output_panel.append("\n✓ Code is valid for execution!")
        self.status_bar.showMessage("Validation completed successfully")
        
    def clear_fields(self):
        self.code_editor.clear()
        self.output_panel.clear()
        self.status_bar.showMessage("Ready")
        
    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open C++ File", "", "C++ Files (*.cpp *.h *.hpp);;All Files (*)")
        if file_path:
            try:
                with open(file_path, 'r') as file:
                    self.code_editor.setPlainText(file.read())
                self.status_bar.showMessage(f"Opened: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not open file: {str(e)}")
                
    def save_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save C++ File", "", "C++ Files (*.cpp *.h *.hpp);;All Files (*)")
        if file_path:
            try:
                with open(file_path, 'w') as file:
                    file.write(self.code_editor.toPlainText())
                self.status_bar.showMessage(f"Saved: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save file: {str(e)}")