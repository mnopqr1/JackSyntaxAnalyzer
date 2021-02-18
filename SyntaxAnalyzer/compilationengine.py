from jacktokenizer import JackTokenizer

JACK_SUBROUTINE_NAMES = ["constructor", "function", "method"]
JACK_STATEMENT_KEYWORDS = ["if", "let", "while", "do", "return"]
JACK_UNARY_OP = "-~"
JACK_BINARY_OP = "+-*/&|<>="
INDENT_SIZE = 2


class CompilationEngine:
    def __init__(self, filename):
        self.tokenizer = JackTokenizer(filename)
        self.outfilename = filename[:-4] + "xml"
        self.outfile = open(self.outfilename, 'w')
        self.current_level = 0
    
    def opentag(self, tagname):
        self.outfile.write(" " * self.current_level * INDENT_SIZE + "<" + tagname + ">" + "\n")
        self.current_level += 1

    def closetag(self, tagname):
        self.current_level -= 1
        self.outfile.write(" " * self.current_level * INDENT_SIZE + "</" + tagname + ">" + "\n")
    
    def get_assertion_err(self, s):
        return "while writing " + self.outfilename + \
        ", expected token " + s + \
        ", but found token " + \
        self.tokenizer.next_content() + \
        " on line " + str(self.tokenizer.current_line)

    def eat(self, s):
        for word in s.split(" "):
            assert self.tokenizer.next_content() == word, get_assertion_err(word)
            self.next_terminals(1)

    def write_terminal(self, ttype, content):
        self.outfile.write(" " * self.current_level * INDENT_SIZE + "<" + ttype + "> " + content + " </" + ttype + ">" + "\n")

    def next_terminals(self, n):
        for i in range(0,n):
            self.tokenizer.advance()
            self.write_terminal(self.tokenizer.ttype(), self.tokenizer.content())

    def compile_class(self):
        self.opentag("class")
        self.next_terminals(3) # class initialization consists of "class", "name", "{"
        
        # the class variable declarations run until either the closing '}' of the class,
        # or the first time we see a subroutine declaration.
        while (self.tokenizer.next_content() != '}' and 
               self.tokenizer.next_token.content not in JACK_SUBROUTINE_NAMES):
            self.compile_class_var_dec()
            

        # the subroutine declarations then run until we see the closing '}'
        while self.tokenizer.next_content() != '}':
            self.compile_subroutine_dec()

        self.next_terminals(1) # write the closing } symbol
        self.closetag("class")

    def compile_class_var_dec(self):
        assert self.tokenizer.next_content() == "static" or self.tokenizer.next_content() == "field"
        self.opentag("classVarDec")
        
        self.next_terminals(3)  # write the static or field, type declaration, identifier name
        while (self.tokenizer.next_content() == ","):
            self.eat(",")
            self.next_terminals(1)
        
        self.eat(";")
        
        self.closetag("classVarDec")

    def compile_subroutine_dec(self):
        self.opentag("subroutineDec")
        self.next_terminals(4) # write subroutine type, return type, name, and ( for parameter list
        self.compile_parameter_list()
        self.next_terminals(1)  # closing ) of parameter list

        self.opentag("subroutineBody")
        self.next_terminals(1)  # opening { for subroutine
        while (self.tokenizer.next_content() not in JACK_STATEMENT_KEYWORDS):
            self.compile_var_dec()
        self.opentag("statements")
        while (self.tokenizer.next_content() != '}'):
            self.compile_statement()
        self.closetag("statements")
        self.next_terminals(1) # closing } for subroutine
        self.closetag("subroutineBody")

        self.closetag("subroutineDec")

    def compile_parameter_list(self):
        self.opentag("parameterList")
        while self.tokenizer.next_content() != ')':
            self.next_terminals(2) # write the variable type and name
            if self.tokenizer.next_content == ')':
                self.next_terminals(1) # write the comma if it is there
        self.closetag("parameterList")

    def compile_var_dec(self):
        self.opentag("varDec")
        self.eat("var")
        self.next_terminals(2) # write type name and first declared var name

        while (self.tokenizer.next_content() != ';'):
            self.next_terminals(2) # write the comma and next variable name
        self.next_terminals(1) # write the end of line semicolon
        self.closetag("varDec")

    
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

    def compile_let_statement(self):
        self.opentag("letStatement")
        self.eat("let") 
        self.next_terminals(1) # write var name
        if self.tokenizer.next_content() == '[':
            self.eat('[')
            self.compile_expression()
            self.eat(']')

        self.eat('=')
        self.compile_expression()
        
        self.eat(';')

        self.closetag("letStatement")

    def compile_if_statement(self):
        self.opentag("ifStatement")
        self.eat("if")
        self.eat("(")
        self.compile_expression()
        self.eat(")")
        self.eat("{")
        self.compile_statements()
        self.eat("}")
        if self.tokenizer.next_content() == "else":
            self.eat("else")
            self.eat("{")
            self.compile_statements()
            self.eat("}")
        self.closetag("ifStatement")

    def compile_do_statement(self):
        self.opentag("doStatement")
        self.eat("do")
        self.next_terminals(1) # write first identifier: subroutineName or className or varName
        self.complete_subroutine_call()
        self.eat(";")
        self.closetag("doStatement")

    """This method assumes we just wrote the first identifier in a subroutine call
    """
    def complete_subroutine_call(self):
        if self.tokenizer.next_content() == '.': 
            self.eat(".")
            self.next_terminals(1) # write the true subroutineName
        self.eat("(")
        self.compile_expression_list()
        self.eat(")")

    
    def compile_expression_list(self):
        self.opentag("expressionList")
        while self.tokenizer.next_content() != ')':
            self.compile_expression()
            if self.tokenizer.next_content() == ',':
                self.eat(",")
        self.closetag("expressionList")

    def compile_while_statement(self):
        self.opentag("whileStatement")
        self.eat("while")
        self.eat("(")
        self.compile_expression()
        self.eat(")")
        self.eat("{")
        self.compile_statements()
        self.eat("}")
        self.closetag("whileStatement")

    def compile_statements(self):
        self.opentag("statements")
        while self.tokenizer.next_content() != '}':
            self.compile_statement()
        self.closetag("statements")

    def compile_return_statement(self):
        self.opentag("returnStatement")
        self.eat("return")
        if self.tokenizer.next_content() != ";":
            self.compile_expression()
        self.eat(";")
        self.closetag("returnStatement")

    def compile_expression(self):
        self.opentag("expression")
        
        # expression is a term, possibly followed by a number of repetitions of (op term)
        self.compile_term()
        while self.tokenizer.next_content() in JACK_BINARY_OP:
            self.next_terminals(1)
            self.compile_term()

        self.closetag("expression")
    
    def compile_term(self):
        self.opentag("term")
        
        if self.tokenizer.next_token.is_constant():
            self.next_terminals(1)
        elif self.tokenizer.next_content() in JACK_UNARY_OP:
            self.next_terminals(1)
            self.compile_term()
        elif self.tokenizer.next_content() == '(':
            self.eat('(')
            self.compile_expression()
            self.eat(')')
        
        # if we did not succeed yet, then we must be reading an identifier
        # we look ahead to the next symbol, which can be [, (, ., or something else
        else:
            self.next_terminals(1)
            if self.tokenizer.next_content() == '[': # the identifier is an array 
                self.eat('[')
                self.compile_expression()
                self.eat(']')
            elif self.tokenizer.next_content() == '.' or self.tokenizer.next_content() == '(': # the identifier 
                self.complete_subroutine_call()
        
            # if we are in none of these cases, 
            # then the identifier must have been a varname, 
            # and we've already written it,
            # so nothing else to do.

        self.closetag("term")