import logging
from typing import Type, Union

from modelforge.model import Model
from modelforge.storage_backend import StorageBackend

__models__ = set()


def register_model(cls: Type[Model]):
    """
    Include the given model class into the registry.

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
                 backend: StorageBackend=None, **kwargs):
        """
        Initializea new `GenericModel`.

        :param source: UUID, file system path, file object or an URL; None means auto.
        :param dummy: if True, ignore unknown model types.
        :param cache_dir: The directory where to store the downloaded model.
        :param backend: Remote storage backend to use if ``source`` is a UUID or a URL.
        :param kwargs: Everything is passed directly to `Model.__init__`.
        """
        super(GenericModel, self).__init__(**kwargs)
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
