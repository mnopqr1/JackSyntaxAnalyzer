class VMWriter:

    def __init__(filename):
        self.file = open(filename, 'w')
    
    def push(self, segment, index):
        self.file.write("push " + segment + str(index) + "\n")
    
    def pop(self, segment, index):
        self.file.write("pop " + segment + str(index) + "\n")
    
    def arithmetic(self, command):
        self.file.write(command + "\n")

    def label(self, name):
        self.file.write("label " + name + "\n")
    
    def goto(self, name):
        self.file.write("goto " + name + "\n")
    
    def ifgoto(self, name):
        self.file.write("if-goto " + name + "\n")
    
    def call(self, name, n_args):
        self.file.write("call " + name + str(n_args) + "\n")
    
    def function(self, name, n_locals):
        self.file.write("function " + name + str(n_locals) + "\n")

    def ret(self):
        self.file.write("return\n")
    
    def close(self):
        self.file.close()