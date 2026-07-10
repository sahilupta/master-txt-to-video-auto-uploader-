"""
Extract ALL strings, function signatures, and constants from Cython .so files
by importing modules and deeply inspecting every attribute.
"""
import sys, os, importlib, importlib.util, types, inspect, ctypes

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

OUTPUT = os.path.join(PROJECT_ROOT, "full_string_extract.txt")

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

def extract_cython_func_info(func, name=""):
    """Extract info from a Cython function."""
    info = {"name": name}
    info["doc"] = getattr(func, '__doc__', None)
    info["qualname"] = getattr(func, '__qualname__', '')
    
    # Get annotations
    try:
        info["annotations"] = getattr(func, '__annotations__', {})
    except:
        info["annotations"] = {}
    
    # Get defaults
    try:
        info["defaults"] = getattr(func, '__defaults__', None)
        if info["defaults"]:
            info["defaults"] = [repr(d) for d in info["defaults"]]
    except:
        info["defaults"] = None
    
    # Get kwdefaults
    try:
        info["kwdefaults"] = getattr(func, '__kwdefaults__', None)
    except:
        info["kwdefaults"] = None
    
    # Check if coroutine
    try:
        info["is_coroutine"] = inspect.iscoroutinefunction(func)
    except:
        info["is_coroutine"] = False
    
    # Signature
    try:
        sig = inspect.signature(func)
        info["signature"] = str(sig)
    except:
        info["signature"] = "(?)"
    
    # Get __code__ if available
    if hasattr(func, '__code__'):
        code = func.__code__
        info["code_info"] = {
            "co_varnames": list(code.co_varnames),
            "co_names": list(code.co_names),
            "co_consts": [],
            "co_filename": code.co_filename,
            "co_firstlineno": code.co_firstlineno,
            "co_argcount": code.co_argcount,
            "co_flags": code.co_flags,
        }
        for c in code.co_consts:
            if isinstance(c, str):
                info["code_info"]["co_consts"].append(repr(c))
            elif isinstance(c, (int, float)):
                info["code_info"]["co_consts"].append(repr(c))
            elif isinstance(c, bytes):
                info["code_info"]["co_consts"].append(f"b'{c[:100].hex()}'")
            elif isinstance(c, tuple):
                info["code_info"]["co_consts"].append(repr(c))
            elif isinstance(c, types.CodeType):
                # Nested code object
                nested_info = {
                    "type": "nested_code",
                    "name": c.co_name,
                    "varnames": list(c.co_varnames),
                    "names": list(c.co_names),
                    "consts": [repr(x) for x in c.co_consts if isinstance(x, (str, int, float)) and x != ''],
                }
                info["code_info"]["co_consts"].append(str(nested_info))
    
    # For Cython functions, try to get wrapped function
    if hasattr(func, '__wrapped__'):
        info["wrapped"] = str(func.__wrapped__)
    
    # Try to get source
    try:
        info["source"] = inspect.getsource(func)
    except:
        info["source"] = None
    
    return info


