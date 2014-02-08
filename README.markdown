# Pino

## Python template preprocessor

Pino is a template preprocessor that is designed to integrate easily with C-like languages(such as C, C++, C#, and Java). To process a file called "myfile.template.c" and output it to "myfile.c" just call:
```
pino.py myfile.template.c myfile.c
```
If your file is called "myfile.pino.c" then you can just call it like this:
```
pino.py myfile.pino.c
```
And pino will remove the ".pino" extension, and output a to a file called "myfile.c".

## Getting Started

The dollar sign($) is used to signal the preprocessor. There are two types of syntaxes, expressions and blocks. A python expression is evaluated by calling:
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

Pino evaluates python expressions in your source code. Thus, when it finds `$()`, it will evaluate whats inside of the parenthesis, and output that to the file. For example, if you type `$("hello")` it will output `hello` without the quotes to the file. If you want to output `"hello"` with quotes you can type `$(quote("hello"))`. Now to process the file just add ".pino" extension to your file. Pino will process the file, and output to the same file name with the extension removed. So a file named "foo.cpp.pino" will be processed and outputted to "foo.cpp".

## Flow control

Flow control can be done using `if` and `for` statements". Here is the syntax for an `if` statement:
```Javascript
$if conditional { output }
```
If the conditional is true then whatever is in the curly braces will be outputted. If it is not true, then nothing will be outputted. The conditional is a python expression. Right now, `else` clauses are not supported. Here is the syntax for the `for` statement:
```Javascript
$for var in sequence { output }
```
Every time the `for` loop is run, it will output what's in the curly braces. The `for` loop is evaluated from a python `for` loop.

## Python config file

If you want to define python variables and functions to be used in the python file, you can create a python file and pass it into pino like this:
```
pino.py --config=myconfig.py myfile.template.c myfile.c
```
Any variables or functions define in "myconfig.py" will be accessible during processing of the "myfile.template.c" file. For example, if we defined a "template.py" file like this:
```Python
class_name = "foo"
number_of_vars = 5
```
Then if the "MyTemplate.pino.h" file was defined like this:
```Javascript
class $(class_name)
{
    $for i in range(number_of_vars)
    {
        int x$(i);
    }
};
```
You can process the template using pino by calling this:
```
pino.py --config=template.py MyTemplate.pino.h
```
Then pino will generate a file called "MyTemplate.h" with this output:
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

## Multiple Files

Instead of specifying input and output files on the command line, the files to be processed can be specified in the python config file instead. This lets you specify multiple files at once. To specify multiple files, just define an list called `templates` that contains a tuple with the template file to be processed and the name of the output file, like this:
```Python
templates = [("MyTemplateHeader.h", "MyHeader.h"), ("MyTemplateSrc.cpp", "MySrc.cpp")]
```
This will process each file in the `templates` list, and any variables defined in this file will be accessible during processing.  So, for example, if you wrote a "template.py" file define like this:
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
To process the files specified by the `templates` list, you must pass in just the config file without any input or output files, like this:
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

