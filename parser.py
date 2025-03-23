from lexer import TokenType 

class ASTNode:
    def __init__(self, node_type, value=None, children=None):
        self.type = node_type
        self.value = value
        self.children = children if children is not None else []
    
    def add_child(self, child):
        self.children.append(child)
    
    def __repr__(self):
        return f"ASTNode({self.type}, {self.value}, {len(self.children)} children)"

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_index = 0
        self.errors = []
        self.ast = ASTNode("Program")
    
    def parse(self):
        try:
            self._parse_program()
            return {"valid": len(self.errors) == 0, "errors": self.errors, "ast": self.ast}
        except Exception as e:
            self.errors.append(str(e))
            return {"valid": False, "errors": self.errors, "ast": self.ast}
    
    def _parse_program(self):
        while self.current_index < len(self.tokens):
            try:
                self._skip_comments()  # Skip any comments before parsing the statement
                if self.current_index < len(self.tokens):
                    self._parse_statement()
            except Exception as e:
                self.errors.append(str(e))
                self._synchronize()
    
    def _skip_comments(self):
        """Skip any comment tokens"""
        while self.current_index < len(self.tokens) and self.tokens[self.current_index].type == TokenType.COMMENT:
            self.current_index += 1
    
    def _synchronize(self):
        """Skip tokens until a semicolon or block end is found"""
        while self.current_index < len(self.tokens):
            token = self.tokens[self.current_index]
            self.current_index += 1
            if token.value == ";" or token.value == "}":
                return
    
    def _parse_statement(self):
        if self.current_index >= len(self.tokens):
            return
        
        token = self.tokens[self.current_index]
        
        if token.type == TokenType.KEYWORD:
            if token.value == "int" or token.value == "float" or token.value == "long" or token.value == "short" or \
            token.value == "char" or token.value == "double" or token.value == "bool" or token.value == "string":
                self._parse_variable_declaration()
            elif token.value == "for":
                self._parse_for_loop()
            elif token.value == "while":
                self._parse_while_loop()
            elif token.value == "do":
                self._parse_do_while_loop()
            elif token.value == "if":
                self._parse_if_statement()
            elif token.value == "switch":  
                self._parse_switch_statement() 
            elif token.value == "break": 
                self._parse_break_statement() 
            elif token.value == "return":
                self._parse_return_statement()
            else:
                self.current_index += 1
                self.errors.append(f"Unsupported keyword: {token.value} at line {token.line}, column {token.column}")
        elif token.type == TokenType.IDENTIFIER:
            self._parse_expression_statement()
        elif token.type == TokenType.SEPARATOR and token.value == "{":
            self._parse_block()
        elif token.type == TokenType.SEPARATOR and token.value == ";":
            self.current_index += 1  # Skip empty statements
        else:
            self.current_index += 1
            self.errors.append(f"Unexpected token: {token.value} at line {token.line}, column {token.column}")
        
    def _parse_variable_declaration(self):
        type_token = self.tokens[self.current_index]
        self.current_index += 1
        
        # We'll continue parsing variable declarations until we hit a semicolon
        while True:
            self._skip_comments()  # Skip comments between type and identifier
            
            # Check for identifier
            if self.current_index >= len(self.tokens) or self.tokens[self.current_index].type != TokenType.IDENTIFIER:
                self.errors.append(f"Expected identifier after {type_token.value} at line {type_token.line}, column {type_token.column}")
                return
            
            var_node = ASTNode("VariableDeclaration", type_token.value)
            
            # Get variable name
            var_name = self.tokens[self.current_index]
            var_node.add_child(ASTNode("Identifier", var_name.value))
            self.current_index += 1
            
            self._skip_comments()  # Skip comments between identifier and potential initialization
            
            # Check for initialization
            if self.current_index < len(self.tokens) and self.tokens[self.current_index].value == "=":
                self.current_index += 1  # Skip '='
                
                self._skip_comments()  # Skip comments before expression
                
                # Special handling for bool and char types
                if self.current_index < len(self.tokens):
                    value_token = self.tokens[self.current_index]
                    
                    # Type-specific validation
                    if type_token.value == "bool":
                        if value_token.type != TokenType.BOOL_LITERAL:
                            self.errors.append(f"Unexpected token in boolean expression: {value_token.value} at line {value_token.line}, column {value_token.column}")
                        else:
                            # Create literal node for boolean value
                            expr_node = ASTNode("Literal", value_token.value)
                            var_node.add_child(expr_node)
                            self.current_index += 1  # Consume the boolean value
                    elif type_token.value == "char":
                        if value_token.type != TokenType.CHAR_LITERAL:
                            self.errors.append(f"Unexpected token in char expression: {value_token.value} at line {value_token.line}, column {value_token.column}")
                        else:
                            # Create literal node for char value
                            expr_node = ASTNode("Literal", value_token.value)
                            var_node.add_child(expr_node)
                            self.current_index += 1  # Consume the char value
                    elif type_token.value == "string":
                        if value_token.type != TokenType.STRING_LITERAL:
                            self.errors.append(f"Unexpected token in string expression: {value_token.value} at line {value_token.line}, column {value_token.column}")
                        else:
                            # Create literal node for string value
                            expr_node = ASTNode("Literal", value_token.value)
                            var_node.add_child(expr_node)
                            self.current_index += 1  # Consume the string value
                    else:
                        # For other types, parse a full expression
                        expr_node = self._parse_expression()
                        var_node.add_child(expr_node)
            
            # Add the variable declaration to the AST
            self.ast.add_child(var_node)
            
            self._skip_comments()  # Skip comments before comma or semicolon
            
            # Check for comma or semicolon
            if self.current_index >= len(self.tokens):
                self.errors.append(f"Expected ';' at end of statement at line {var_name.line}, column {var_name.column}")
                return
                
            # If we have a comma, continue parsing more variables of the same type
            if self.tokens[self.current_index].value == ",":
                self.current_index += 1  # Skip ','
                self._skip_comments()  # Skip comments after comma
                continue
                
            # If we have a semicolon, we're done
            if self.tokens[self.current_index].value == ";":
                self.current_index += 1  # Skip ';'
                return
                
            # Otherwise, it's an error
            self.errors.append(f"Expected ',' or ';' after variable declaration at line {var_name.line}, column {var_name.column}")
            return
            
    def _parse_expression(self):
        if self.current_index >= len(self.tokens):
            self.errors.append("Unexpected end of input while parsing expression")
            return ASTNode("Error")
        
        return self._parse_assignment()
    
    def _parse_assignment(self):
        left = self._parse_logical_or()
        
        self._skip_comments()  # Skip comments before assignment operator
        
        if self.current_index < len(self.tokens) and self.tokens[self.current_index].value == "=":
            op_token = self.tokens[self.current_index]
            self.current_index += 1
            
            self._skip_comments()  # Skip comments after assignment operator
            
            right = self._parse_assignment()
            return ASTNode("Assignment", op_token.value, [left, right])
        
        return left
    
    def _parse_logical_or(self):
        left = self._parse_logical_and()
        
        while self.current_index < len(self.tokens):
            self._skip_comments()  # Skip comments before operator
            
            if self.current_index < len(self.tokens) and self.tokens[self.current_index].value == "||":
                op_token = self.tokens[self.current_index]
                self.current_index += 1
                
                self._skip_comments()  # Skip comments after operator
                
                right = self._parse_logical_and()
                left = ASTNode("BinaryOp", op_token.value, [left, right])
            else:
                break
        
        return left
        
    def _parse_logical_and(self):
        left = self._parse_equality()
        
        while self.current_index < len(self.tokens):
            self._skip_comments()  # Skip comments before operator
            
            if self.current_index < len(self.tokens) and self.tokens[self.current_index].value == "&&":
                op_token = self.tokens[self.current_index]
                self.current_index += 1
                
                self._skip_comments()  # Skip comments after operator
                
                right = self._parse_equality()
                left = ASTNode("BinaryOp", op_token.value, [left, right])
            else:
                break
        
        return left
    
    def _parse_equality(self):
        left = self._parse_relational()
        
        while self.current_index < len(self.tokens):
            self._skip_comments()  # Skip comments before operator
            
            if self.current_index < len(self.tokens) and self.tokens[self.current_index].value in ["==", "!="]:
                op_token = self.tokens[self.current_index]
                self.current_index += 1
                
                self._skip_comments()  # Skip comments after operator
                
                right = self._parse_relational()
                left = ASTNode("BinaryOp", op_token.value, [left, right])
            else:
                break
        
        return left
    
    def _parse_relational(self):
        left = self._parse_additive()
        
        while self.current_index < len(self.tokens):
            self._skip_comments()  # Skip comments before operator
            
            if self.current_index < len(self.tokens) and self.tokens[self.current_index].value in ["<", ">", "<=", ">="]:
                op_token = self.tokens[self.current_index]
                self.current_index += 1
                
                self._skip_comments()  # Skip comments after operator
                
                right = self._parse_additive()
                left = ASTNode("BinaryOp", op_token.value, [left, right])
            else:
                break
        
        return left
    
    def _parse_additive(self):
        left = self._parse_multiplicative()
        
        while self.current_index < len(self.tokens):
            self._skip_comments()  # Skip comments before operator
            
            if self.current_index < len(self.tokens) and self.tokens[self.current_index].value in ["+", "-"]:
                op_token = self.tokens[self.current_index]
                self.current_index += 1
                
                self._skip_comments()  # Skip comments after operator
                
                right = self._parse_multiplicative()
                left = ASTNode("BinaryOp", op_token.value, [left, right])
            else:
                break
        
        return left
    
    def _parse_multiplicative(self):
        left = self._parse_unary()
        
        while self.current_index < len(self.tokens):
            self._skip_comments()  # Skip comments before operator
            
            if self.current_index < len(self.tokens) and self.tokens[self.current_index].value in ["*", "/", "%"]:
                op_token = self.tokens[self.current_index]
                self.current_index += 1
                
                self._skip_comments()  # Skip comments after operator
                
                right = self._parse_unary()
                left = ASTNode("BinaryOp", op_token.value, [left, right])
            else:
                break
        
        return left
    
    def _parse_unary(self):
        self._skip_comments()  # Skip comments before unary operator
        
        if self.current_index < len(self.tokens) and self.tokens[self.current_index].value in ["+", "-", "!", "++", "--"]:
            op_token = self.tokens[self.current_index]
            self.current_index += 1
            
            self._skip_comments()  # Skip comments after unary operator
            
            right = self._parse_unary()
            return ASTNode("UnaryOp", op_token.value, [right])
        
        return self._parse_primary()
    
    def _parse_primary(self):
        self._skip_comments()  # Skip comments before primary expression
        
        if self.current_index >= len(self.tokens):
            self.errors.append("Unexpected end of input while parsing primary expression")
            return ASTNode("Error")
        
        token = self.tokens[self.current_index]
        self.current_index += 1
        
        if token.type == TokenType.LITERAL:
            return ASTNode("Literal", token.value)
        elif token.type == TokenType.IDENTIFIER:
            # Get the identifier node
            id_node = ASTNode("Identifier", token.value)
            
            self._skip_comments()  # Skip comments before postfix operators
            
            # Check for postfix operators
            if (self.current_index < len(self.tokens) and 
                self.tokens[self.current_index].value in ["++", "--"]):
                op_token = self.tokens[self.current_index]
                self.current_index += 1
                return ASTNode("PostfixOp", op_token.value, [id_node])
            
            return id_node
        elif token.value == "(":
            expr = self._parse_expression()
            
            self._skip_comments()  # Skip comments before closing parenthesis
            
            if self.current_index >= len(self.tokens) or self.tokens[self.current_index].value != ")":
                self.errors.append(f"Expected ')' after expression at line {token.line}, column {token.column}")
                return ASTNode("Error")
            
            self.current_index += 1  # Skip ')'
            return expr
        else:
            self.errors.append(f"Unexpected token in expression: {token.value} at line {token.line}, column {token.column}")
            return ASTNode("Error")
            
    def _parse_expression_statement(self):
        expr = self._parse_expression()
        
        self._skip_comments()  # Skip comments before semicolon
        
        if self.current_index >= len(self.tokens) or self.tokens[self.current_index].value != ";":
            self.errors.append(f"Expected ';' after expression at line {self.tokens[self.current_index-1].line}, column {self.tokens[self.current_index-1].column}")
            return
        
        self.current_index += 1  # Skip ';'
        self.ast.add_child(expr)
    
    def _parse_block(self):
        if self.current_index >= len(self.tokens) or self.tokens[self.current_index].value != "{":
            self.errors.append("Expected '{' to start block")
            return
        
        self.current_index += 1  # Skip '{'
        
        block_node = ASTNode("Block")
        
        while self.current_index < len(self.tokens):
            self._skip_comments()  # Skip comments inside block
            
            if self.current_index < len(self.tokens) and self.tokens[self.current_index].value == "}":
                break
            
            try:
                self._parse_statement()
            except Exception as e:
                self.errors.append(str(e))
                self._synchronize()
        
        if self.current_index >= len(self.tokens) or self.tokens[self.current_index].value != "}":
            self.errors.append("Expected '}' to end block")
            return
        
        self.current_index += 1  # Skip '}'
        self.ast.add_child(block_node)
    
    # Loop parsing functions   
    def _parse_for_loop(self):
        if self.current_index >= len(self.tokens) or self.tokens[self.current_index].value != "for":
            self.errors.append("Expected 'for' keyword")
            return None
        self.current_index += 1  # Skip 'for'
        
        self._skip_comments()  # Skip comments after 'for'
        
        if self.current_index >= len(self.tokens) or self.tokens[self.current_index].value != "(":
            self.errors.append("Expected '(' after 'for'")
            return None
        self.current_index += 1  # Skip '('
        
        self._skip_comments()  # Skip comments after '('
        
        for_node = ASTNode("ForLoop")
        
        # Parse initialization
        if (self.current_index < len(self.tokens) and 
            self.tokens[self.current_index].type == TokenType.KEYWORD and 
            self.tokens[self.current_index].value in ["int", "float", "char", "double", "bool"]):
            # Get the type
            var_type = self.tokens[self.current_index].value
            self.current_index += 1  # Skip type
            
            self._skip_comments()  # Skip comments after type
            
            # Get the variable name
            if self.current_index >= len(self.tokens) or self.tokens[self.current_index].type != TokenType.IDENTIFIER:
                self.errors.append("Expected identifier after type")
                return None
            
            var_name = self.tokens[self.current_index].value
            self.current_index += 1  # Skip identifier
            
            self._skip_comments()  # Skip comments after identifier
            
            # Create a variable declaration node
            var_decl = ASTNode("VariableDeclaration")
            var_decl.value = var_type
            
            # Add the identifier as a child
            id_node = ASTNode("Identifier")
            id_node.value = var_name
            var_decl.add_child(id_node)
            
            # Handle initialization if present
            if self.current_index < len(self.tokens) and self.tokens[self.current_index].value == "=":
                self.current_index += 1  # Skip '='
                
                self._skip_comments()  # Skip comments after '='
                
                # Parse the initializer expression
                init_expr = self._parse_expression()
                if init_expr is not None:
                    var_decl.add_child(init_expr)
            
            # Add the variable declaration to the for loop node
            for_node.add_child(var_decl)
            
            self._skip_comments()  # Skip comments before semicolon
            
            # Expect semicolon
            if self.current_index >= len(self.tokens) or self.tokens[self.current_index].value != ";":
                self.errors.append("Expected ';' after variable declaration")
                return None
            self.current_index += 1  # Skip ';'
        else:
            # Expression initialization
            init_expr = self._parse_expression()
            if init_expr is None:
                init_expr = ASTNode("Empty")
            for_node.add_child(init_expr)
            
            self._skip_comments()  # Skip comments before semicolon
            
            if self.current_index >= len(self.tokens) or self.tokens[self.current_index].value != ";":
                self.errors.append("Expected ';' after for loop initialization")
                return None
            self.current_index += 1  # Skip ';'
        
        self._skip_comments()  # Skip comments after initialization semicolon
        
        # Parse condition
        if self.current_index < len(self.tokens) and self.tokens[self.current_index].value != ";":
            condition = self._parse_expression()
            if condition is None:
                condition = ASTNode("Empty")
            for_node.add_child(condition)
        else:
            for_node.add_child(ASTNode("Empty"))
        
        self._skip_comments()  # Skip comments before condition semicolon
        
        if self.current_index >= len(self.tokens) or self.tokens[self.current_index].value != ";":
            self.errors.append("Expected ';' after for loop condition")
            return None
        self.current_index += 1  # Skip ';'
        
        self._skip_comments()  # Skip comments after condition semicolon
        
        # Parse increment
        if self.current_index < len(self.tokens) and self.tokens[self.current_index].value != ")":
            increment = self._parse_expression()
            if increment is None:
                increment = ASTNode("Empty")
            for_node.add_child(increment)
        else:
            for_node.add_child(ASTNode("Empty"))
        
        self._skip_comments()  # Skip comments before closing parenthesis
        
        if self.current_index >= len(self.tokens) or self.tokens[self.current_index].value != ")":
            self.errors.append("Expected ')' after for loop increment")
            return None
        self.current_index += 1  # Skip ')'
        
        self._skip_comments()  # Skip comments after closing parenthesis
        
        # Parse body
        body_node = None
        
        # First check if we have a block
        if self.current_index < len(self.tokens) and self.tokens[self.current_index].value == "{":
            body_node = self._parse_block()
            if body_node is None:
                body_node = ASTNode("Block")
        else:
            # Now parse the statement
            if self.current_index < len(self.tokens):
                body_node = self._parse_statement()
                if body_node is None:
                    body_node = ASTNode("Statement")
            else:
                body_node = ASTNode("Block")  # Empty block if nothing to parse
        
        for_node.add_child(body_node)
    
        return for_node
    
    def _parse_do_while_loop(self):
        if self.current_index >= len(self.tokens) or self.tokens[self.current_index].value != "do":
            self.errors.append("Expected 'do' keyword")
            return
        
        self.current_index += 1  # Skip 'do'
        self._skip_comments()  # Skip comments after 'do'
        
        do_while_node = ASTNode("DoWhileLoop")
        
        # Parse body
        if self.current_index < len(self.tokens) and self.tokens[self.current_index].value == "{":
            self._parse_block()
        else:
            self._parse_statement()
        
        self._skip_comments()  # Skip comments after body
        
        if self.current_index >= len(self.tokens) or self.tokens[self.current_index].value != "while":
            self.errors.append("Expected 'while' after do-while loop body")
            return
        
        self.current_index += 1  # Skip 'while'
        self._skip_comments()  # Skip comments after 'while'
        
        if self.current_index >= len(self.tokens) or self.tokens[self.current_index].value != "(":
            self.errors.append("Expected '(' after 'while' in do-while loop")
            return
        
        self.current_index += 1  # Skip '('
        self._skip_comments()  # Skip comments after '('
        
        # Parse condition
        condition = self._parse_expression()
        do_while_node.add_child(condition)
        
        self._skip_comments()  # Skip comments after condition
        
        if self.current_index >= len(self.tokens) or self.tokens[self.current_index].value != ")":
            self.errors.append("Expected ')' after do-while loop condition")
            return
        
        self.current_index += 1  # Skip ')'
        self._skip_comments()  # Skip comments after ')'
        
        if self.current_index >= len(self.tokens) or self.tokens[self.current_index].value != ";":
            self.errors.append("Expected ';' after do-while loop")
            return
        
        self.current_index += 1  # Skip ';'
        self.ast.add_child(do_while_node)
        
    def _parse_while_loop(self):
        if self.current_index >= len(self.tokens) or self.tokens[self.current_index].value != "while":
            self.errors.append("Expected 'while' keyword")
            return
        
        self.current_index += 1  # Skip 'while'
        self._skip_comments()  # Skip comments after 'while'
        
        if self.current_index >= len(self.tokens) or self.tokens[self.current_index].value != "(":
            self.errors.append("Expected '(' after 'while'")
            return
        
        self.current_index += 1  # Skip '('
        self._skip_comments()  # Skip comments after '('
        
        while_node = ASTNode("WhileLoop")
        
        # Parse condition
        condition = self._parse_expression()
        while_node.add_child(condition)
        
        self._skip_comments()  # Skip comments after condition
        
        if self.current_index >= len(self.tokens) or self.tokens[self.current_index].value != ")":
            self.errors.append("Expected ')' after while condition")
            return
        
        self.current_index += 1  # Skip ')'
        self._skip_comments()  # Skip comments after ')'
        
        # Parse body
        if self.current_index < len(self.tokens) and self.tokens[self.current_index].value == "{":
            self._parse_block()
        else:
            self._parse_statement()
        
        self.ast.add_child(while_node)
    
    def _parse_if_statement(self):
        if self.current_index >= len(self.tokens) or self.tokens[self.current_index].value != "if":
            self.errors.append("Expected 'if' keyword")
            return
        
        self.current_index += 1  # Skip 'if'
        self._skip_comments()  # Skip comments after 'if'
        
        if self.current_index >= len(self.tokens) or self.tokens[self.current_index].value != "(":
            self.errors.append("Expected '(' after 'if'")
            return
        
        self.current_index += 1  # Skip '('
        self._skip_comments()  # Skip comments after '('
        
        if_node = ASTNode("IfStatement")
        
        # Parse condition
        condition = self._parse_expression()
        if_node.add_child(condition)
        
        self._skip_comments()  # Skip comments after condition
        
        if self.current_index >= len(self.tokens) or self.tokens[self.current_index].value != ")":
            self.errors.append("Expected ')' after if condition")
            return
        
        self.current_index += 1  # Skip ')'
        self._skip_comments()  # Skip comments after ')'
        
        # Parse then branch
        if self.current_index < len(self.tokens) and self.tokens[self.current_index].value == "{":
            self._parse_block()
        else:
            self._parse_statement()
        
        self._skip_comments()  # Skip comments after then branch
        
        # Parse else branch if present
        if self.current_index < len(self.tokens) and self.tokens[self.current_index].value == "else":
            self.current_index += 1  # Skip 'else'
            self._skip_comments()  # Skip comments after 'else'
            
            if self.current_index < len(self.tokens) and self.tokens[self.current_index].value == "{":
                self._parse_block()
            else:
                self._parse_statement()
        
        self.ast.add_child(if_node)
        
    def _parse_switch_statement(self):
        if self.current_index >= len(self.tokens) or self.tokens[self.current_index].value != "switch":
            self.errors.append("Expected 'switch' keyword")
            return None
        
        self.current_index += 1  # Skip 'switch'
        self._skip_comments()  # Skip comments after 'switch'
        
        if self.current_index >= len(self.tokens) or self.tokens[self.current_index].value != "(":
            self.errors.append("Expected '(' after 'switch'")
            return None
        
        self.current_index += 1  # Skip '('
        self._skip_comments()  # Skip comments after '('
        
        switch_node = ASTNode("SwitchStatement")
        
        # Parse the expression to switch on
        expression = self._parse_expression()
        if expression:
            switch_node.add_child(expression)
        
        self._skip_comments()  # Skip comments after expression
        
        if self.current_index >= len(self.tokens) or self.tokens[self.current_index].value != ")":
            self.errors.append("Expected ')' after switch expression")
            return switch_node
        
        self.current_index += 1  # Skip ')'
        self._skip_comments()  # Skip comments after ')'
        
        # Parse the switch body with cases
        if self.current_index >= len(self.tokens) or self.tokens[self.current_index].value != "{":
            self.errors.append("Expected '{' after switch condition")
            return switch_node
        
        self.current_index += 1  # Skip '{'
        self._skip_comments()  # Skip comments after '{'
        
        # Parse case statements
        while self.current_index < len(self.tokens) and self.tokens[self.current_index].value != "}":
            self._skip_comments()  # Skip comments before case
            
            if self.current_index >= len(self.tokens):
                self.errors.append("Unexpected end of file in switch statement")
                return switch_node
            
            if self.tokens[self.current_index].value == "case":
                case_node = self._parse_case_statement()
                if case_node:
                    switch_node.add_child(case_node)
            elif self.tokens[self.current_index].value == "default":
                default_node = self._parse_default_statement()
                if default_node:
                    switch_node.add_child(default_node)
            else:
                self.errors.append(f"Expected 'case' or 'default' in switch statement, got {self.tokens[self.current_index].value}")
                self._synchronize()
        
        if self.current_index >= len(self.tokens) or self.tokens[self.current_index].value != "}":
            self.errors.append("Expected '}' to close switch statement")
            return switch_node
        
        self.current_index += 1  # Skip '}'
        return switch_node
        
    def _parse_case_statement(self):
        if self.current_index >= len(self.tokens) or self.tokens[self.current_index].value != "case":
            self.errors.append("Expected 'case' keyword")
            return None
        
        self.current_index += 1  # Skip 'case'
        self._skip_comments()  # Skip comments after 'case'
        
        case_node = ASTNode("CaseStatement")
        
        # Parse the case value
        value = self._parse_expression()
        if value:
            case_node.add_child(value)
        
        self._skip_comments()  # Skip comments after value
        
        if self.current_index >= len(self.tokens) or self.tokens[self.current_index].value != ":":
            self.errors.append("Expected ':' after case value")
            return case_node
        
        self.current_index += 1  # Skip ':'
        self._skip_comments()  # Skip comments after ':'
        
        # Parse case body statements
        while (self.current_index < len(self.tokens) and 
               self.tokens[self.current_index].value not in ["case", "default", "}"]):
            
            statement = self._parse_statement()
            if statement:
                case_node.add_child(statement)
            
            self._skip_comments()  # Skip comments after statement
        
        return case_node
    
    def _parse_default_statement(self):
        if self.current_index >= len(self.tokens) or self.tokens[self.current_index].value != "default":
            self.errors.append("Expected 'default' keyword")
            return None
        
        self.current_index += 1  # Skip 'default'
        self._skip_comments()  # Skip comments after 'default'
        
        default_node = ASTNode("DefaultStatement")
        
        if self.current_index >= len(self.tokens) or self.tokens[self.current_index].value != ":":
            self.errors.append("Expected ':' after default")
            return default_node
        
        self.current_index += 1  # Skip ':'
        self._skip_comments()  # Skip comments after ':'
        
        # Parse default body statements
        while (self.current_index < len(self.tokens) and 
               self.tokens[self.current_index].value not in ["case", "default", "}"]):
            
            statement = self._parse_statement()
            if statement:
                default_node.add_child(statement)
            
            self._skip_comments()  # Skip comments after statement
        
        return default_node
    
    def _parse_break_statement(self):
        if self.current_index >= len(self.tokens) or self.tokens[self.current_index].value != "break":
            self.errors.append("Expected 'break' keyword")
            return None
        
        self.current_index += 1  # Skip 'break'
        self._skip_comments()  # Skip comments after 'break'
        
        break_node = ASTNode("BreakStatement")
        
        if self.current_index >= len(self.tokens) or self.tokens[self.current_index].value != ";":
            self.errors.append("Expected ';' after break statement")
            return break_node
        
        self.current_index += 1  # Skip ';'
        return break_node
    
    def _parse_return_statement(self):
        if self.current_index >= len(self.tokens) or self.tokens[self.current_index].value != "return":
            self.errors.append("Expected 'return' keyword")
            return None
        
        self.current_index += 1  # Skip 'return'
        self._skip_comments()  # Skip comments after 'return'
        
        return_node = ASTNode("ReturnStatement")
        
        # Parse return value if not immediately followed by semicolon
        if self.current_index < len(self.tokens) and self.tokens[self.current_index].value != ";":
            expr = self._parse_expression()
            if expr:
                return_node.add_child(expr)
        
        self._skip_comments()  # Skip comments after return expression
        
        if self.current_index >= len(self.tokens) or self.tokens[self.current_index].value != ";":
            self.errors.append("Expected ';' after return statement")
            return return_node
        
        self.current_index += 1  # Skip ';'
        return return_node