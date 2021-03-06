import datetime
from abc import abstractmethod
from collections import OrderedDict
from contextlib import contextmanager
from typing import Optional, Type, Union, Callable, Dict, List

from django.core.cache import caches, cache as default_cache
from django.core.cache.backends.base import BaseCache
from django.db.models import Model
from django.conf import settings
from rest_framework.serializers import ModelSerializer, Serializer, BaseSerializer, SerializerMetaclass, ListSerializer, LIST_SERIALIZER_KWARGS


def _first_true(iterable, default=False, pred=None):
    """Returns the first true value in the iterable.

    If no true value is found, returns *default*

    If *pred* is not None, returns the first item
    for which pred(item) is true.

    """
    # first_true([a,b,c], x) --> a or b or c or x
    # first_true([a,b], x, f) --> a if f(a) else b if f(b) else x
    return next(filter(pred, iterable), default)


class _CashedSerializerBase:
    _cache: BaseCache = default_cache
    _key_prefix: str = "sercache"
    _context_cache_count = 0
    _context_cache_prefix = None
    _context_cache_keys = set()
    _cache_timeout = 60 * 60 * 24
    _cache_version = None
    model: Model

    def __new__(cls, *args, cache_scope=False, **kwargs):
        # We override this method in order to automagically create
        # `CachedSerializer` classes instead when `many=True` is set.
        if kwargs.pop('many', False):
            return cls.many_init(*args, cache_scope=cache_scope, **kwargs)
        return super().__new__(cls, *args, **kwargs)

    def __init__(self, *args, use_cache: Union[bool, str] = True, cache_scope=False, **kwargs) -> None:
        if isinstance(use_cache, bool):
            use_cache = "true" if use_cache else "false"
        self._use_cache = use_cache
        super().__init__(*args, **kwargs)

    @classmethod
    def many_init(cls, *args, cache_scope=False, **kwargs):
        """
        This method implements the creation of a `ListSerializer` parent
        class when `many=True` is used. You can customize it if you need to
        control which keyword arguments are passed to the parent, and
        which are passed to the child.

        Note that we're over-cautious in passing most arguments to both parent
        and child classes in order to try to cover the general case. If you're
        overriding this method you'll probably want something much simpler, eg:

        @classmethod
        def many_init(cls, *args, **kwargs):
            kwargs['child'] = cls()
            return CustomListSerializer(*args, **kwargs)
        """
        allow_empty = kwargs.pop('allow_empty', None)
        child_serializer = cls(*args, **kwargs)
        list_kwargs = {
            'child': child_serializer,
            'cache_scope': cache_scope
        }
        if allow_empty is not None:
            list_kwargs['allow_empty'] = allow_empty
        list_kwargs.update({
            key: value for key, value in kwargs.items()
            if key in LIST_SERIALIZER_KWARGS + ("cache_scope",)
        })
        meta = getattr(cls, 'Meta', None)
        list_serializer_class = getattr(meta, 'list_serializer_class', CachedListSerializer)
        return list_serializer_class(*args, **list_kwargs)

    def _is_in_scope(self) -> bool:
        return self._context_cache_count > 0

    def _get_do_use_cache(self) -> bool:
        return self._use_cache == "true" or (self._use_cache == "scoped_only" and self._is_in_scope())

    @classmethod
    @abstractmethod
    def _generate_cache_key(cls, instance) -> str:
        pass

    @classmethod
    def _get_cache_key_prefix(cls) -> str:
        if cls._context_cache_count > 0:
            return f"{cls._key_prefix}_{cls._context_cache_prefix}_{cls.__class__.__name__.lower()}"
        else:
            return f"{cls._key_prefix}_{cls.__class__.__name__.lower()}"

    def _cache_add(self, key, value):
        self.get_cache().add(key, value, self._cache_timeout, self._cache_version)
        if self._context_cache_count > 0:
            self._context_cache_keys.add(key)

    @classmethod
    @contextmanager
    def cache_scope(cls):
        if cls._context_cache_count == 0:
            cls._context_cache_prefix = str(datetime.datetime.now().timestamp()).replace(".", "_")
        cls._context_cache_count += 1
        yield
        cls._context_cache_count -= 1
        if cls._context_cache_count == 0 and cls._context_cache_keys:
            cls.get_cache().delete_many(cls._context_cache_keys, cls._cache_version)
            cls._context_cache_keys = set()

    def invalidate_cache(self):
        return self._cache.delete(self._generate_cache_key(self.instance), version=self._cache_version)

    @classmethod
    def get_cache(cls) -> BaseCache:
        if isinstance(cls._cache, str):
            cls._cache = caches[cls._cache]
        return cls._cache


class CachedListSerializer(ListSerializer):

    def __init__(self, *args, cache_scope=False, **kwargs):
        super().__init__(*args, **kwargs)
        self._cache_scope = cache_scope

    def _generate_cache_key(self, instance) -> str:
        return self.child._generate_cache_key(instance)

    def to_representation(self, data):
        if self._cache_scope:
            with self.child.cache_scope():
                return super().to_representation(data)
        else:
            return super().to_representation(data)

    def invalidate_cache(self):
        keys = list(map(self._generate_cache_key, self.instance))
        return self.child._cache.delete_many(keys, self.child._cache_version)


