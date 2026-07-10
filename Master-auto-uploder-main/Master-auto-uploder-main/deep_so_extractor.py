"""
Deep .so file extractor - Extracts actual code logic, methods, constants,
string values, API endpoints, headers, and bytecode disassembly from compiled .so modules.
"""
import sys
import os
import dis
import types
import importlib
import importlib.util
import inspect
import json
import traceback
import io
from collections import defaultdict

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

OUTPUT_FILE = os.path.join(PROJECT_ROOT, "deep_so_analysis.txt")

SO_FILES = [
    ("master.server", "master/server.so"),
    ("master.database", "master/database.so"),
    ("master.utils", "master/utils.so"),
    ("master.helper", "master/helper.so"),
    ("master.logdb", "master/logdb.so"),
    ("master.key", "master/key.so"),
    ("master.buttom", "master/buttom.so"),
    ("constant.buttom", "constant/buttom.so"),
    ("constant.msg", "constant/msg.so"),
    ("modules.appx_master", "modules/appx_master.so"),
    ("modules.appxdata", "modules/appxdata.so"),
    ("modules.manager", "modules/manager.so"),
    ("modules.tasks", "modules/tasks.so"),
    ("modules.scheduler", "modules/scheduler.so"),
    ("modules.retasks", "modules/retasks.so"),
]


def get_string_constants_from_code(code_obj, depth=0):
    """Extract all string constants from a code object recursively."""
    strings = []
    if hasattr(code_obj, 'co_consts'):
        for const in code_obj.co_consts:
            if isinstance(const, str) and len(const) > 1:
                strings.append(const)
            elif isinstance(const, bytes) and len(const) > 1:
                try:
                    strings.append(f"[bytes] {const}")
                except:
                    pass
            elif isinstance(const, types.CodeType):
                strings.extend(get_string_constants_from_code(const, depth + 1))
    return strings


def get_all_names_from_code(code_obj):
    """Extract all names referenced in bytecode."""
    names = {
        "co_names": list(code_obj.co_names) if hasattr(code_obj, 'co_names') else [],
        "co_varnames": list(code_obj.co_varnames) if hasattr(code_obj, 'co_varnames') else [],
        "co_freevars": list(code_obj.co_freevars) if hasattr(code_obj, 'co_freevars') else [],
        "co_cellvars": list(code_obj.co_cellvars) if hasattr(code_obj, 'co_cellvars') else [],
    }
    return names


def disassemble_to_string(code_obj):
    """Disassemble code object to string."""
    output = io.StringIO()
    try:
        dis.dis(code_obj, file=output)
    except:
        pass
    return output.getvalue()


def extract_function_details(func_obj, func_name=""):
    """Extract detailed information from a function."""
    result = {}
    
    # Basic info
    result["name"] = func_name or getattr(func_obj, '__name__', 'unknown')
    result["qualname"] = getattr(func_obj, '__qualname__', '')
    result["is_coroutine"] = inspect.iscoroutinefunction(func_obj)
    
    # Signature
    try:
        sig = inspect.signature(func_obj)
        result["signature"] = str(sig)
        result["parameters"] = {}
        for pname, param in sig.parameters.items():
            pinfo = {"kind": str(param.kind)}
            if param.default != inspect.Parameter.empty:
                try:
                    pinfo["default"] = repr(param.default)
                except:
                    pinfo["default"] = str(type(param.default))
            if param.annotation != inspect.Parameter.empty:
                pinfo["annotation"] = str(param.annotation)
            result["parameters"][pname] = pinfo
    except:
        result["signature"] = "(?)"
    
    # Code object analysis
    if hasattr(func_obj, '__code__'):
        code = func_obj.__code__
        result["filename"] = code.co_filename
        result["firstlineno"] = code.co_firstlineno
        result["argcount"] = code.co_argcount
        result["nlocals"] = code.co_nlocals
        result["stacksize"] = code.co_stacksize
        result["flags"] = code.co_flags
        result["varnames"] = list(code.co_varnames)
        result["names"] = list(code.co_names)
        result["freevars"] = list(code.co_freevars)
        
        # All constants (includes strings, numbers, None, nested code objects)
        consts = []
        for c in code.co_consts:
            if isinstance(c, types.CodeType):
                consts.append(f"<code: {c.co_name}>")
            elif isinstance(c, str):
                consts.append(repr(c) if len(c) < 500 else repr(c[:500]) + "...[TRUNCATED]")
            elif isinstance(c, (int, float, bool, type(None))):
                consts.append(repr(c))
            elif isinstance(c, bytes):
                consts.append(f"b'{c.hex()}'")
            elif isinstance(c, tuple):
                consts.append(repr(c))
            else:
                consts.append(str(type(c)))
        result["constants"] = consts
        
        # String constants only
        result["string_constants"] = [c for c in code.co_consts if isinstance(c, str) and len(c) > 0]
        
        # Number constants
        result["number_constants"] = [c for c in code.co_consts if isinstance(c, (int, float)) and not isinstance(c, bool)]
        
        # Bytecode disassembly
        result["bytecode"] = disassemble_to_string(code)
        
        # Nested function code objects
        nested = []
        for c in code.co_consts:
            if isinstance(c, types.CodeType):
                nested.append({
                    "name": c.co_name,
                    "varnames": list(c.co_varnames),
                    "names": list(c.co_names),
                    "string_constants": [x for x in c.co_consts if isinstance(x, str) and len(x) > 0],
                    "bytecode": disassemble_to_string(c),
                })
        result["nested_functions"] = nested
    
    # Defaults
    if hasattr(func_obj, '__defaults__') and func_obj.__defaults__:
        result["defaults"] = [repr(d) for d in func_obj.__defaults__]
    
    # Closure
    if hasattr(func_obj, '__closure__') and func_obj.__closure__:
        closure_vals = []
        for cell in func_obj.__closure__:
            try:
                closure_vals.append(repr(cell.cell_contents))
            except:
                closure_vals.append("<empty cell>")
        result["closure"] = closure_vals
    
    return result


