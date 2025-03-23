import re
from enum import Enum, auto

class TokenType(Enum):
    KEYWORD = auto()
    IDENTIFIER = auto()
    LITERAL = auto()
    BOOL_LITERAL = auto()       # Added for 'true' and 'false'
    CHAR_LITERAL = auto()       # Added for 'A'
    STRING_LITERAL = auto()
    NUMBER = auto()             # Added for 123
    OPERATOR = auto()
    SEPARATOR = auto()
    COMMENT = auto()
    WHITESPACE = auto()
    PREPROCESSOR = auto()
    UNKNOWN = auto()

class Token:
    def __init__(self, token_type, value, line, column):
        self.type = token_type
        self.value = value
        self.line = line
        self.column = column
    
    def __repr__(self):
        return f"Token({self.type}, '{self.value}', line={self.line}, col={self.column})"

class Lexer:
    def __init__(self, code):
        self.code = code
        self.tokens = []
        self.current_pos = 0
        self.line = 1
        self.column = 1
        
        # Keywords
        self.keywords = {
            # Basic Data Types
            "char", "int", "float", "double", "bool", "long", "short", "string",

            # Looping Keywords
            "for", "while", "do",

            # Arithmetic & Operators
            "return",

            # Conditionals (Useful for Loops)
            "if", "else", "break", "switch", "case", "default"
        }
        
        # Regular expressions for tokens
        self.token_specs = [
            # Whitespace
            (r'[ \t\r\f]+', TokenType.WHITESPACE),
            # Newline
            (r'\n', TokenType.WHITESPACE),
            # C++ style comments
            (r'//.*', TokenType.COMMENT),
            # C style comments
            (r'/\*.*?\*/', TokenType.COMMENT, re.DOTALL),
            # Preprocessor directives
            (r'#\w+.*?(?:\n|$)', TokenType.PREPROCESSOR),
            # Character literals
            (r"'(?:\\.|[^'\\])'", TokenType.CHAR_LITERAL),
            # String literals
            (r'"(?:\\.|[^"\\])*"', TokenType.STRING_LITERAL),
            # String literals
            (r'"(?:\\.|[^"\\])*"', TokenType.LITERAL),
            # Floating point literals
            (r'\d+\.\d*(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?|\d+[eE][+-]?\d+', TokenType.LITERAL),
            # Integer literals
            (r'0[xX][0-9a-fA-F]+|\d+', TokenType.LITERAL),
            # Boolean literals 
            (r'\btrue\b|\bfalse\b', TokenType.BOOL_LITERAL),
            # Operators
            (r'--|\+\+|==|!=|<=|>=|&&|\|\||<<|>>|->|::|[+\-*/%=&|^~!<>?:.]', TokenType.OPERATOR),
            # Separators
            (r'[(){}\[\];,]', TokenType.SEPARATOR),
            # Identifiers
            (r'[a-zA-Z_]\w*', TokenType.IDENTIFIER),
            # Anything else
            (r'.', TokenType.UNKNOWN)
        ]
        
        # Compile patterns
        self.patterns = []
        for pattern in self.token_specs:
            if len(pattern) == 2:
                regex, token_type = pattern
                flags = 0
            else:
                regex, token_type, flags = pattern
            self.patterns.append((re.compile(regex, flags), token_type))
    
    def tokenize(self):
        self.tokens = []
        
        # Split code into lines for better error reporting
        lines = self.code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            col = 1
            pos = 0
            
            while pos < len(line):
                match = None
                
                # Try to match each pattern
                for pattern, token_type in self.patterns:
                    regex_match = pattern.match(line, pos)
                    if regex_match:
                        match = regex_match
                        value = match.group(0)
                        
                        # Skip whitespace tokens
                        if token_type != TokenType.WHITESPACE:
                            # Check if identifier is a keyword
                            if token_type == TokenType.IDENTIFIER and value in self.keywords:
                                token_type = TokenType.KEYWORD
                            
                            self.tokens.append(Token(token_type, value, line_num, col))
                        
                        col += len(value)
                        pos = match.end()
                        break
                
                if not match:
                    # If no pattern matches, raise an error
                    raise ValueError(f"Unknown token at line {line_num}, column {col}: '{line[pos]}'")
        
        return self.tokens
    
"""code = 'string name = "vian";'
lexer = Lexer(code)
tokens = lexer.tokenize()

for token in tokens:
    print(token)""" 