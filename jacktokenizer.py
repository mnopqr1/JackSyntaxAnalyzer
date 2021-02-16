import os
from jacktoken import Token

JACK_SYMBOLS = "\{\}()\[\].,;+-*/&|<>=-"
JACK_WHITE = " \n\t"

class JackTokenizer:
    current_token = None
    next_token = None

    current_line = 0
    current_comment_start_line = None
    
    file = None
    filename = None


    # auxiliary method seek_comment_end:
    # read from the file until we find '*/'
    # if we reach end of file, then there is a comment opening /* without ending */
    def seek_comment_end(self):
        while True:
            char = self.file.read(1)
            if char == '':  # reached EOF while seeking end
                print(f"Syntax error: end of file reached while parsing multiline comment started on line {current_comment_start_line}")
            if char == '\n': 
                current_line += 1
                continue
            if char == '*':
                if self.file.read(1) == '/':
                    return
                else:
                    continue

    # auxiliary method read_next_real_char:
    # finds next character that is not whitespace or part of a comment
    # TODO: more efficient implementation using regex
    def read_next_real_char(self):
        while True:
            c = self.file.read(1)
            if c == '':
                return None
            if c == ' ' or c == '\t':
                continue
            elif c == '\n':
                self.current_line += 1
                continue
            elif c == '/':
                lastpos = self.file.tell()
                nextc = self.file.read(1)
                if nextc == '/':
                    self.file.readline()
                elif nextc == '*':
                    self.current_comment_start_line = self.current_line
                    self.seek_comment_end()
                else:
                    self.file.seek(lastpos)
                    return '/'
            else:
                return c



    # main auxiliary method find_next_token:
    # sets the self.next_token field to a new Token read from self.file
    def find_next_token(self):
        self.next_token = None            # reset next token

        # treat first character separately:
        # if it is EOF or symbol, we can return right away
        # if it is a quotation mark, we are dealing with a string
        # otherwise, it is just the first character of an integer, identifier, or keyword token
        firstchar = self.read_next_real_char()

        if firstchar == None:           # reached EOF
            return
        
        if firstchar in JACK_SYMBOLS:   # return immediately if found a symbol
            self.next_token = Token("SYMBOL", firstchar)
            return
        
        new_token_content = ""

        is_string = firstchar == "\""    # if we start with quote, we enter string constant

        if not is_string:                # if we're not in a string, then the first char is part of token
            new_token_content += firstchar

        # main character read loop
        while True:
            lastpos = self.file.tell()
            char = self.file.read(1)
            if char == "\n":  # keep track of the line-count
                current_line += 1
            
            if is_string: # if we are in a string, continue reading unless we see the closing "
                if char == "\"":
                    self.next_token = Token("STRING_CONST", new_token_content)
                    break
                else:
                    new_token_content += char
            else: # if we are not in a string
                if char in JACK_SYMBOLS or char in JACK_WHITE or char == "\"": # any symbol, whitespace, or " means the new token has ended
                    self.file.seek(lastpos)
                    self.next_token = Token.from_content(new_token_content)
                    break
                else: # any other character should simply be added
                    new_token_content += char

        if self.next_token == None:    
            print("Syntax error: reached end of file while parsing token " + new_token_content)
            exit(0)

        return



    # API methods

    # constructor
    def __init__(self, filename):
        self.filename = filename
        try:
            self.file = open(filename, 'r')
        except FileNotFoundError:
            print(f"File {filename} not found")
        self.find_next_token()

    def has_more_tokens(self):
        return self.next_token != None

    def advance(self):
        assert self.has_more_tokens()
        self.current_token = self.next_token
        self.find_next_token()
        return
    
    def token_type(self):
        return current_token.token_type
    
    def keyword(self):
        assert current_token.token_type == "KEYWORD"
        return current_token.content
    
    def symbol(self):
        assert current_token.token_type == "SYMBOL"
        return current_token.content
    
    def identifier(self):
        assert current_token.token_type == "IDENTIFIER"
        return current_token.content

    def int_val(self):
        assert current_token.token_type == "INT_CONST"
        return current_token.content
    
    def string_val(self):
        assert current_token.token_type == "STRING_CONST"
        return current_token.content