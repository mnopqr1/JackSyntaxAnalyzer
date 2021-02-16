JACK_KEYWORDS = ["class", "method", "function", "constructor", 
                 "int", "boolean", "char", "void", "var", "static",
                 "field", "let", "do", "if", "else", "while",
                 "return", "true", "false", "null", "this"]

class Token:
    token_type = None
    content = None

    def __init__(self, token_type, content):
        self.token_type = token_type
        self.content = content
    
    @classmethod
    def from_content(cls, content):
        if content in JACK_KEYWORDS:
            token_type = "KEYWORD"
            content = content.upper()
        elif content[0].isdigit():
            token_type = "INT_CONST"
            content = int(content)
        else:
            token_type = "IDENTIFIER"
            content = content
        return cls(token_type, content)
    
    def to_string(self):
        return "<" + self.token_type + ">" + self.content + "</" + self.token_type + ">"
