import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QTextEdit, QPushButton, QSplitter, QStatusBar, 
                           QPlainTextEdit)
from PyQt5.QtGui import QFont, QColor, QPainter 
from PyQt5.QtCore import Qt, QSize, QRect 

from syntax_highlighter import SyntaxHighlighter
from lexer import Lexer
from parser import Parser
from analyzer import SemanticAnalyzer
from error_handler import ErrorHandler

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.codeEditor = editor

    def sizeHint(self):
        return QSize(self.codeEditor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)

class CodeEditorWithLineNumbers(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lineNumberArea = LineNumberArea(self)
        
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        
        # Initialize
        self.updateLineNumberAreaWidth(0)
        #self.highlightCurrentLine()
        
        # Set font for code editor
        font = QFont("Courier New", 12)
        self.setFont(font)
        
        # Set placeholder text
        self.setPlaceholderText("Enter your code here...")

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
            
# Main window class
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        # Set window properties
        self.setWindowTitle("QuadPalidator")
        self.setGeometry(100, 100, 1000, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create splitter for code and output panels
        splitter = QSplitter(Qt.Vertical)
        
        self.code_editor = CodeEditorWithLineNumbers()
        self.highlighter = SyntaxHighlighter(self.code_editor.document())
        
        # Output panel
        self.output_panel = QTextEdit()
        self.output_panel.setFont(QFont("Courier New", 12))
        self.output_panel.setReadOnly(True)
        
        splitter.addWidget(self.code_editor)
        splitter.addWidget(self.output_panel)
        splitter.setSizes([int(self.height() * 0.7), int(self.height() * 0.3)])
        
        # Add splitter to main layout
        main_layout.addWidget(splitter)
        
        button_layout = QHBoxLayout()
        self.validate_button = QPushButton("Validate Code")
        self.validate_button.clicked.connect(self.validate_code)
        button_layout.addWidget(self.validate_button)
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_fields)
        button_layout.addWidget(self.clear_button)
        
        main_layout.addLayout(button_layout)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

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
        self.status_bar.showMessage("Validation completed successfully!")
        
    def clear_fields(self):
        self.code_editor.clear()
        self.output_panel.clear()
        self.status_bar.showMessage("Ready")