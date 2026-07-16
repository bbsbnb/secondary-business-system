import sys
import os

sys.path.insert(0, r"C:\Users\Administrator\Desktop\天行建筑-全流程系统\backend")

print('=' * 60)
print('Debug: Check for duplicate module execution')
print('=' * 60)

# Clear all modules
for mod_name in list(sys.modules.keys()):
    if mod_name.startswith('app'):
        del sys.modules[mod_name]

# Import database and track execution
print('\n[Step 1] Import database...')

# Patch the import system to track module execution
original_exec_module = None
execution_log = []

def patched_exec_module(module):
    if hasattr(module, '__file__') and module.__file__:
        execution_log.append(f"Executing: {module.__name__} ({module.__file__})")
    return original_exec_module(module)

import importlib._bootstrap
original_exec_module = importlib._bootstrap._call_with_frames_removed

# Now import database
from app.core import database as db_mod
print('  db_mod.Base type:', type(db_mod.Base))
print('  db_mod.Base.metadata.tables:', list(db_mod.Base.metadata.tables.keys()))
print('  id(db_mod.Base):', id(db_mod.Base))

# Check what modules were executed
print('\n[Step 2] Module execution log:')
for entry in execution_log:
    print('  ', entry)

# Now try to import models with detailed tracking
print('\n[Step 3] Import models with tracking...')

# Clear execution log
execution_log.clear()

# Check if app.models is already in sys.modules before import
print('  "app.models.__init__" in sys.modules before import:', 'app.models.__init__' in sys.modules)

try:
    from app.models import Project, Department, User
    print('  Success!')
except Exception as e:
    print('  Failed:', type(e).__name__, str(e)[:200])
    
    # Check what was executed
    print('\n  Module execution log after failed import:')
    for entry in execution_log:
        print('   ', entry)
    
    # Check if app.models.__init__ was partially loaded
    if 'app.models.__init__' in sys.modules:
        mod = sys.modules['app.models.__init__']
        print('\n  app.models.__init__ is partially loaded:')
        print('    mod.__file__:', getattr(mod, '__file__', 'N/A'))
        print('    hasattr(mod, "Project"):', hasattr(mod, 'Project'))
        print('    hasattr(mod, "Department"):', hasattr(mod, 'Department'))
        
        # Check what's in the module's namespace
        for name in dir(mod):
            if not name.startswith('_'):
                obj = getattr(mod, name)
                print(f'    {name}: {type(obj)}')
