# from . import transaction
# from . import supply
# from . import sales
# from . import product
# from . import pharmacy
# from . import mixins
# from . import facility
# from . import consultation
# from . import conf
# from . import client
# from . import auth
# from . import admission
# from .services import services
# from .services import service_cart
# from .lab import lab
import pkgutil
import importlib

for module in pkgutil.iter_modules(__path__):
    importlib.import_module(f"{__name__}.{module.name}")

