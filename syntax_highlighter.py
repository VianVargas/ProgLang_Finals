from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, QColor

class CppSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.highlighting_rules = []
        
        # Format for keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(0, 0, 255))  # Blue
        keyword_format.setFontWeight(QFont.Bold)
        
        # C++ keywords
        keywords = [
            "auto", "break", "case", "catch", "class", "const", "continue", "default",
            "delete", "do", "double", "else", "enum", "explicit", "export", "extern",
            "false", "float", "for", "friend", "goto", "if", "inline", "int", "long",
            "mutable", "namespace", "new", "operator", "private", "protected", "public",
            "register", "return", "short", "signed", "sizeof", "static", "struct",
            "switch", "template", "this", "throw", "true", "try", "typedef", "typeid",
            "typename", "union", "unsigned", "using", "virtual", "void", "volatile", "while"
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
        
        # Handle multi-line comments
        self.setCurrentBlockState(0)
        
        start_index = 0
        if self.previousBlockState() != 1:
            start_index = self.comment_start_expression.indexIn(text)
        
        while start_index >= 0:
            end_index = self.comment_end_expression.indexIn(text, start_index)
            
            if end_index == -1:
                self.setCurrentBlockState(1)
                comment_length = len(text) - start_index
            else:
                comment_length = end_index - start_index + self.comment_end_expression.matchedLength()
            
            self.setFormat(start_index, comment_length, self.multi_line_comment_format)
            start_index = self.comment_start_expression.indexIn(text, start_index + comment_length)