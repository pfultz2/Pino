# Pino

## Python template preprocessor

Pino is a template preprocessor that is designed to integrate easily with C-like languages(such as C, C++, C#, and Java). To process a file called "myfile.template.c" and output it to "myfile.c" just call:
```
pino.py myfile.template.c myfile.c
```

## Getting Started

The dollar sign($) is used to signal the preprocessor. There are two types of 
syntaxes, expressions and blocks. A python expression is evaluated by calling:
```Javascript
$("hello")
```
Blocks allow flow control, such as:
```Javascript
$if i is 5
{
    hello
}
```
Here is an example that creates a class that has 5 variables:
```Javascript
class foo
{
    $for i in range(5)
    {
        int x$(i);
    }
};
```
This will output:
```Javascript
class foo
{
        int x0;
        int x1;
        int x2;
        int x3;
        int x4;
};
```

# How it works

## Overview

Pino evaluates python expressions in your source code. Thus, when it finds `$()`, 
it will evaluate whats inside of the parenthesis, and output that to the file. 
For example, if you type `$("hello")` it will output `hello` without the quotes to
the file. If you want to output `"hello"` with quotes you can type 
`$(quote("hello"))`.
Now to process the file just add ".pino" extension to your file. Pino will 
process the file, and output to the same file name with the extension removed.
So a file named "foo.cpp.pino" will be processed and outputted to "foo.cpp".

## Flow control

Flow control can be done using "if" and "for" statements". Here is the syntax 
for an if statement:
```Javascript
$if conditional { output }
```
If the conditional is true then whatever is in the curly braces will be 
outputted. If it is not true, then nothing will be outputted. The conditional is
a python expression. Right now, else clauses are not supported. 
Here is the syntax for the for statement:
```Javascript
$for python-for { output }
```
Every time the for loop is run, it will output what's in the curly braces. The for
loop is evaluated from a python for loop.

## Multiple Files

If you are wanting to process several files in a data driven way, then you can pass a python file(rather than a ".pino" file) where you can define variables and functions that are available in the template file. Then in the python file, just define an list called templates that contains a tuple with the template file to be processed and the name of the output file:
```Python
templates = [("MyTemplateHeader.h", "MyHeader.h"), ("MyTemplateSrc.cpp", "MySrc.cpp")]
```
This will process each file in the templates list, and any variables defined in this file will be accessible during processing.  So, for example, if you wrote a "template.py" file define like this:
```Python
templates = [("MyTemplate.h", "MyHeader.h")]
class_name = "foo"
number_of_vars = 5
```
Then if the "MyTemplate.h" file was defined like this:
```Javascript
class $(class_name)
{
    $for i in range(number_of_vars)
    {
        int x$(i);
    }
};
```
Call pino on the file like this:
```
pino.py --config=template.py
```
Then pino will generate a file called "MyHeader.h" with this output:
```Javascript
class foo
{
        int x0;
        int x1;
        int x2;
        int x3;
        int x4;
};
```

