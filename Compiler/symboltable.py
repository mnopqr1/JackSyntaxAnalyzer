class SymbolTable:
    def __init__(self):
        self.class_table = {}
        self.subroutine_table = {}
        self.assign_next = {"static" : 0, "field" : 0, "arg" : 0, "var" : 0}

    def start_subroutine(self):
        self.subroutine_table = {}
        self.assign_next["arg"] = 0
        self.assign_next["var"] = 0
    
    '''Define a new identifier of given sname, stype and skind (static, field, arg or var)
    and assign a running idx to it'''
    def define(self, sname, stype, skind):
        if skind not in {"static", "field", "arg", "var"}:
            raise ValueError("Unrecognized identifier kind: " + skind + ". Must be static, field, arg or var.")
        new_record = {"type" : stype, "kind" : skind, "idx" : self.assign_next[skind]}
        self.assign_next[skind] += 1
        if skind == "static" or skind == "field":
            self.class_table[sname] = new_record
        elif skind == "arg" or skind == "var": 
            self.subroutine_table[sname] = new_record

    def var_count(self, skind):
        return self.assign_next[skind]
    
    def get_record(self, sname):
        assert sname in self.subroutine_table.keys() or sname in self.class_table.keys(), \
            "Unrecognized symbol name: " + sname
        if sname in self.subroutine_table.keys():
            return self.subroutine_table[sname]
        else:
            return self.class_table[sname]

    def is_local(self, sname):
        return sname in self.subroutine.table.keys()

    def kind_of(self, sname):
        return self.get_record(sname)["kind"]

    def type_of(self, sname):
        return self.get_record(sname)["type"]

    def idx_of(self, sname):
        return self.get_record(sname)["idx"]

    def diagnostics(self):
        print("symboltable class: ") 
        print(self.class_table)
        print("symboltable subroutine: ") 
        print(self.subroutine_table)