def extract_class_details(cls_obj, cls_name=""):
    """Extract detailed information from a class."""
    result = {}
    result["name"] = cls_name or cls_obj.__name__
    result["bases"] = [b.__name__ for b in cls_obj.__bases__]
    result["mro"] = [c.__name__ for c in cls_obj.__mro__]
    
    # Class-level attributes
    attrs = {}
    methods = {}
    properties = {}
    
    for name in sorted(dir(cls_obj)):
        if name.startswith('__') and name.endswith('__') and name not in ('__init__', '__call__', '__enter__', '__exit__', '__aenter__', '__aexit__'):
            continue
        
        try:
            obj = getattr(cls_obj, name)
            
            if callable(obj) and not isinstance(obj, type):
                methods[name] = extract_function_details(obj, name)
            elif isinstance(obj, property):
                properties[name] = str(obj)
            elif isinstance(obj, (str, int, float, bool, list, dict, tuple)):
                attrs[name] = repr(obj) if len(repr(obj)) < 1000 else repr(obj)[:1000] + "...[TRUNCATED]"
            else:
                attrs[name] = f"<{type(obj).__name__}>"
        except Exception as e:
            attrs[name] = f"<error: {e}>"
    
    result["attributes"] = attrs
    result["methods"] = methods
    result["properties"] = properties
    
    return result


def analyze_module(module_name, so_path):
    """Deeply analyze a single .so module."""
    result = {"module": module_name, "path": so_path}
    
    full_path = os.path.join(PROJECT_ROOT, so_path)
    if not os.path.exists(full_path):
        result["error"] = "File not found"
        return result
    
    try:
        # Import the module
        spec = importlib.util.spec_from_file_location(module_name, full_path)
        if spec is None:
            result["error"] = "Could not create module spec"
            return result
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        
        # Set up parent packages if needed
        parts = module_name.split(".")
        if len(parts) > 1:
            parent_name = parts[0]
            if parent_name not in sys.modules:
                parent_spec = importlib.util.spec_from_file_location(
                    parent_name,
                    os.path.join(PROJECT_ROOT, parent_name, "__init__.py")
                )
                if parent_spec:
                    parent_module = importlib.util.module_from_spec(parent_spec)
                    sys.modules[parent_name] = parent_module
        
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            result["load_error"] = f"{type(e).__name__}: {e}"
            # Still try to analyze what we loaded
        
        # Get all module members
        functions = {}
        classes = {}
        variables = {}
        all_strings = []
        imports = []
        
        for name in dir(module):
            if name.startswith('_') and name != '__all__':
                continue
            
            try:
                obj = getattr(module, name)
                
                if isinstance(obj, types.FunctionType):
                    functions[name] = extract_function_details(obj, name)
                elif isinstance(obj, type):
                    classes[name] = extract_class_details(obj, name)
                elif isinstance(obj, types.ModuleType):
                    imports.append({"name": name, "module": getattr(obj, '__name__', str(obj))})
                elif isinstance(obj, str):
                    variables[name] = repr(obj) if len(obj) < 2000 else repr(obj[:2000]) + "...[TRUNCATED]"
                elif isinstance(obj, (int, float, bool)):
                    variables[name] = repr(obj)
                elif isinstance(obj, dict):
                    try:
                        variables[name] = json.dumps(obj, indent=2, default=str)[:3000]
                    except:
                        variables[name] = repr(obj)[:3000]
                elif isinstance(obj, (list, tuple)):
                    variables[name] = repr(obj)[:3000]
                else:
                    variables[name] = f"<{type(obj).__name__}> = {repr(obj)[:500]}"
            except Exception as e:
                variables[name] = f"<error accessing: {e}>"
        
        result["functions"] = functions
        result["classes"] = classes
        result["variables"] = variables
        result["imports"] = imports
        
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
    
    return result


