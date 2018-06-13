import logging
from typing import Type, Union

from modelforge.model import Model
from modelforge.storage_backend import StorageBackend

__models__ = set()


def register_model(cls: Type[Model]):
    """
    Includes the given model class into the registry.
    :param cls: The class of the registered model.
    :return: None
    """
    if not issubclass(cls, Model):
        raise TypeError("model bust be a subclass of Model")
    if issubclass(cls, GenericModel):
        raise TypeError("model must not be a subclass of GenericModel")
    __models__.add(cls)
    return cls


class GenericModel(Model):
    """
    Compatible with any model: loads it in :func:`__init__`.
    """
    def __init__(self, source: Union[str, "Model"]=None, dummy=False, cache_dir: str=None,
                 backend: StorageBackend=None, log_level: int=logging.DEBUG):
        super(GenericModel, self).__init__(log_level=log_level)
        self._models = {m.NAME: m for m in __models__} if not dummy else {}
        self.load(source=source, cache_dir=cache_dir, backend=backend)

    def _load_tree(self, tree):
        model = self._models.get(self.meta["model"])
        if model is None:
            if self._models:
                raise ValueError("Unknown model: %s" % self.meta["model"])
            return
        # we overwrite our class - shady, but works
        self.__class__ = model
        log_level = self._log.level
        self._log = logging.getLogger(self.NAME)
        self._log.setLevel(log_level)
        self._load_tree(tree)
