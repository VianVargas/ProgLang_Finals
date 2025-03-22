class ErrorHandler:
    def __init__(self):
        self.errors = []
    
    def add_error(self, error_type, message, line, column):
        """Add an error with type, message, and location."""
        self.errors.append({
            'type': error_type,
            'message': message,
            'line': line,
            'column': column
        })
    
    def format_errors(self):
        """Format all errors into a readable string."""
        formatted = []
        for error in self.errors:
            formatted.append(f"{error['type']} Error at line {error['line']}, column {error['column']}: {error['message']}")
        return '\n'.join(formatted)
    
    def get_errors(self):
        """Get the list of errors."""
        return self.errors
    
    def has_errors(self):
        """Check if there are any errors."""
        return len(self.errors) > 0
    
    def clear(self):
        """Clear all errors."""
        self.errors = []