def format_output(results):
    """Format analysis results into readable text."""
    output = []
    output.append("=" * 80)
    output.append("DEEP .SO MODULE ANALYSIS - COMPLETE CODE EXTRACTION")
    output.append(f"Total modules analyzed: {len(results)}")
    output.append("=" * 80)
    
    for res in results:
        output.append("")
        output.append("=" * 80)
        output.append(f"MODULE: {res['module']}")
        output.append(f"PATH: {res['path']}")
        output.append("=" * 80)
        
        if "error" in res:
            output.append(f"  ERROR: {res['error']}")
            continue
        
        if "load_error" in res:
            output.append(f"  LOAD WARNING: {res['load_error']}")
        
        # IMPORTS
        if res.get("imports"):
            output.append("")
            output.append("  --- IMPORTS ---")
            for imp in res["imports"]:
                output.append(f"  import {imp['name']}  # from {imp['module']}")
        
        # VARIABLES
        if res.get("variables"):
            output.append("")
            output.append("  --- VARIABLES & CONSTANTS ---")
            for name, val in sorted(res["variables"].items()):
                output.append(f"  {name} = {val}")
        
        # CLASSES
        if res.get("classes"):
            output.append("")
            output.append("  --- CLASSES ---")
            for cls_name, cls_info in res["classes"].items():
                output.append(f"")
                output.append(f"  class {cls_name}({', '.join(cls_info.get('bases', []))}):")
                
                if cls_info.get("attributes"):
                    output.append(f"    # Class Attributes:")
                    for attr_name, attr_val in cls_info["attributes"].items():
                        output.append(f"    {attr_name} = {attr_val}")
                
                if cls_info.get("methods"):
                    output.append(f"    # Methods:")
                    for method_name, method_info in cls_info["methods"].items():
                        is_async = method_info.get("is_coroutine", False)
                        prefix = "async " if is_async else ""
                        sig = method_info.get("signature", "(?)")
                        output.append(f"")
                        output.append(f"    {prefix}def {method_name}{sig}:")
                        output.append(f"      # varnames: {method_info.get('varnames', [])}")
                        output.append(f"      # names used: {method_info.get('names', [])}")
                        
                        if method_info.get("string_constants"):
                            output.append(f"      # String constants in this method:")
                            for s in method_info["string_constants"]:
                                output.append(f"      #   {repr(s)[:200]}")
                        
                        if method_info.get("number_constants"):
                            output.append(f"      # Number constants: {method_info['number_constants']}")
                        
                        if method_info.get("defaults"):
                            output.append(f"      # parameter defaults: {method_info['defaults']}")
                        
                        # BYTECODE
                        if method_info.get("bytecode"):
                            output.append(f"      # --- BYTECODE ---")
                            for line in method_info["bytecode"].split("\n"):
                                if line.strip():
                                    output.append(f"      # {line}")
        
        # FUNCTIONS
        if res.get("functions"):
            output.append("")
            output.append("  --- FUNCTIONS ---")
            for func_name, func_info in res["functions"].items():
                is_async = func_info.get("is_coroutine", False)
                prefix = "async " if is_async else ""
                sig = func_info.get("signature", "(?)")
                
                output.append(f"")
                output.append(f"  {prefix}def {func_name}{sig}:")
                output.append(f"    # varnames: {func_info.get('varnames', [])}")
                output.append(f"    # names used: {func_info.get('names', [])}")
                output.append(f"    # argcount: {func_info.get('argcount', '?')}")
                
                if func_info.get("string_constants"):
                    output.append(f"    # String constants in this function:")
                    for s in func_info["string_constants"]:
                        output.append(f"    #   {repr(s)[:300]}")
                
                if func_info.get("number_constants"):
                    output.append(f"    # Number constants: {func_info['number_constants']}")
                
                if func_info.get("defaults"):
                    output.append(f"    # parameter defaults: {func_info['defaults']}")
                
                if func_info.get("nested_functions"):
                    output.append(f"    # Nested functions:")
                    for nf in func_info["nested_functions"]:
                        output.append(f"    #   {nf['name']}:")
                        output.append(f"    #     varnames: {nf.get('varnames', [])}")
                        output.append(f"    #     names: {nf.get('names', [])}")
                        if nf.get("string_constants"):
                            for ns in nf["string_constants"]:
                                output.append(f"    #     string: {repr(ns)[:200]}")
                
                # BYTECODE 
                if func_info.get("bytecode"):
                    output.append(f"    # --- BYTECODE ---")
                    for line in func_info["bytecode"].split("\n"):
                        if line.strip():
                            output.append(f"    # {line}")
    
    return "\n".join(output)


if __name__ == "__main__":
    print("Starting deep .so analysis...")
    print(f"Python version: {sys.version}")
    print(f"Project root: {PROJECT_ROOT}")
    
    results = []
    for module_name, so_path in SO_FILES:
        print(f"\nAnalyzing: {module_name} ({so_path})...")
        try:
            result = analyze_module(module_name, so_path)
            results.append(result)
            
            func_count = len(result.get("functions", {}))
            class_count = len(result.get("classes", {}))
            var_count = len(result.get("variables", {}))
            print(f"  Found: {func_count} functions, {class_count} classes, {var_count} variables")
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({"module": module_name, "path": so_path, "error": str(e)})
    
    # Write output
    formatted = format_output(results)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(formatted)
    
    print(f"\n\nAnalysis complete! Output written to: {OUTPUT_FILE}")
    print(f"Total size: {len(formatted)} characters")
