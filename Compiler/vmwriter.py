class VMWriter:

    def __init__(self, filename):
        self.file = open(filename, 'w')
        self.buffer = ""
    
    def putnow(self, string):
        self.file.write(string + "\n")

    def flush(self):
        self.file.write(self.buffer)
        self.buffer = ""

    def push(self, segment, idx):
        self.buffer += "push " + segment + " " + str(idx) + "\n"
    
    def pop(self, segment, idx):
        self.buffer += "pop " + segment + " " + str(idx) + "\n"
    
    def arithmetic(self, command):
        self.buffer += command + "\n"

    def label(self, name):
        self.buffer += "label " + name + "\n"
    
    def goto(self, name):
        self.buffer += "goto " + name + "\n"
    
    def ifgoto(self, name):
        self.buffer += "if-goto " + name + "\n"
    
    def call(self, name, n_args):
        self.buffer += "call " + name + " " + str(n_args) + "\n"
    
    def function(self, name, n_locals):
        self.buffer += "function " + name + str(n_locals) + "\n"

    def ret(self):
        self.buffer += "return\n"
    
    def close(self):
        self.file.close()