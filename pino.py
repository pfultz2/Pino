#!/usr/bin/python
#
#    pino.py
#
#    Copyright (C) 2011 Paul Fultz II
#    
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
import string
import sys, os
import getopt

# content => (block | statement | .)*
# statement => $func;
# expression => $(func)
# block => $func { content }

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
        if (lexer.HasNext() and lexer.Next() == '$'):
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
        if (lexer.HasNext() and lexer.Next() == '$'):
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
        if (lexer.HasNext() and lexer.Next() == '$' and lexer.HasNext() and lexer.Next() == '('):
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
        print "                 Then in the python file, just define an list called templates that contains"
        print "                 a tuple with the template file to be processed and"
        print "                 the name of the output file"
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
        opts, args = getopt.getopt(sys.argv[1:], "hc:", ["help", "config="])
except getopt.GetoptError:
        usage()
        sys.exit(2) 
  
for opt, arg in opts:
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
else: # otherwise use the input parameters by order, first input then output
  templates = [(args[0], args[1])]    

for (template, output_file) in templates:
    output = __engine__.Process(open(template).read())
    open(output_file, "w+").write(output)
