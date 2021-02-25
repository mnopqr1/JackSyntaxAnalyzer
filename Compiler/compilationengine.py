from jacktokenizer import JackTokenizer
from symboltable import SymbolTable

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

    def writeintag(self, tagname, tagcontent):
        self.outfile.write(" " * self.current_level * INDENT_SIZE + "<" + tagname + "> " + tagcontent + " </"+ tagname + ">\n")


    def eat(self, s):
        for word in s.split(" "):
            assert self.tokenizer.next_content() == word, self.get_error(word)
            self.next_terminals(1)

    def next_terminals(self, n):
        for i in range(0,n):
            self.tokenizer.advance()
            self.write_terminal(self.tokenizer.ttype(), self.tokenizer.content())

    def get_contents(self, n):
        contents = []
        for i in range(0,n):
            self.tokenizer.advance()
            contents.append(self.tokenizer.content())
        return contents

    # error message when trying to eat
    def get_error(self, s):
        return "while writing " + self.outfilename + \
        ", expected token " + s + \
        ", but found token " + \
        self.tokenizer.next_content() + \
        " on line " + str(self.tokenizer.current_line)

    def compile_class(self):
        self.symboltable = SymbolTable()
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


    def write_identifier(self, sname, skind, being_defined, stype, index):
        self.opentag("identifier")

        self.writeintag("name",sname)
        self.writeintag("kind",skind)
        self.writeintag("isdefinition",str(being_defined))
        self.writeintag("type",stype)
        self.writeintag("index",str(index))

        self.closetag("identifier")
    def declare_symbol(self, skind, stype, sname):
        self.symboltable.define(sname, stype, skind)
        record = self.symboltable.get_record(sname)
        self.write_identifier(sname, record["kind"], True, record["type"], record["index"])

    def compile_class_var_dec(self):  # class variable declaration
        assert self.tokenizer.next_content() == "static" or self.tokenizer.next_content() == "field"
        self.opentag("classVarDec")
        
        identifier_info = self.get_contents(3) # static or field, type declaration, identifier name
        skind = identifier_info[0]
        stype = identifier_info[1]
        sname = identifier_info[2]
        self.declare_symbol(skind, stype, sname)
        
        while (self.tokenizer.next_content() == ","):
            self.eat(",")
            sname = self.get_contents(1)
            self.declare_symbol(skind, stype, sname)

        self.eat(";")
        
        self.closetag("classVarDec")

    def compile_subroutine_dec(self):                                         
        self.opentag("subroutineDec")                                        
        definition_info = self.get_contents(3)                                # subroutine kind, return type, name
        self.write_identifier(definition_info[2], definition_info[0], True, definition_info[1], -1)
        # self.next_terminals(3)                                              
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

        declaration_info = self.get_contents(3)
        skind = declaration_info[0] # var
        stype = declaration_info[1] # type
        sname = declaration_info[2] # first declared variable name

        self.declare_symbol(skind, stype, sname)
        
        while (self.tokenizer.next_content() != ';'):
            self.eat(",")
            sname = self.get_contents(1)[0] # next variable names
            self.declare_symbol(skind, stype, sname)
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
        sname = self.get_contents(1)[0]          # variable name
        self.lookup_and_write(sname)
        #self.next_terminals(1)                   # variable name
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
        sname = self.get_contents(1)[0]  # read first identifier
        
        self.finish_subroutine_call(sname)    # possibly add .identifier2, and (parameterlist)
        self.eat(";")                    # ;
        self.closetag("doStatement")

    """This method finishes a subroutine call, after having read the first name"""
    def finish_subroutine_call(self, firstname):
        if self.tokenizer.next_content() == '.': 
            self.eat(".")                              # .
            secondname = self.get_contents(1)[0]       # read subroutine name
            self.write_identifier(firstname, "class", False, "class", -1)
            self.write_identifier(secondname, "subroutine", False, "subroutine", -1)
        else: # otherwise the firstname was already a subroutine name within this class
            self.write_identifier(firstname, "subroutine", False, "subroutine", -1)
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
    
    def lookup_and_write(self, sname):
        record = self.symboltable.get_record(sname)
        self.write_identifier(sname,record["kind"],False,record["type"],record["index"])

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
            sname = self.get_contents(1)[0]  # get the identifier
            # the identifier names an array 
            if self.tokenizer.next_content() == '[':
                self.lookup_and_write(sname)
                self.eat('[')
                self.compile_expression()
                self.eat(']')
            # the identifier is part of a subroutine call
            elif self.tokenizer.next_content() == '.' or self.tokenizer.next_content() == '(': 
                self.finish_subroutine_call(sname)
            else:
            # if we are in none of these cases,  then the identifier must have been a varname, so we look it up
                self.lookup_and_write(sname)
                

        self.closetag("term")