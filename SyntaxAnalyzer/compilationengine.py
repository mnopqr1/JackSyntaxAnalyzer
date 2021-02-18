from jacktokenizer import JackTokenizer

JACK_SUBROUTINE_NAMES = ["constructor", "function", "method"]
JACK_STATEMENT_KEYWORDS = ["if", "let", "while", "do", "return"]
JACK_UNARY_OP = "-~"
JACK_BINARY_OP = "+-*/&|<>="
INDENT_SIZE = 2


class CompilationEngine:
    # constructor
    def __init__(self, filename):
        self.tokenizer = JackTokenizer(filename)
        self.outfilename = filename[:-4] + "xml"
        self.outfile = open(self.outfilename, 'w')
        self.current_level = 0
    
    # advance & write functions:
    # open xml tag, close xml tag, write terminal symbol, eat some terminal symbols
    def opentag(self, tagname):
        self.outfile.write(" " * self.current_level * INDENT_SIZE + "<" + tagname + ">" + "\n")
        self.current_level += 1

    def closetag(self, tagname):
        self.current_level -= 1
        self.outfile.write(" " * self.current_level * INDENT_SIZE + "</" + tagname + ">" + "\n")
    

    def write_terminal(self, ttype, content):
        self.outfile.write(" " * self.current_level * INDENT_SIZE + "<" + ttype + "> " + content + " </" + ttype + ">" + "\n")

    def eat(self, s):
        for word in s.split(" "):
            assert self.tokenizer.next_content() == word, self.get_error(word)
            self.next_terminals(1)

    def next_terminals(self, n):
        for i in range(0,n):
            self.tokenizer.advance()
            self.write_terminal(self.tokenizer.ttype(), self.tokenizer.content())

    # error message when trying to eat
    def get_error(self, s):
        return "while writing " + self.outfilename + \
        ", expected token " + s + \
        ", but found token " + \
        self.tokenizer.next_content() + \
        " on line " + str(self.tokenizer.current_line)

    def compile_class(self):
        self.opentag("class")
        self.eat("class")                       # class
        self.next_terminals(1)                  # name
        self.eat("{")                           # {

        
        # variable declarations
        while (self.tokenizer.next_content() != '}' and 
               self.tokenizer.next_token.content not in JACK_SUBROUTINE_NAMES):
            self.compile_class_var_dec()

        # subroutine declarations
        while self.tokenizer.next_content() != '}':
            self.compile_subroutine_dec()

        self.eat("}")                            # }
        self.closetag("class")

    def compile_class_var_dec(self):  # class variable declaration
        assert self.tokenizer.next_content() == "static" or self.tokenizer.next_content() == "field"
        self.opentag("classVarDec")
        
        self.next_terminals(3)        # static or field, type declaration, identifier name
        while (self.tokenizer.next_content() == ","):
            self.eat(",")
            self.next_terminals(1)
        
        self.eat(";")
        
        self.closetag("classVarDec")

    def compile_subroutine_dec(self):                                         # subroutine declaration
        self.opentag("subroutineDec")
        self.next_terminals(3)                                                # subroutine type, return type, name
        self.eat("(")                                                         # (parameters)
        self.compile_parameter_list()
        self.eat(")")

        self.opentag("subroutineBody")                                        # {
        self.eat("{")
        while (self.tokenizer.next_content() not in JACK_STATEMENT_KEYWORDS): # variable declarations
            self.compile_var_dec()

        self.opentag("statements")
        while (self.tokenizer.next_content() != '}'):                         # statements
            self.compile_statement()
        self.closetag("statements")

        self.eat("}")                                                         # }
        self.closetag("subroutineBody")

        self.closetag("subroutineDec")

    def compile_parameter_list(self):
        self.opentag("parameterList")
        while self.tokenizer.next_content() != ')':
            self.next_terminals(2)                    # variable type and name
            if self.tokenizer.next_content() != ')':  # ,
                self.eat(",") 
        self.closetag("parameterList")

    def compile_var_dec(self):    # variable declaration
        self.opentag("varDec")
        self.eat("var")            # var
        self.next_terminals(2)     # type name and first declared var name

        while (self.tokenizer.next_content() != ';'):
            self.eat(",")
            self.next_terminals(1) # next variable names
        self.eat(";")
        self.closetag("varDec")

    
    def compile_statement(self):
        assert self.tokenizer.next_content() in JACK_STATEMENT_KEYWORDS
        
        # dispatch to the correct statement compiler
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

        self.eat("let")                          # let
        self.next_terminals(1)                   # variable name
        if self.tokenizer.next_content() == '[': # possible array index
            self.eat('[')
            self.compile_expression()
            self.eat(']')

        self.eat('=')                            # =

        self.compile_expression()                # expression
        
        self.eat(';')                            # ;

        self.closetag("letStatement")

    def compile_if_statement(self):
        self.opentag("ifStatement")
                                         
        self.eat("if")                              # if
        self.eat("(")                               # (condition)
        self.compile_expression()
        self.eat(")")

        self.eat("{")                               # statement block
        self.compile_statements()
        self.eat("}")

        if self.tokenizer.next_content() == "else": # else
            self.eat("else")                        # statement block
            self.eat("{")
            self.compile_statements()
            self.eat("}")

        self.closetag("ifStatement")

    def compile_do_statement(self):
        self.opentag("doStatement")
        self.eat("do")                   # do
        self.next_terminals(1)           # identifier
        self.finish_subroutine_call()  # possibly add .identifier2, and (parameterlist)
        self.eat(";")                    # ;
        self.closetag("doStatement")

    """This method assumes we just wrote the first identifier in a subroutine call"""
    def finish_subroutine_call(self):
        if self.tokenizer.next_content() == '.': 
            self.eat(".")                # .
            self.next_terminals(1)       # subroutinename
        self.eat("(")
        self.compile_expression_list()   # expressions to go into parameters
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
        self.eat("while")                # while (condition)
        self.eat("(")                  
        self.compile_expression()
        self.eat(")")
        self.eat("{")                    # statement block
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
        self.eat("return")                # return
        if self.tokenizer.next_content() != ";":
            self.compile_expression()     # expression
        self.eat(";")                     # ;
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
        
        # first checks:
        # is the term a constant
        if self.tokenizer.next_token.is_constant():
            self.next_terminals(1)
        # is it a unary operator
        elif self.tokenizer.next_content() in JACK_UNARY_OP:
            self.next_terminals(1)
            self.compile_term()
        # is it a (expression)
        elif self.tokenizer.next_content() == '(':
            self.eat('(')
            self.compile_expression()
            self.eat(')')
        
        # if we did not succeed yet, then we must be reading an identifier
        # we look ahead to the next symbol, which can be [, (, ., or something else
        else:
            self.next_terminals(1)  # write the identifier
             # the identifier names an array 
            if self.tokenizer.next_content() == '[':
                self.eat('[')
                self.compile_expression()
                self.eat(']')
            # the identifier is part of a subroutine call
            elif self.tokenizer.next_content() == '.' or self.tokenizer.next_content() == '(': 
                self.finish_subroutine_call()
        
            # if we are in none of these cases,  then the identifier must have been a varname, 
            # and we've already written it, so nothing else to do.

        self.closetag("term")