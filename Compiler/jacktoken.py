JACK_KEYWORDS = ["class", "method", "function", "constructor", 
                 "int", "boolean", "char", "void", "var", "static",
                 "field", "let", "do", "if", "else", "while",
                 "return", "true", "false", "null", "this"]

JACK_KEYWORD_CONSTANTS = ["true", "false", "null", "this"]

class Token:
    token_type = None
    content = None

    def __init__(self, token_type, content):
        self.token_type = token_type
        self.content = content
    
    @classmethod
    def from_content(cls, content):
        if content in JACK_KEYWORDS:
            if content in JACK_KEYWORD_CONSTANTS:
                token_type = "keywordConstant"
            else:
                token_type = "keyword"
        elif content[0].isdigit():
            token_type = "integerConstant"
        else:
            token_type = "identifier"
        return cls(token_type, content)
    
    def is_constant(self):
        return self.token_type in ["integerConstant", "stringConstant", "keywordConstant"]
