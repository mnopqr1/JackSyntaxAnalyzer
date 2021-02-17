from jacktokenizer import JackTokenizer

JACK_SUBROUTINE_NAMES = ["constructor", "function", "method"]
JACK_STATEMENT_KEYWORDS = ["if", "let", "while", "do", "return"]
INDENT_SIZE = 3


class CompilationEngine:
    def __init__(self, filename):
        self.tokenizer = JackTokenizer(filename)
        self.outfilename = filename[:-4] + "xml"
        self.outfile = open(self.outfilename, 'w')
        self.current_level = 0
    
    def write_open(self, tagname):
        self.outfile.write(" " * self.current_level * INDENT_SIZE + "<" + tagname + ">" + "\n")
        self.current_level += 1

    def write_close(self, tagname):
        self.current_level -= 1
        self.outfile.write(" " * self.current_level * INDENT_SIZE + "</" + tagname + ">" + "\n")
        

    def write_terminal(self, ttype, content):
        self.outfile.write(" " * self.current_level * INDENT_SIZE + "<" + ttype + "> " + content + " </" + ttype + ">" + "\n")

    def write_next_terminals(self, n):
        for i in range(0,n):
            self.tokenizer.advance()
            self.write_terminal(self.tokenizer.ttype(), self.tokenizer.content())
            

    def write_class_end(self):
        pass

    def compile_class(self):
        self.write_open("class")
        self.write_next_terminals(3) # class initialization consists of "class", "name", "{"
        
        # the class variable declarations run until either the closing '}' of the class,
        # or the first time we see a subroutine declaration.
        while (self.tokenizer.next_content() != '}' and 
               self.tokenizer.next_token.content not in JACK_SUBROUTINE_NAMES):
            self.compile_class_var_dec()
            

        # the subroutine declarations then run until we see the closing '}'
        while self.tokenizer.next_content() != '}':
            self.compile_subroutine_dec()

        self.write_next_terminals(1) # write the closing } symbol
        self.write_close("class")

    def compile_class_var_dec(self):
        assert self.tokenizer.next_content() == "static" or self.tokenizer.next_content() == "field"
        self.write_open("classVarDec")
        
        self.write_next_terminals(3)  # write the static or field, type declaration, identifier name
        while (self.tokenizer.next_content() == ","):
            self.now_write(",")
            self.write_next_terminals(1)
        
        self.now_write(";")
        
        self.write_close("classVarDec")

    def compile_subroutine_dec(self):
        self.write_open("subroutineDec")
        self.write_next_terminals(4) # write subroutine type, return type, name, and ( for parameter list
        self.compile_parameter_list()
        self.write_next_terminals(1)  # closing ) of parameter list

        self.write_open("subroutineBody")
        self.write_next_terminals(1)  # opening { for subroutine
        while (self.tokenizer.next_content() not in JACK_STATEMENT_KEYWORDS):
            self.compile_var_dec()
        self.write_open("statements")
        while (self.tokenizer.next_content() != '}'):
            self.compile_statement()
        self.write_close("statements")
        self.write_next_terminals(1) # closing } for subroutine
        self.write_close("subroutineBody")

        self.write_close("subroutineDec")

    def compile_parameter_list(self):
        self.write_open("parameterList")
        while self.tokenizer.next_content() != ')':
            self.write_next_terminals(2) # write the variable type and name
            if self.tokenizer.next_content == ')':
                self.write_next_terminals(1) # write the comma if it is there
        self.write_close("parameterList")

    def compile_var_dec(self):
        self.write_open("varDec")
        self.now_write("var")
        self.write_next_terminals(2) # write the var keyword, type name and first declared var name

        while (self.tokenizer.next_content() != ';'):
            self.write_next_terminals(2) # write the comma and next variable name
        self.write_next_terminals(1) # write the end of line semicolon
        self.write_close("varDec")

    
    def compile_statement(self):
        assert self.tokenizer.next_content() in JACK_STATEMENT_KEYWORDS
        statement_type = self.tokenizer.next_content()
        if statement_type == "let":
            self.compile_let_statement()
        if statement_type == "do":
            self.compile_do_statement()
        if statement_type == "while":
            self.compile_while_statement()            
        if statement_type == "if":
            self.compile_if_statement()
        if statement_type == "return":
            self.compile_return_statement()
    
    def get_assertion_err(self, s):
        return "while writing " + self.outfilename + \
        ", expected token " + s + \
        ", but found token " + \
        self.tokenizer.next_content() + \
        " on line " + str(self.tokenizer.current_line)

    def now_write(self, s):
        assert self.tokenizer.next_content() == s, get_assertion_err(s)
        self.write_next_terminals(1)

    def compile_let_statement(self):
        self.write_open("letStatement")
        self.now_write("let") 
        self.write_next_terminals(1) # write var name
        if self.tokenizer.next_content() == '[':
            self.now_write('[')
            self.compile_expression()
            self.now_write(']')

        self.now_write('=')
        self.compile_expression()
        
        self.now_write(';')

        self.write_close("letStatement")

    def compile_if_statement(self):
        self.write_open("ifStatement")
        self.now_write("if")
        self.now_write("(")
        self.compile_expression()
        self.now_write(")")
        self.now_write("{")
        self.compile_statements()
        self.now_write("}")
        if self.tokenizer.next_content() == "else":
            self.now_write("else")
            self.now_write("{")
            self.compile_statements()
            self.now_write("}")
        self.write_close("ifStatement")

    def compile_do_statement(self):
        self.write_open("doStatement")
        self.now_write("do")
        self.compile_subroutine_call()
        self.now_write(";")
        self.write_close("doStatement")

    def compile_subroutine_call(self):
        # subroutine call is not encapsulated in tag (not sure why...)
        self.write_next_terminals(1) # write identifier: subroutineName or className or varName
        if self.tokenizer.next_content() == '.': 
            self.now_write(".")
            self.write_next_terminals(1) # write the true subroutineName
        self.now_write("(")
        self.compile_expression_list()
        self.now_write(")")

    
    def compile_expression_list(self):
        self.write_open("expressionList")
        while self.tokenizer.next_content() != ')':
            self.compile_expression()
            if self.tokenizer.next_content() == ',':
                self.now_write(",")
        self.write_close("expressionList")

    def compile_while_statement(self):
        self.write_open("whileStatement")
        self.now_write("while")
        self.now_write("(")
        self.compile_expression()
        self.now_write(")")
        self.now_write("{")
        self.compile_statements()
        self.now_write("}")
        self.write_close("whileStatement")

    def compile_statements(self):
        self.write_open("statements")
        while self.tokenizer.next_content() != '}':
            self.compile_statement()
        self.write_close("statements")

    def compile_return_statement(self):
        self.write_open("returnStatement")
        self.now_write("return")
        if self.tokenizer.next_content() != ";":
            self.compile_expression()
        self.now_write(";")
        self.write_close("returnStatement")

    def compile_expression(self):
        self.write_open("expression")
        
        # expression is non-empty list of terms but for now it is just one term
        self.compile_term()

        self.write_close("expression")
    
    def compile_term(self):
        self.write_open("term")
        self.write_next_terminals(1)  # a term is just a single terminal for now
        self.write_close("term")
