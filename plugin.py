import importlib
import os
import time
import warnings
from types import ModuleType
from typing import Any, Set, Dict, Optional


class Plugin:
    __slots__ = ('module', 'name', 'usage', 'st_mtime')


    def __init__(self,
                 module: ModuleType,
                 name: Optional[str] = None,
                 usage: Optional[Any] = None,
                 st_mtime: Optional[str] = None):
        self.module = module
        self.name = name
        self.usage = usage
        self.st_mtime = st_mtime


class PluginManager:
    _plugins: Dict[str, Plugin] = {}


    def __init__(self):
        pass


    @classmethod
    def add_plugin(cls, module_path: str, plugin: Plugin) -> None:
        """Register a plugin
        
        Args:
            module_path (str): module path
            plugin (Plugin): Plugin object
        """
        if module_path in cls._plugins:
            warnings.warn(f"Plugin {module_path} already exists")
            return
        cls._plugins[module_path] = plugin


    @classmethod
    def get_plugin(cls, module_path: str) -> Optional[Plugin]:
        """Get plugin object by plugin module path
        
        Args:
            module_path (str): Plugin module path
        
        Returns:
            Optional[Plugin]: Plugin object
        """
        return cls._plugins.get(module_path, None)


    @classmethod
    def remove_plugin(cls, module_path: str) -> bool:
        """Remove a plugin by plugin module path
        
        ** Warning: This function not remove plugin actually! **
        ** Just remove command, nlprocessor and event handlers **

        Args:
            module_path (str): Plugin module path

        Returns:
            bool: Success or not
        """
        plugin = cls.get_plugin(module_path)
        if not plugin:
            warnings.warn(f"Plugin {module_path} not exists")
            return False
        del cls._plugins[module_path]
        return True


def load_plugin(module_path: str) -> Optional[Plugin]:
    """Load a module as a plugin
    
    Args:
        module_path (str): path of module to import
    
    Returns:
        Optional[Plugin]: Plugin object loaded
    """
    try:
        st_mtime = os.stat(module_path.replace('.', '/') + '.py').st_mtime
        file_time = time.strftime("%Y-%m-%d %H-%M-%S", time.localtime(st_mtime))

        module: ModuleType = importlib.import_module(module_path)
        name = getattr(module, '__plugin_name__', None)
        usage = getattr(module, '__plugin_usage__', None)
        plugin = Plugin(module, name, usage, file_time)
        PluginManager.add_plugin(module_path, plugin)
        print(f'Succeeded to import "{module_path}"')
        return plugin
    except Exception as e:
        print(f'Failed to import "{module_path}", error: {e}')
        return None


def reload_plugin(module_path: str) -> Optional[Plugin]:
    try:
        st_mtime = os.stat(module_path.replace('.', '/') + '.py').st_mtime
        file_time = time.strftime("%Y-%m-%d %H-%M-%S", time.localtime(st_mtime))
        old_plugin = PluginManager.get_plugin(module_path)
        result = PluginManager.remove_plugin(module_path)
        if not result:
            return None
        module: ModuleType = importlib.reload(old_plugin.module)
        name = getattr(module, '__plugin_name__', None)
        usage = getattr(module, '__plugin_usage__', None)
        plugin = Plugin(module, name, usage, file_time)
        PluginManager.add_plugin(module_path, plugin)
        print(f'Succeeded to import "{module_path}"')
        return plugin
    except Exception as e:
        print(f'Failed to import "{module_path}", error: {e}')
    return None


def load_plugins(plugin_dir: str = 'plugins', reload: bool = False) -> Set[Plugin]:
    """Find all non-hidden modules or packages in a given directory,
    and import them with the given module prefix.

    Args:
        plugin_dir (str): Plugin directory to search
        reload(bool):Plugin reload
    Returns:
        Set[Plugin]: Set of plugin objects successfully loaded
    """
    count = set()
    plugin_names = []
    for root, dir_list, file_list in os.walk(plugin_dir):
        for file_name in file_list:
            path = os.path.join(root, file_name)
            if os.path.isfile(path) and (file_name.startswith('_') or not file_name.endswith('.py')):
                continue
            if os.path.isdir(path) and (
                    file_name.startswith('_') or not os.path.exists(os.path.join(path, '__init__.py'))):
                continue
            file_path = os.path.join(root, file_name.split('.')[0])
            plugin_name = file_path.replace('\\', '.', -1)
            # 只更新有更新内容的文件
            # st_mtime = os.stat(plugin_name.replace('.', '/') + '.py').st_mtime
            # file_time = time.strftime("%Y-%m-%d %H-%M-%S", time.localtime(st_mtime))
            # old_plugin = PluginManager.get_plugin(plugin_name)
            # if old_plugin and old_plugin.st_mtime == file_time:
            #     continue
            plugin_names.append(plugin_name)

    if reload:
        for i in range(2):
            for module_path in plugin_names:
                result = reload_plugin(module_path)
                if i == 1 and result:
                    count.add(result)
            time.sleep(0.5)
    else:
        for module_path in plugin_names:
            result = load_plugin(module_path)
            if result:
                count.add(result)
    return count
