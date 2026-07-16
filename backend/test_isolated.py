import sys
import os

sys.path.insert(0, r"C:\Users\Administrator\Desktop\天行建筑-全流程系统\backend")

print('=' * 60)
print('Isolated Test')
print('=' * 60)

# Clear all modules
for mod_name in list(sys.modules.keys()):
    if mod_name.startswith('app'):
        del sys.modules[mod_name]

# Import database
print('\n[Step 1] Import database...')
from app.core import database as db_mod
print('  db_mod.Base type:', type(db_mod.Base))
print('  db_mod.Base.metadata.tables:', list(db_mod.Base.metadata.tables.keys()))
print('  id(db_mod.Base):', id(db_mod.Base))

# Try to import models
print('\n[Step 2] Import models...')
try:
    from app.models import Project, Department, User
    print('  Success!')
    print('  db_mod.Base.metadata.tables:', list(db_mod.Base.metadata.tables.keys()))
except Exception as e:
    print('  Failed:', type(e).__name__, str(e)[:200])
    
    # Check Base state
    print('\n  Detailed diagnostics:')
    print('  len(db_mod.Base.metadata.tables):', len(db_mod.Base.metadata.tables))
    
    # Check all Base classes in sys.modules
    print('  Checking all Base classes in sys.modules:')
    for mod_name in sorted(sys.modules.keys()):
        if mod_name.startswith('app') and hasattr(sys.modules[mod_name], 'Base'):
            b = getattr(sys.modules[mod_name], 'Base')
            if hasattr(b, 'metadata'):
                print(f'    {mod_name}: Base id={id(b)}, tables={len(b.metadata.tables)}')
    
    # Check registry
    from sqlalchemy.orm import registry
    reg = registry()
    print('\n  Registry info:')
    print('    global registry id:', id(reg))
    print('    Base.registry id:', id(db_mod.Base.registry))
    print('    Base.registry is reg:', db_mod.Base.registry is reg)
    print('    len(reg.mappers):', len(list(reg.mappers)))
    print('    len(Base.registry.mappers):', len(list(db_mod.Base.registry.mappers)))
