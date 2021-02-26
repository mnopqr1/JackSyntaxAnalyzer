from jacktokenizer import JackTokenizer
from symboltable import SymbolTable
from vmwriter import VMWriter

JACK_SUBROUTINE_NAMES = ["constructor", "function", "method"]
JACK_STATEMENT_KEYWORDS = ["if", "let", "while", "do", "return"]
VM_SEGMENT_NAME = {"arg": "argument", "var": "local", "static": "static", "field": "this"}
VM_UNARY_OP_NAME = {"-" : "neg", "~" : "not"}
VM_BINARY_OP_NAME = {"+": "add", 
                     "-": "sub", 
                     "&": "and", 
                     "|" : "or", 
                     "<" : "lt", 
                     ">" : "gt", 
                     "=": "eq", 
                     "*" : "call Math.multiply 2",
                     "/" : "call Math.divide 2"}
JACK_UNARY_OP = "-~"
JACK_BINARY_OP = "+-*/&|<>="
INDENT_SIZE = 2


"""Where I left this Thursday 25 March 9pm:
* started making transition from writing XML file to VM file
* wrote vmwriter class
* need to rework all the compile-methods to write VM code
* rewrote compileclass
* started with the compilefunction method --> need to work on this
"""


class CompilationEngine:
    # constructor
    def __init__(self, filename):
        self.tokenizer = JackTokenizer(filename)
        self.write = VMWriter(filename[:-4] + "vm")
        self.outfile = open("dummyfile", 'w')
        self.classname = None

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
            self.tokenizer.advance()
            # self.next_terminals(1)

    def next_terminals(self, n):
        for i in range(0,n):
            self.tokenizer.advance()

    def get_contents(self, n):
        contents = []
        for i in range(0,n):
            self.tokenizer.advance()
            contents.append(self.tokenizer.content())
        return contents

    def get_content(self):
        self.tokenizer.advance()
        return self.tokenizer.content()

    # error message when trying to eat
    def get_error(self, s):
        return "while writing class " + self.classname + \
        ", expected token " + s + \
        ", but found token " + \
        self.tokenizer.next_content() + \
        " on line " + str(self.tokenizer.current_line)

    def compile_class(self):
        self.symboltable = SymbolTable()
        self.eat("class")                       # class
        self.classname = self.get_content()     # name        
        self.eat("{")                           # {
        
        # variable declarations
        while (self.tokenizer.next_content() != '}' and 
               self.tokenizer.next_token.content not in JACK_SUBROUTINE_NAMES):
            self.compile_class_var_dec()

        # subroutine declarations
        while self.tokenizer.next_content() != '}':
            self.compile_subroutine_dec()

        self.eat("}")                            # }


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
        [skind, rettype, sname] = self.get_contents(3)                        # subroutine kind, return type, name
                
        self.eat("(")                                                         # get parameters
        params = self.compile_parameter_list()                                                                       
        self.eat(")")

        self.symboltable.start_subroutine()
        
        for param in params:
            self.symboltable.define(param[1], param[0], "arg")

        
        self.eat("{")
        while (self.tokenizer.next_content() not in JACK_STATEMENT_KEYWORDS): # variable declarations
            self.compile_var_dec()

        self.opentag("statements")
        while (self.tokenizer.next_content() != '}'):                         # statements
            self.compile_statement()
        self.closetag("statements")

        self.eat("}")                                                         # }
        

        

    '''returns the list of parameters as a list of lists [vartype, varname]'''
    def compile_parameter_list(self):
        params = []
        while self.tokenizer.next_content() != ')':            
            params.append(self.get_contents(2))                    # variable type and name
            if self.tokenizer.next_content() != ')':  # ,
                self.eat(",") 
        return params

    def compile_var_dec(self):    
        [skind, stype, sname] = self.get_contents(3)
        
        self.declare_symbol(skind, stype, sname)
        
        while (self.tokenizer.next_content() != ';'):
            self.eat(",")
            sname = self.get_content() 
            self.declare_symbol(skind, stype, sname)
        
        self.eat(";")
        

    
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
        sname = self.get_content()               # variable name
        self.lookup_and_write(sname)
        
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
        self.eat("do")                   # do
        sname = self.get_content()       # read first identifier        
        fullname, n_params = self.get_call_info(sname)    # possibly add .identifier2, and (parameterlist)
        self.write.call(fullname, n_params)
        if False:      # TODO case of void function: caller must pop dummy return value
            self.write.pop("temp", 0)
        self.eat(";")                         # ;
        

    """This method gets the full info of a subroutine call, after having read the first name,
    and returns a list containing the full subroutine name, and the number of passed parameters."""
    def get_call_info(self, firstname):
        fullname = firstname
        if self.tokenizer.next_content() == '.': 
            self.eat(".")                              # .
            secondname = self.get_content()            # read subroutine name
            fullname += "." + secondname
        
        self.eat("(")
        n_params = self.compile_expression_list()   # push expressions for parameters onto stack
        self.eat(")")

        return fullname, n_params

    '''Pushes expressions in list onto stack, one by one'''
    def compile_expression_list(self):
        n = 0
        while self.tokenizer.next_content() != ')':
            n += 1
            self.compile_expression()
            if self.tokenizer.next_content() == ',':
                self.eat(",")
        return n

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
        self.eat("return")                # return
        if self.tokenizer.next_content() != ";":
            self.compile_expression()     # expression
        self.eat(";")                     # ;
        self.write.ret()
        
    '''Pushes the result of evaluating the next expression on top of the stack'''
    def compile_expression(self):
        # expression is a term, possibly followed by a number of repetitions of (op term)
        self.compile_term()
        while self.tokenizer.next_content() in JACK_BINARY_OP:
            operation = self.get_content()
            self.compile_term()
            self.write.arithmetic(VM_BINARY_OP_NAME[operation])

    def lookup_and_write(self, sname):
        record = self.symboltable.get_record(sname)
        self.write_identifier(sname,record["kind"],False,record["type"],record["index"])

    def lookup_and_push(self, sname):
        record = self.symboltable.get_record(sname)
        segment = VM_SEGMENT_NAME[record["kind"]]
        self.write.push(segment, record["index"])

    '''Pushes the result of evaluating the term on top of the stack'''
    def compile_term(self):
        self.opentag("term")
        
        # first checks:
        # is the term a constant
        if self.tokenizer.next_token.is_constant():
            value = self.get_content()
            self.write.push("constant ", value)
        # is it unary operator applied to a term
        elif self.tokenizer.next_content() in JACK_UNARY_OP:
            operation = self.get_content()
            self.compile_term()
            self.write.arithmetic(VM_UNARY_OP_NAME[operation])
        # is it a (expression)
        elif self.tokenizer.next_content() == '(':
            self.eat('(')
            self.compile_expression()
            self.eat(')')
        
        # if we did not succeed yet, then we must be reading an identifier
        # we look ahead to the next symbol, which can be [, (, ., or something else
        else:
            sname = self.get_content()  # get the identifier
            # the identifier names an array TODO
            if self.tokenizer.next_content() == '[':
                self.lookup_and_write(sname)
                self.eat('[')
                self.compile_expression()
                self.eat(']')
            # the identifier is part of a subroutine call TODO
            elif self.tokenizer.next_content() == '.' or self.tokenizer.next_content() == '(': 
                self.get_call_info(sname)
            else:
            # if we are in none of these cases, then the identifier must have been a simple varname, 
            # so we look it up and push it to the stack
                self.lookup_and_push(sname)
                

        self.closetag("term")