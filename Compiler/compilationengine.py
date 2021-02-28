from jacktokenizer import JackTokenizer
from symboltable import SymbolTable
from vmwriter import VMWriter

JACK_SUBROUTINE_NAMES = ["constructor", "function", "method"]
JACK_STATEMENT_KEYWORDS = ["if", "let", "while", "do", "return"]
VM_SEGMENT_NAME = {"arg": "argument", "var": "local",
                   "static": "static", "field": "this"}
VM_UNARY_OP_NAME = {"-": "neg", "~": "not"}
VM_BINARY_OP_NAME = {"+": "add",
                     "-": "sub",
                     "&": "and",
                     "|": "or",
                     "<": "lt",
                     ">": "gt",
                     "=": "eq",
                     "*": "call Math.multiply 2",
                     "/": "call Math.divide 2"}
JACK_UNARY_OP = "-~"
JACK_BINARY_OP = "+-*/&|<>="
INDENT_SIZE = 2


class CompilationEngine:
    # constructor
    def __init__(self, filename):
        self.writer = VMWriter(filename[:-4] + "vm")
        self.tokenizer = JackTokenizer(filename)
        self.classname = None

        self.next_label = 1


    def eat(self, s):
        for word in s.split(" "):
            if self.tokenizer.next_content() != word:
                raise ValueError(self.get_error(word))
            self.tokenizer.advance()

    def next_terminals(self, n):
        for i in range(0, n):
            self.tokenizer.advance()

    def get_contents(self, n):
        contents = []
        for i in range(0, n):
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

    # adds current Jack code line as a comment to buffer
    def commentline(self):
        self.writer.comment(self.tokenizer.getline())
    
    def commentlinenow(self):
        self.writer.commentnow(self.tokenizer.getline())

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


        # record = self.symboltable.get_record(sname)
        # self.write_identifier(sname, record["kind"], True, record["type"], record["idx"])

    def compile_class_var_dec(self):  # class variable declaration
        if not (self.tokenizer.next_content() == "static" or self.tokenizer.next_content() == "field"):
            raise ValueError("Expected static or field, but found " + self.tokenizer.next_content())

        # static or field, type declaration, identifier name
        [skind, stype, sname] = self.get_contents(3)
        self.symboltable.define(sname, stype, skind)

        while (self.tokenizer.next_content() == ","):
            self.eat(",")
            sname = self.get_content()
            self.symboltable.define(sname, stype, skind)

        self.eat(";")

    def compile_subroutine_dec(self):
        # subroutine kind, return type, name
        [skind, rettype, sname] = self.get_contents(3)

        # get parameters
        self.eat("(")
        params = self.compile_parameter_list()
        self.eat(")")

        self.symboltable.start_subroutine()

        # add parameter names to symbol table as arguments
        for param in params:
            self.symboltable.define(param[1], param[0], "arg")

        # print("current subroutine: " + sname)
        # self.symboltable.diagnostics()

        if skind == "constructor":
            self.new_object()
            self.set_this_base()
            # self.symboltable.define("this", self.classname, "var")

        if skind == "method":
            # self.set_this_base() -> was a bug, method already has "this" as argument, don't set base.
            self.symboltable.define("this", self.classname, "arg")
            self.writer.push("argument", 0)
            self.writer.pop("pointer", 0)     # set the "this" pointer to argument 0

        self.eat("{")
        while (self.tokenizer.next_content() not in JACK_STATEMENT_KEYWORDS):  # variable declarations
            self.compile_var_dec()

        while (self.tokenizer.next_content() != '}'):                         # statements
            self.compile_statement()

        self.eat("}")
        self.writer.putnow("function " + self.classname + "." +
                           sname + " " + str(self.symboltable.assign_next["var"]))
        self.writer.flush()

    def new_object(self):
        n_fields = self.symboltable.var_count("field")
        self.writer.push("constant", n_fields)
        self.writer.call("Memory.alloc", 1)

    def set_this_base(self):  # pops address from top of stack into pointer 0
        self.writer.pop("pointer", 0)

    '''returns the list of parameters as a list of lists [vartype, varname]'''

    def compile_parameter_list(self):
        params = []
        while self.tokenizer.next_content() != ')':
            # variable type and name
            params.append(self.get_contents(2))
            if self.tokenizer.next_content() != ')':  # ,
                self.eat(",")
        return params

    def compile_var_dec(self):
        [skind, stype, sname] = self.get_contents(3)
        self.symboltable.define(sname, stype, skind)

        while (self.tokenizer.next_content() != ';'):
            self.eat(",")
            sname = self.get_content()
            self.symboltable.define(sname, stype, skind)

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
        self.eat("let")                          # let
        sname = self.get_content()               # variable name
        stype, skind, idx = self.symboltable.get_record(sname).values()

        # are we assigning to an array?
        assign_to_array = self.tokenizer.next_content() == '['

        # then the intermediate temp register is needed to deal with examples like
        # let a[some_method(4)] = 10 * another_method(b[5]) - 3
        if assign_to_array:
            self.eat('[')
            self.compile_expression()
            self.writer.pop("temp", 1)
            self.eat(']')

        self.eat('=')
        # push value X of expression on top of stack
        self.compile_expression()

        if assign_to_array:
            # find destination address in memory
            self.writer.push(VM_SEGMENT_NAME[skind], idx)
            self.writer.push("temp", 1)
            self.writer.arithmetic("add")
            # pop this address to the pointer
            self.writer.pop("pointer", 1)
            # now pop the value X to that
            self.writer.pop("that", 0)
        else:
            self.writer.pop(VM_SEGMENT_NAME[skind], idx)

        self.eat(';')                            # ;

    def fresh_label(self):
        self.next_label += 1
        return "L" + str(self.next_label - 1)

    def compile_if_statement(self):
        self.eat("if")                              # if
        self.eat("(")                               # (condition)
        self.compile_expression()
        self.eat(")")

        self.writer.arithmetic("not")

        elseblock = self.fresh_label()
        afterif = self.fresh_label()
        self.writer.ifgoto(elseblock)

        self.eat("{")                               # statement block
        self.compile_statements()
        self.eat("}")
        self.writer.goto(afterif)
        
        self.writer.label(elseblock)
        if self.tokenizer.next_content() == "else":  # else
            self.eat("else")                        # statement block
            self.eat("{")
            self.compile_statements()
            self.eat("}")
        self.writer.label(afterif)

    def compile_do_statement(self):
        self.eat("do")                   # do
        sname = self.get_content()       # read first identifier
        # possibly add .identifier2, push parameterlist onto stack and call
        self.compile_call(sname)

        # dump return value (do statement treats called function as void)
        self.writer.pop("temp", 0)
        self.eat(";")                         # ;

    """compile_call gets the full info of a subroutine call, after having read the first name,
    and writes the parameters and then the call command."""
    def compile_call(self, firstname):
        
        n_params = 0
        if self.tokenizer.next_content() == '.':       # CASE 1: firstname.secondname
            self.eat(".")                              # .
            secondname = self.get_content()            # read subroutine name
            
            if firstname[0].islower():                 # CASE 1a: firstname = identifier of some object instance, secondname = method
                # pass that instance as first argument
                objkind = self.symboltable.kind_of(firstname)
                objidx = self.symboltable.idx_of(firstname)
                self.writer.push(VM_SEGMENT_NAME[objkind], objidx)
                n_params = 1
                # and need to call the method from that class
                fullname = self.symboltable.type_of(firstname) + "." + secondname
            else:                                       # CASE 1b: firstname = class name, secondname = function name
                fullname = firstname + "." + secondname
        else:                                           # CASE 2: firstname only, then the callee must be a method (!) from this class
            fullname = self.classname + "." + firstname   
            # pass "this" as first argument
            self.writer.push("pointer", 0)
            n_params = 1

        self.eat("(")
        # push expressions for explicit parameters onto stack
        n_params += self.compile_expression_list()
        self.eat(")")
        self.writer.call(fullname, n_params)

    '''compile_expression pushes expressions in list onto stack, one by one'''
    def compile_expression_list(self):
        n = 0
        while self.tokenizer.next_content() != ')':
            n += 1
            self.compile_expression()
            if self.tokenizer.next_content() == ',':
                self.eat(",")
        return n

    def compile_while_statement(self):
        beginwhile = self.fresh_label()
        endwhile = self.fresh_label()

        self.writer.label(beginwhile)    # label beginning of while loop

        self.eat("while")                # while (condition)
        self.eat("(")
        self.compile_expression()
        self.eat(")")
        self.writer.arithmetic("not")    
        self.writer.ifgoto(endwhile)     # if not (condition), jump to end while

        self.eat("{")                    # statement block
        self.compile_statements()
        self.eat("}")
        self.writer.goto(beginwhile)     # go back to beginwhile

        self.writer.label(endwhile)      # label end of while loop

    def compile_statements(self):
        while self.tokenizer.next_content() != '}':
            self.compile_statement()

    def compile_return_statement(self):
        self.eat("return")                # return
        if self.tokenizer.next_content() == "this":
            # "return this" should push pointer 0 (in a constructor)
            self.writer.push("pointer", 0)
            self.eat("this")
        elif self.tokenizer.next_content() == ";":
            # for a void function, push constant 0 as return value
            self.writer.push("constant", 0)
        else:
            self.compile_expression()     # expression
        self.eat(";")                     # ;
        self.writer.ret()

    '''Pushes the result of evaluating the next expression on top of the stack'''

    def compile_expression(self):
        # expression is a term, possibly followed by a number of repetitions of (op term)
        self.compile_term()
        while self.tokenizer.next_content() in JACK_BINARY_OP:
            operation = self.get_content()
            self.compile_term()
            self.writer.arithmetic(VM_BINARY_OP_NAME[operation])

    def lookup_and_push(self, sname):
        record = self.symboltable.get_record(sname)
        segment = VM_SEGMENT_NAME[record["kind"]]
        self.writer.push(segment, record["idx"])

    """Creates a new string constant containing "content"
    and pushes its address on top of the stack"""
    def create_string(self, content):
        # tell OS to create a new string of len(content) characters
        self.writer.push("constant", len(content))
        self.writer.call("String.new", 1)
        # the new string's base address is now on top of the stack
        for c in content:
            self.writer.push("constant", ord(c)) # push the character's ascii ordinal
            self.writer.call("String.appendChar", 2) # call the method on the string
            # the return value is again the string's base address, 
            # which may be used for the next character
        # at the end, we have the new string's base address on top of the stack


    def compile_constant_term(self):
        self.tokenizer.advance()
        const_token = self.tokenizer.current_token

        if not const_token.is_constant():
            raise ValueError("Expected constant token but found: " + const_token.content)

        if const_token.token_type == "integerConstant":
            self.writer.push("constant", const_token.content)
        elif const_token.token_type == "stringConstant":
            self.create_string(const_token.content)
        elif const_token.content == "this":
            self.writer.push("pointer", 0)
        elif const_token.content in ["false", "null"]:
            self.writer.push("constant", 0)
        elif const_token.content == "true":
            self.writer.push("constant", 0)
            self.writer.arithmetic("not")
        else:
            raise ValueError("Could not handle constant token : " + const_token.content)
    
    '''Pushes the result of evaluating the term on top of the stack'''
    def compile_term(self):
        # first checks:
        # is the term a constant
        if self.tokenizer.next_token.is_constant():
            self.compile_constant_term()
        # is it unary operator applied to a term
        elif self.tokenizer.next_content() in JACK_UNARY_OP:
            operation = self.get_content()
            self.compile_term()
            self.writer.arithmetic(VM_UNARY_OP_NAME[operation])
        # is it a (expression)
        elif self.tokenizer.next_content() == '(':
            self.eat('(')
            self.compile_expression()
            self.eat(')')

        # if we did not succeed yet, then we must be reading an identifier
        # we look ahead to the next symbol, which can be [, (, ., or something else
        else:
            sname = self.get_content()  # get the identifier
            # the identifier names an array
            if self.tokenizer.next_content() == '[':
                record = self.symboltable.get_record(sname)
                self.eat('[')
                self.compile_expression()
                self.eat(']')
                self.writer.push(VM_SEGMENT_NAME[record["kind"]], record["idx"]) # array base location
                self.writer.arithmetic("add")
                self.writer.pop("pointer", 1) # set "that" pointer to correct location
                self.writer.push("that", 0)   # push that 0 onto stack
            # the identifier is part of a subroutine call TODO check that this works?
            elif self.tokenizer.next_content() == '.' or self.tokenizer.next_content() == '(':
                self.compile_call(sname)
            else:
                # if we are in none of these cases, then the identifier must have been a simple varname,
                # so we look it up and push it to the stack
                self.lookup_and_push(sname)
