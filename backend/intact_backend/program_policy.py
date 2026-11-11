"""A small CAD-program contract, checked in addition to OS isolation."""
import ast
import math
import re

MAX_SOURCE=120000
MAX_PARTS=128
MAX_PARAMETERS=150
MODULES={'build123d','math','numpy','intact_lattice'}
FORBIDDEN_NAMES={'eval','exec','compile','open','input','breakpoint','help','globals','locals','vars','dir','getattr','setattr','delattr','__import__','memoryview'}
FORBIDDEN_ATTRS={'os','sys','ctypes','builtins','subprocess','socket','inspect','system','popen','fork','spawn','exec','eval','compile','open','read','write','read_text','write_text','read_bytes','write_bytes','tofile','fromfile','load','save','savetxt','loadtxt','memmap','import_step','import_stl','import_brep','export_step','export_stl','export_brep','export_gltf','show','show_object'}

class ProgramPolicyError(ValueError):pass

def validate_parameters(value:dict)->dict[str,float]:
    if not isinstance(value,dict) or len(value)>MAX_PARAMETERS:raise ProgramPolicyError(f'Supply at most {MAX_PARAMETERS} numeric parameters.')
    result={}
    for key,number in value.items():
        if not isinstance(key,str) or not re.fullmatch('[a-z][a-z0-9_]{0,47}',key):raise ProgramPolicyError('Parameter names must use lowercase letters, numbers and underscores.')
        if isinstance(number,bool) or not isinstance(number,(int,float)) or not math.isfinite(number) or abs(number)>1e6:raise ProgramPolicyError('Parameters must be finite numbers within ±1,000,000.')
        result[key]=float(number)
    return result

def validate_source(source:str)->str:
    if not isinstance(source,str) or not source.strip() or len(source.encode())>MAX_SOURCE:raise ProgramPolicyError('CAD source must contain 1–120,000 UTF-8 bytes.')
    try:tree=ast.parse(source,filename='design.py')
    except SyntaxError as exc:raise ProgramPolicyError(f'Python syntax error at line {exc.lineno}: {exc.msg}') from exc
    if len(list(ast.walk(tree)))>30000:raise ProgramPolicyError('The CAD program is too large.')
    functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='build']
    if len(functions)!=1 or len(functions[0].args.args)!=1 or functions[0].decorator_list:raise ProgramPolicyError('Define exactly one undecorated build(params) function.')
    for node in ast.walk(tree):
        if isinstance(node,(ast.Import,ast.ImportFrom)):
            names=[n.name.split('.')[0] for n in node.names] if isinstance(node,ast.Import) else [(node.module or '').split('.')[0]]
            if any(n not in MODULES for n in names) or isinstance(node,ast.ImportFrom) and node.level:raise ProgramPolicyError('Only build123d, math, numpy and intact_lattice may be imported.')
            if any(n.name.startswith('_') or n.name.startswith(('export_','import_')) for n in node.names):raise ProgramPolicyError('Private imports are not supported.')
        if isinstance(node,ast.Name) and (node.id.startswith('__') or node.id in FORBIDDEN_NAMES):raise ProgramPolicyError(f'Unsupported name: {node.id}.')
        if isinstance(node,ast.Attribute) and (node.attr.startswith(('_','export_','import_','save','load','dump')) or node.attr.lower() in FORBIDDEN_ATTRS):raise ProgramPolicyError(f'Unsupported attribute: {node.attr}.')
        if isinstance(node,(ast.ClassDef,ast.AsyncFunctionDef,ast.Await,ast.Yield,ast.YieldFrom,ast.Global,ast.Nonlocal)):
            raise ProgramPolicyError('Use ordinary functions and CAD operations; classes, async and global mutation are not supported.')
    return source
