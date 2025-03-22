class Symbol:
    def __init__(self, name, type_name, scope_level):
        self.name = name
        self.type = type_name
        self.scope_level = scope_level
        self.initialized = False
        self.used = False
    
    def __repr__(self):
        return f"Symbol({self.name}, {self.type}, level={self.scope_level}, init={self.initialized}, used={self.used})"

class Scope:
    def __init__(self, parent=None, level=0):
        self.symbols = {}
        self.parent = parent
        self.level = level
    
    def define(self, name, type_name):
        symbol = Symbol(name, type_name, self.level)
        self.symbols[name] = symbol
        return symbol
    
    def resolve(self, name):
        if name in self.symbols:
            return self.symbols[name]
        elif self.parent:
            return self.parent.resolve(name)
        return None

class SemanticAnalyzer:
    def __init__(self, ast):
        self.ast = ast
        self.current_scope = Scope()
        self.errors = []
    
    def analyze(self):
        self._analyze_node(self.ast)
        return {"valid": len(self.errors) == 0, "errors": self.errors}
    
    def _analyze_node(self, node):
        if node.type == "Program":
            for child in node.children:
                self._analyze_node(child)
        
        elif node.type == "Block":
            # Create new scope for block
            parent_scope = self.current_scope
            self.current_scope = Scope(parent_scope, parent_scope.level + 1)
            
            for child in node.children:
                self._analyze_node(child)
            
            # Restore parent scope
            self.current_scope = parent_scope
        
        elif node.type == "VariableDeclaration":
            var_type = node.value
            var_name = node.children[0].value
            
            # Check if variable is already defined in current scope
            if var_name in self.current_scope.symbols:
                self.errors.append(f"Variable '{var_name}' is already defined in this scope")
            else:
                symbol = self.current_scope.define(var_name, var_type)
                
                # Check for initialization
                if len(node.children) > 1:
                    init_expr = node.children[1]
                    self._analyze_node(init_expr)
                    symbol.initialized = True
                    
                    # Type checking for initialization
                    if init_expr.type == "Literal":
                        # Simple type check for literals
                        literal_value = init_expr.value
                        if var_type == "int":
                            if literal_value.startswith('"') or literal_value.startswith("'"):
                                self.errors.append(f"Cannot initialize int variable '{var_name}' with string literal")
                        elif var_type == "float" or var_type == "double":
                            if literal_value.startswith('"') or literal_value.startswith("'"):
                                self.errors.append(f"Cannot initialize {var_type} variable '{var_name}' with string literal")
                        elif var_type == "char":
                            if not (literal_value.startswith("'") and len(literal_value) == 3):
                                self.errors.append(f"Invalid character literal for variable '{var_name}'")
        
        elif node.type == "Identifier":
            var_name = node.value
            symbol = self.current_scope.resolve(var_name)
            
            if not symbol:
                self.errors.append(f"Undefined variable '{var_name}'")
            else:
                symbol.used = True
                
                # Check if variable is used before initialization
                if not symbol.initialized:
                    self.errors.append(f"Variable '{var_name}' is used before initialization")
        
        elif node.type == "Assignment":
            # Check left side is an identifier
            if node.children[0].type != "Identifier":
                self.errors.append("Left side of assignment must be a variable")
                return
            
            var_name = node.children[0].value
            symbol = self.current_scope.resolve(var_name)
            
            if not symbol:
                self.errors.append(f"Undefined variable '{var_name}'")
            else:
                # Mark as initialized
                symbol.initialized = True
                
                # Check right side
                self._analyze_node(node.children[1])
                
                # Type checking for assignment
                if node.children[1].type == "Literal":
                    literal_value = node.children[1].value
                    if symbol.type == "int":
                        if literal_value.startswith('"') or literal_value.startswith("'"):
                            self.errors.append(f"Cannot assign string literal to int variable '{var_name}'")
                    elif symbol.type == "float" or symbol.type == "double":
                        if literal_value.startswith('"') or literal_value.startswith("'"):
                            self.errors.append(f"Cannot assign string literal to {symbol.type} variable '{var_name}'")
                    elif symbol.type == "char":
                        if not (literal_value.startswith("'") and len(literal_value) == 3):
                            self.errors.append(f"Invalid character literal for variable '{var_name}'")
        
        elif node.type == "BinaryOp":
            # Analyze operands
            self._analyze_node(node.children[0])
            self._analyze_node(node.children[1])
            
            # Type checking for binary operations
            if node.value in ["+", "-", "*", "/", "%"] and node.children[0].type == "Identifier" and node.children[1].type == "Identifier":
                left_symbol = self.current_scope.resolve(node.children[0].value)
                right_symbol = self.current_scope.resolve(node.children[1].value)
                
                if left_symbol and right_symbol:
                    if left_symbol.type == "char" or right_symbol.type == "char":
                        if node.value == "%":
                            self.errors.append(f"Cannot use modulo operator '%' with char operands")
        
        elif node.type == "UnaryOp":
            # Analyze operand
            self._analyze_node(node.children[0])
            
            # Type checking for unary operations
            if node.value in ["++", "--"] and node.children[0].type == "Identifier":
                symbol = self.current_scope.resolve(node.children[0].value)
                if symbol and symbol.type not in ["int", "float", "double"]:
                    self.errors.append(f"Cannot use increment/decrement operator with non-numeric type '{symbol.type}'")
        
        elif node.type == "ForLoop":
            # Create new scope for loop
            parent_scope = self.current_scope
            self.current_scope = Scope(parent_scope, parent_scope.level + 1)
            
            # Analyze initialization, condition, and increment
            for child in node.children:
                self._analyze_node(child)
            
            # Restore parent scope
            self.current_scope = parent_scope
        
        elif node.type == "WhileLoop" or node.type == "DoWhileLoop":
            # Analyze condition
            self._analyze_node(node.children[0])
            
            # Create new scope for loop
            parent_scope = self.current_scope
            self.current_scope = Scope(parent_scope, parent_scope.level + 1)
            
            # Analyze body
            for i in range(1, len(node.children)):
                self._analyze_node(node.children[i])
            
            # Restore parent scope
            self.current_scope = parent_scope
        
        elif node.type == "IfStatement":
            # Analyze condition
            self._analyze_node(node.children[0])
            
            # Create new scope for then branch
            parent_scope = self.current_scope
            self.current_scope = Scope(parent_scope, parent_scope.level + 1)
            
            # Analyze then branch
            if len(node.children) > 1:
                self._analyze_node(node.children[1])
            
            # Restore parent scope
            self.current_scope = parent_scope
            
            # Create new scope for else branch
            if len(node.children) > 2:
                self.current_scope = Scope(parent_scope, parent_scope.level + 1)
                self._analyze_node(node.children[2])
                self.current_scope = parent_scope
        
        elif node.type == "ReturnStatement":
            # Analyze return value
            if node.children:
                self._analyze_node(node.children[0])
        
        elif node.type == "Literal":
            # Nothing to do for literals
            pass
        
        elif node.type == "Error":
            # Already reported in parser
            pass
        
        else:
            # Analyze child nodes
            for child in node.children:
                self._analyze_node(child)