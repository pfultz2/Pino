#!/usr/bin/python
#
#    pino.py
#
#    Copyright (c) 2011, Paul Fultz II
#    All rights reserved.
#
#    Redistribution and use in source and binary forms, with or without
#    modification, are permitted provided that the following conditions are met: 
#
#    1. Redistributions of source code must retain the above copyright notice, this
#       list of conditions and the following disclaimer. 
#    2. Redistributions in binary form must reproduce the above copyright notice,
#       this list of conditions and the following disclaimer in the documentation
#       and/or other materials provided with the distribution. 
#
#    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#    ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#    WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#    DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
#    ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#    (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#    LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#    ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#    (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#    SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#


import re
import string
import sys, os
import getopt

# content => (block | statement | .)*
# statement => $func;
# expression => $(func)
# block => $func { content }

__ptoken__ = '$'

class Lexer:
    lexer_regex = "\\w+|\\s+|\\W"
    def __init__(self, s, index=-1, tokens=""):
        self.s = s
        self.index = index
        if (tokens == ""): self.tokens = re.findall(Lexer.lexer_regex, s)
        else: self.tokens = tokens
        
    def Next(self):
        self.index = self.index + 1
        return self.tokens[self.index]
        
    def HasNext(self):
        return self.index < (len(self.tokens) - 1)
        
    def Copy(self):
        return Lexer(self.s, self.index, self.tokens)
        
class VariableStack:
    def __init__(self):    
        self.stack = []
        
    def peek(self):
        last = len(self.stack) - 1
        if last < 0: return dict()
        else: return self.stack[len(self.stack) - 1]
    
    def push(self, vars):
        self.stack.append(dict(self.peek().items() + dict(vars).items()))
                          
    def pop(self):
        return self.stack.pop()
        
    def __len__(self):
        return len(self.stack)
        
        
        
def remove_empty_lines(s):
    result = []
    for line in s.split('\n'):
        if (not is_empty(line)): result.append(line)
    if len(result) > 1: return '\n' + string.join(result, '\n')
    elif len(result) == 1: return result[0].strip()
    else: return ''
        
        
def is_empty(s):
    for c in s:
        if c not in string.whitespace: return False
    return True
    
            