def extract_module(module_name, so_path):
    """Extract everything from a module."""
    full_path = os.path.join(PROJECT_ROOT, so_path)
    if not os.path.exists(full_path):
        return {"error": f"File not found: {full_path}"}
    
    result = {"module": module_name, "path": so_path}
    
    try:
        # Setup parent package
        parts = module_name.split(".")
        if len(parts) > 1:
            parent = parts[0]
            if parent not in sys.modules:
                init_path = os.path.join(PROJECT_ROOT, parent, "__init__.py")
                if os.path.exists(init_path):
                    pspec = importlib.util.spec_from_file_location(parent, init_path)
                    pmod = importlib.util.module_from_spec(pspec)
                    sys.modules[parent] = pmod
        
        spec = importlib.util.spec_from_file_location(module_name, full_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            result["load_error"] = str(e)
        
        # Extract ALL members
        result["functions"] = {}
        result["classes"] = {}
        result["variables"] = {}
        result["all_strings"] = []
        
        for name in dir(module):
            try:
                obj = getattr(module, name)
                
                # Skip imported standard library items
                if isinstance(obj, types.ModuleType):
                    continue
                if name.startswith('__') and name.endswith('__'):
                    continue
                
                # Check if it's from pyrogram/motor/other library
                obj_module = getattr(obj, '__module__', '')
                if isinstance(obj_module, str) and any(x in obj_module for x in ['pyrogram', 'motor', 'aiohttp', 'httpx', 'PIL', 'Crypto']):
                    if isinstance(obj, type):
                        continue  # Skip imported classes
                
                if callable(obj) and not isinstance(obj, type):
                    result["functions"][name] = extract_cython_func_info(obj, name)
                elif isinstance(obj, type):
                    # Extract class
                    cls_info = {
                        "name": name,
                        "bases": [b.__name__ for b in getattr(obj, '__bases__', [])],
                        "module": getattr(obj, '__module__', ''),
                        "attributes": {},
                        "methods": {},
                    }
                    
                    for attr_name in dir(obj):
                        if attr_name.startswith('__') and attr_name.endswith('__') and attr_name not in ('__init__',):
                            continue
                        try:
                            attr_obj = getattr(obj, attr_name)
                            if callable(attr_obj) and not isinstance(attr_obj, type):
                                cls_info["methods"][attr_name] = extract_cython_func_info(attr_obj, attr_name)
                            elif isinstance(attr_obj, (str, int, float, bool, list, dict, tuple)):
                                cls_info["attributes"][attr_name] = repr(attr_obj)
                        except:
                            pass
                    
                    result["classes"][name] = cls_info
                elif isinstance(obj, str):
                    result["variables"][name] = repr(obj) if len(obj) < 5000 else repr(obj[:5000]) + "..."
                    result["all_strings"].append((name, obj if len(obj) < 5000 else obj[:5000]))
                elif isinstance(obj, (int, float, bool)):
                    result["variables"][name] = repr(obj)
                elif isinstance(obj, dict):
                    result["variables"][name] = repr(obj)[:3000]
                elif isinstance(obj, (list, tuple)):
                    result["variables"][name] = repr(obj)[:3000]
                else:
                    result["variables"][name] = f"<{type(obj).__name__}>"
            except Exception as e:
                result["variables"][name] = f"<error: {e}>"

        # Extract strings from binary
        try:
            with open(full_path, 'rb') as f:
                data = f.read()
            
            # Find all printable ASCII strings >= 4 chars
            import re
            binary_strings = re.findall(b'[\x20-\x7e]{4,}', data)
            # Filter for interesting ones (URLs, format strings, messages)
            interesting = []
            for s in binary_strings:
                decoded = s.decode('ascii', errors='ignore')
                if any(kw in decoded.lower() for kw in [
                    'http', 'api', 'error', 'format', 'batch', 'video', 'pdf', 
                    'channel', 'group', 'topic', 'upload', 'download', 'send',
                    'token', 'login', 'user', 'admin', 'message', 'caption',
                    'thumb', 'file', 'name', 'course', 'schedule', 'time',
                    'mongodb', 'async', 'await', 'return', 'button', 'keyboard',
                    'callback', 'inline', '{}', 'f"', "f'", '<b>', '<i>',
                    'appx', 'class', 'data', 'subject', 'folder', 'content',
                    'encrypt', 'decrypt', 'key', 'aes', 'base64', 'photo',
                    'watermark', 'duration', 'thumbnail', 'ffmpeg', 'yt-dlp',
                    'help', 'start', 'premium', 'paid', 'free',
                    'complete', 'progress', 'status', 'delete', 'update',
                    'recover', 'incomplete', 'daily', 'scheduler',
                ]):
                    interesting.append(decoded)
            
            result["binary_strings"] = interesting[:200]  # Limit
        except Exception as e:
            result["binary_strings_error"] = str(e)
    
    except Exception as e:
        import traceback
        result["error"] = traceback.format_exc()
    
    return result


def format_result(results):
    lines = []
    lines.append("=" * 100)
    lines.append("COMPLETE .SO MODULE STRING & CODE EXTRACTION")
    lines.append("=" * 100)
    
    for r in results:
        lines.append("")
        lines.append("=" * 100)
        lines.append(f"MODULE: {r['module']}")
        lines.append(f"PATH: {r['path']}")
        lines.append("=" * 100)
        
        if "error" in r:
            lines.append(f"  ERROR: {r['error']}")
            continue
        
        if "load_error" in r:
            lines.append(f"  LOAD WARNING: {r['load_error']}")
        
        # Variables
        if r.get("variables"):
            lines.append("")
            lines.append("  ═══ MODULE-LEVEL VARIABLES ═══")
            for name, val in sorted(r["variables"].items()):
                lines.append(f"  {name} = {val}")
        
        # Classes
        if r.get("classes"):
            lines.append("")
            lines.append("  ═══ CLASSES ═══")
            for cls_name, cls_info in r["classes"].items():
                # Skip Config class (shown in every module) and library classes
                if cls_name == 'Config':
                    lines.append(f"  [Config class - same as config.py, skipped]")
                    continue
                if cls_info.get("module", "") and cls_info["module"] not in (r["module"], '__main__'):
                    lib_mod = cls_info.get("module", "")
                    if any(x in lib_mod for x in ['pyrogram', 'motor', 'datetime']):
                        continue
                
                bases = ', '.join(cls_info.get('bases', []))
                lines.append(f"")
                lines.append(f"  class {cls_name}({bases}):  # from module: {cls_info.get('module', '?')}")
                
                if cls_info.get("attributes"):
                    for a, v in cls_info["attributes"].items():
                        lines.append(f"    {a} = {v}")
                
                if cls_info.get("methods"):
                    for m_name, m_info in cls_info["methods"].items():
                        prefix = "async " if m_info.get("is_coroutine") else ""
                        sig = m_info.get("signature", "(?)")
                        lines.append(f"")
                        lines.append(f"    {prefix}def {m_name}{sig}:")
                        
                        if m_info.get("doc"):
                            lines.append(f'      """{m_info["doc"][:500]}"""')
                        
                        if m_info.get("code_info"):
                            ci = m_info["code_info"]
                            lines.append(f"      # varnames: {ci.get('co_varnames', [])}")
                            lines.append(f"      # names: {ci.get('co_names', [])}")
                            if ci.get("co_consts"):
                                lines.append(f"      # constants:")
                                for c in ci["co_consts"]:
                                    lines.append(f"      #   {c}")
                        
                        if m_info.get("source"):
                            lines.append(f"      # === SOURCE CODE ===")
                            for sl in m_info["source"].split("\n"):
                                lines.append(f"      # {sl}")
        
        # Functions
        if r.get("functions"):
            lines.append("")
            lines.append("  ═══ FUNCTIONS ═══")
            for func_name, func_info in r["functions"].items():
                prefix = "async " if func_info.get("is_coroutine") else ""
                sig = func_info.get("signature", "(?)")
                lines.append(f"")
                lines.append(f"  {prefix}def {func_name}{sig}:")
                
                if func_info.get("doc"):
                    lines.append(f'    """{func_info["doc"][:500]}"""')
                
                if func_info.get("code_info"):
                    ci = func_info["code_info"]
                    lines.append(f"    # varnames: {ci.get('co_varnames', [])}")
                    lines.append(f"    # names: {ci.get('co_names', [])}")
                    if ci.get("co_consts"):
                        lines.append(f"    # constants:")
                        for c in ci["co_consts"]:
                            lines.append(f"    #   {c}")
                
                if func_info.get("source"):
                    lines.append(f"    # === SOURCE CODE ===")
                    for sl in func_info["source"].split("\n"):
                        lines.append(f"    # {sl}")
        
        # Binary Strings
        if r.get("binary_strings"):
            lines.append("")
            lines.append("  ═══ EXTRACTED BINARY STRINGS (filtered) ═══")
            for s in r["binary_strings"]:
                lines.append(f"  | {s}")
    
    return "\n".join(lines)


if __name__ == "__main__":
    print("Starting full string extraction...")
    results = []
    for mod_name, so_path in SO_FILES:
        print(f"  Extracting: {mod_name}...")
        r = extract_module(mod_name, so_path)
        results.append(r)
        print(f"    Functions: {len(r.get('functions', {}))}, Classes: {len(r.get('classes', {}))}, Vars: {len(r.get('variables', {}))}")
    
    output = format_result(results)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"\nDone! Output: {OUTPUT} ({len(output)} chars)")
