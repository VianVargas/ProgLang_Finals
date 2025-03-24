from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, QColor

class SyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.highlighting_rules = []
        
        # Format for keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(0, 0, 255)) 
        keyword_format.setFontWeight(QFont.Bold)
        
        # Keywords Scope
        keywords = [
            "bool", "break", "case", "char", "class", "continue", "default",
            "do", "double", "else", "false", "float", "for", "if", "int", "long",
            "return", "short", "string", "switch", "true", "while"
        ]
        
        for word in keywords:
            pattern = QRegExp("\\b" + word + "\\b")
            self.highlighting_rules.append((pattern, keyword_format))
        
        # Format for operators
        operator_format = QTextCharFormat()
        operator_format.setForeground(QColor(150, 0, 150))  # Purple
        operator_format.setFontWeight(QFont.Bold)
        
        operators = [
            "=", "==", "!=", "<", "<=", ">", ">=", "\\+", "-", "\\*", "/", "%",
            "\\+=", "-=", "\\*=", "/=", "%=", "\\+\\+", "--", "&&", "\\|\\|", "!",
            "&", "\\|", "\\^", "~", "<<", ">>", ">>=", "<<=", "&=", "\\|=", "\\^="
        ]
        
        for op in operators:
            pattern = QRegExp(op)
            self.highlighting_rules.append((pattern, operator_format))
        
        # Format for numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor(0, 150, 0))  # Green
        pattern = QRegExp("\\b[0-9]+\\b")
        self.highlighting_rules.append((pattern, number_format))
        
        # Format for strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor(255, 0, 0))  # Red
        pattern = QRegExp("\".*\"")
        pattern.setMinimal(True)
        self.highlighting_rules.append((pattern, string_format))
        
        # Format for single-line comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(128, 128, 128))  # Gray
        pattern = QRegExp("//[^\n]*")
        self.highlighting_rules.append((pattern, comment_format))
        
        # Format for multi-line comments
        self.multi_line_comment_format = QTextCharFormat()
        self.multi_line_comment_format.setForeground(QColor(128, 128, 128))  # Gray
        
        self.comment_start_expression = QRegExp("/\\*")
        self.comment_end_expression = QRegExp("\\*/")
        
    def highlightBlock(self, text):
        # Apply regular highlighting rules
        for pattern, format in self.highlighting_rules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)