class __CashedRegularSerializer(_CashedSerializerBase):

    @classmethod
    def _generate_cache_key_model_serializer(cls: (Type[ModelSerializer], Type["_CashedSerializerBase"]),
                                             instance) -> str:
        model = getattr(cls.Meta, 'model')
        return f"{cls._get_cache_key_prefix()}_{model._meta.verbose_name}_#{hash(instance)}"

    @classmethod
    def _generate_cache_key(cls, instance) -> str:
        return f"{cls._get_cache_key_prefix()}_#{hash(instance)}"


class __CashedModelSerializer(_CashedSerializerBase):

    @classmethod
    def _get_model(cls) -> Type[Model]:
        return getattr(cls.Meta, 'model')

    @classmethod
    def _generate_cache_key(cls, instance) -> str:
        model = cls._get_model()
        return f"{cls._get_cache_key_prefix()}_{model._meta.verbose_name}_#{hash(instance)}"


def _to_representation_helper(self: _CashedSerializerBase, instance, org_to_representation: Callable):
    if not self._get_do_use_cache():
        return org_to_representation(self, instance)

    key = self._generate_cache_key(instance)
    if key in self._cache:
        return self._cache.get(key)
    rep = org_to_representation(self, instance)
    self._cache_add(key, rep)
    return rep


def _decorate_serializer_class(name: str,
                               bases: List[type],
                               org_to_representation: Callable[[BaseSerializer, Model], OrderedDict],
                               org_update: Callable[[BaseSerializer, Model, Dict], Model],
                               serializer_type: Union[Type[Serializer], Type[ModelSerializer]],
                               cache: Optional[Union[str, BaseCache]] = None,
                               key_prefix: str = "sercache",
                               cache_timeout: int = 60 * 60 * 24,
                               cache_version=None,
                               auto_invalidate=False,
                               dict_=None,
                               ) -> (Type[BaseSerializer], Type[_CashedSerializerBase],):
    cache = cache or settings.CACHELIZER_DEFAULT_CACHE
    if cache is str:
        cache = caches[cache]
    dict_ = dict_ or {}

    extra = {
        **dict_,
        "_cache": cache,
        "_key_prefix": key_prefix,
        "_cache_timeout": cache_timeout,
        cache_version: cache_version,
    }

    if serializer_type == ModelSerializer:
        bases = [__CashedModelSerializer, *bases]
    elif serializer_type == Serializer:
        bases = [__CashedRegularSerializer, *bases]
    else:
        raise ValueError("can only decorate serializer class")

    def _to_representation(self, instance):
        return _to_representation_helper(self, instance, org_to_representation)

    extra["to_representation"] = _to_representation

    if auto_invalidate:
        def _update(self, instance, validated_data):
            self.invalidate_cache(instance)
            return org_update(self, instance, validated_data)

        extra["update"] = _update

    return type(name, (*bases,), extra)


class CashedSerializerMeta(SerializerMetaclass):

    def __new__(mcs, name, bases, dict_: Dict, *args, **kwargs) -> (Type[Serializer], Type[_CashedSerializerBase]):
        cache: Optional[Union[str, BaseCache]] = None
        key_prefix: str = "sercache"
        cache_timeout: int = 60 * 60 * 24
        cache_version = None
        auto_invalidate = False
        to_representation = dict_.pop("to_representation") if "to_representation" in dict_ else \
            _first_true(bases, pred=lambda b: hasattr(b, "to_representation")).to_representation
        update = dict_.pop("update") if "update" in dict_ else \
            _first_true(bases, pred=lambda b: hasattr(b, "update")).update
        if ModelSerializer in bases:
            serializer_type = ModelSerializer
        elif Serializer in bases:
            serializer_type = Serializer
        else:
            raise TypeError("unsupported class")
        return _decorate_serializer_class(name, bases, to_representation, update, cache=cache, key_prefix=key_prefix,
                                          cache_timeout=cache_timeout,
                                          cache_version=cache_version,
                                          auto_invalidate=auto_invalidate, dict_=dict_, serializer_type=serializer_type)


def cached_serializer(cls: Type[Serializer],
                      cache: Optional[Union[str, BaseCache]] = None,
                      key_prefix: str = "sercache",
                      cache_timeout: int = 60 * 60 * 24,
                      cache_version=None,
                      auto_invalidate=False) -> (Type[Serializer], Type[_CashedSerializerBase]):
    """
    decorator to add
    :param cls:
    :param cache:
    :param key_prefix:
    :param cache_timeout:
    :param cache_version:
    :param auto_invalidate:
    :return:
    """
    if issubclass(cls, ModelSerializer):
        serializer_type = ModelSerializer
    elif issubclass(cls, Serializer):
        serializer_type = Serializer
    else:
        raise ValueError("can only decorate serializer class")
    return _decorate_serializer_class(cls.__name__, [cls], cls.to_representation, cls.update,
                                      serializer_type, cache=cache, key_prefix=key_prefix,
                                      cache_timeout=cache_timeout, cache_version=cache_version,
                                      auto_invalidate=auto_invalidate)


class CashedSerializer(__CashedRegularSerializer, Serializer):
    def to_representation(self, instance):
        return _to_representation_helper(self, instance, Serializer.to_representation)


class CashedModelSerializer(__CashedModelSerializer, ModelSerializer):
    def to_representation(self, instance):
        return _to_representation_helper(self, instance, ModelSerializer.to_representation)
