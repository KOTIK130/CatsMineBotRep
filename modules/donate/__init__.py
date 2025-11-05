import importlib
import pkgutil
from aiogram import Dispatcher

def donate_modules(dp: Dispatcher):
    for _, module_name, _ in pkgutil.iter_modules(__path__):
        module = importlib.import_module(f"{__name__}.{module_name}")
        
        if hasattr(module, "router"):
            dp.include_router(module.router)
        elif hasattr(module, "register_handlers"):
            module.register_handlers(dp)