class TemplateEngine:
    def __init__(self):
        self.commands = dict()
        self.commands["if"] = self.if_
        self.commands["for"] = self.for_
        self.stack = VariableStack()
        
        
    
    def Process(self, s):
        self.stack.push(locals())
        return self.process_template(s)
        
    def AddCommand(self, token, command):
        self.commands[token] = command
        
    def AddMacro(self, func):
        self.commands[func.__name__] = lambda statement, content: func(self.token_tail(statement).strip(), self.process_template(content))
        
    def if_(self, statement, content):
        tail = self.token_tail(statement).strip()
        try:
            if eval(tail, globals(), self.stack.peek()): return self.process_template(content)
        except:
            print "Cant evaluate", statement, content
            raise
        return ''
                
        
    def for_(self, statement__, content__):
        code__ = "result__ = ''\n" + statement__.strip() + ":\n\t" + \
        "self.stack.push(locals())\n\t" + \
        "result__ += self.process_template(content__)\n\t" + \
        "self.stack.pop()"
        try:
            self.stack.push(locals())
            exec code__ in globals(), self.stack.peek()
            return self.stack.pop()["result__"]
        except:
            print "Error processing block: ", code__
            raise
        
        return ''
        
            
    def Call(self, statement, content):
        head = self.token_head(statement).strip()
        try:
            out = ''
            if (head in self.commands): out = self.commands[head](statement, content)
            else: out = eval(statement.strip(), globals(), self.stack.peek())
            out = str(out)
            if (len(out.strip()) == 0): out = ''
            return remove_empty_lines(out)
        except:
            print "Error calling: ", statement, content
            raise
        

    #deprecated
    def parse_statement(self, lexer):
        if (lexer.HasNext() and lexer.Next() == __ptoken__):
            #print "parse statement"
            statement = ''
            while(lexer.HasNext()):
                token = lexer.Next()
                if (token == '{'): break
                if (token == ';'):
                    #print "statement:", statement 
                    return (lexer, statement)
                statement += token
        return (None, '')
                
    def parse_block(self, lexer):
        if (lexer.HasNext() and lexer.Next() == __ptoken__):
            statement = ''
            while(lexer.HasNext()):
                token = lexer.Next()
                if (token == ';'): break
                if (token == '{'):
                    (lex, content) = self.parse_content(lexer.Copy())
                    return (lex, statement, content)
                statement += token
        return (None, '', '')
        
        
    def parse_expr(self, lexer):
        if (lexer.HasNext() and lexer.Next() == __ptoken__ and lexer.HasNext() and lexer.Next() == '('):
            stack = VariableStack()
            statement = ''
            while(lexer.HasNext()):
                token = lexer.Next()
                if (token =='('): stack.push({'(': ')'})
                if (token == '{'): break
                if (token == ')'):
                    if (len(stack) == 0): return (lexer, statement)
                    else: stack.pop()
                statement += token
        return (None, '')
            
            
    def parse_content(self, lexer, include_close_brace=False):
        statement = ''
        while(lexer.HasNext()):
            token = lexer.Next()
            
            if (token == '{'):
                statement += token
                (lex, content) = self.parse_content(lexer.Copy(), True)
                statement += content
                lexer = lex
            elif (token == '}'):
                if (include_close_brace): statement += token
                return (lexer, statement)
            else:
                statement += token
        return (lexer, statement)
        
    def process_template(self, s):
        out = ''
        lexer = Lexer(s)
        while (lexer.HasNext()):
            content = ''
            (lex, statement) = self.parse_expr(lexer.Copy())
            if (lex == None): (lex, statement, content) = self.parse_block(lexer.Copy())
            
            if (lex == None):
                out += lexer.Next()
            else:
                lexer = lex
                out += str(self.Call(statement, content))
        return out
    
    def token_head(self, s):
        tokens = re.findall("\\w+", s)
        if (len(tokens) > 0): return tokens[0]
        else: return ''
        
    def token_tail(self, s):
        head = self.token_head(s)
        i = s.find(head)
        #print head, i
        if i >= 0: return s[i+len(head):]
        else: return ''
        
        
def quote(s):
    return '"' + s + '"'
                
def usage():
        print "Usage: pino.py [OPTIONS] [input-file] [output-file]"
        print ""
        print " -c, --config    a python file(rather than a \".pino\" file) where you can define variables"
        print "                 and functions that are available in the template file"
        print "                 If an input file and output file is not specified then the files to be"
        print "                 processed must be specified in the python file. This can be done by defining "
        print "                 a list called templates that contain a tuple with the template file to be "
        print "                 processed and the name of the output file"
        print "                 (eg. templates = [(\"MyTemplateHeader.h\", \"MyHeader.h\"), (\"MyTemplateSrc.cpp\", \"MySrc.cpp\")])"
        print " -h, --help      display this help and exit"
        exit()

if len(sys.argv) < 2:
        usage()
        sys.exit(2)

templates = []
__engine__ = TemplateEngine()
__config_dir__ = __config_base_file__ = __config_file__ = ""

try:
        __opts__, __args__ = getopt.getopt(sys.argv[1:], "hc:", ["help", "config="])
except getopt.GetoptError:
        usage()
        sys.exit(2) 
  
for opt, arg in __opts__:
        if opt in ("-h", "--help"):
          usage()
          sys.exit(0)
        elif opt in ("-c", "--config"):
          __config_file__ = arg
          __config_base_file__ = os.path.basename(__config_file__)
          __config_dir__ = os.path.dirname(__config_file__)

# change current working directory
if len(__config_dir__) > 0: os.chdir(__config_dir__)
# execute config file if defined
if len(__config_base_file__) > 0: 
    execfile(__config_base_file__)
#use input parameters for the input and output file
if len(__args__) > 1:
    templates = [(__args__[0], __args__[1])]
#use the input parameter for the input file, and remove .pino for the output file
if len(__args__) == 1:
    templates = [(__args__[0], __args__[0].replace(".pino", ""))]
       

for (template, output_file) in templates:
    output = __engine__.Process(open(template).read())
    open(output_file, "w+").write(output)
