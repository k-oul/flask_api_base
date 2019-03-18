from datetime import datetime

from flask_sqlalchemy import SQLAlchemy as _SQLAlchemy, BaseQuery
from sqlalchemy import Column, Integer, SmallInteger
from contextlib import contextmanager

from app.libs.error_code import NotFound


class SQLAlchemy(_SQLAlchemy):
    @contextmanager
    def auto_commit(self):
        try:
            yield
            self.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e


class Query(BaseQuery):
    def filter_by(self, **kwargs):
        if 'status' not in kwargs.keys():
            kwargs['status'] = 1
        return super(Query, self).filter_by(**kwargs)

    def get_or_404(self, ident):
        rv = self.get(ident)
        if not rv:
            raise NotFound()
        return rv

    def first_or_404(self):
        rv = self.first()
        if not rv:
            raise NotFound()
        return rv


db = SQLAlchemy(query_class=Query)


class Base(db.Model):
    __abstract__ = True
    create_time = Column(Integer)
    status = Column(SmallInteger, default=1)

    client_exclude_attrs = []

    def __init__(self):
        self.create_time = int(datetime.now().timestamp())

    def __getitem__(self, item):
        return getattr(self, item)

    @property
    def create_datetime(self):
        if self.create_time:
            return datetime.fromtimestamp(self.create_time)
        else:
            return None

    def set_attrs(self, attrs_dict):
        for key, value in attrs_dict.items():
            if hasattr(self, key) and key != 'id':
                setattr(self, key, value)

    def delete(self):
        self.status = 0

    def keys(self):
        return self.fields

    def hide(self, *keys):
        for key in keys:
            self.fields.remove(key)
        return self

    def append(self, *keys):
        for key in keys:
            self.fields.append(key)
        return self

    def update(self, **kwargs):
        with db.auto_commit():
            for k, v in kwargs.items():
                if k in self.fields:
                    setattr(self, k, v)

    def to_dict(self, view=None, excludes=[], relation_keys=[]):
        """ 以 dict 形式返回 model 数据
            会应用 Model.hash_id_map 和 Model.client_exclude_attrs 中的设置

            @view : str
            要使用的 ModelView 的名称

            @excludes : list[str]
            要忽略的属性, 可以与view同时使用

            @relation_keys : list[str]
            包含的 relation_keys 的列表
            必须传入已经在 Model 中声明过的 relation_key
            接受以下形式:
                'relation_key'
                'relation_key:view_name'

        """

        if view:
            if not self.views or view not in self.views:
                fmt = 'Model "%s" does not have view named "%s"'
                raise KeyError(fmt % (type(self).__name__, view))
            d = self.views[view].render(self)
        else:
            d = dict()
            for column in self.__table__.columns:
                d[column.name] = getattr(self, column.name)

        # 处理去除建
        remove_keys = []
        for key, value in d.items():
            if key in type(self).client_exclude_attrs or key in excludes:
                remove_keys.append(key)
            elif value is None:
                if isinstance(value, int) or isinstance(value, float):
                    d[key] = 0
                elif isinstance(value, bool):
                    d[key] = False
                else:
                    d[key] = ''

        for key in remove_keys:
            del d[key]

        # 把所有datetime类型转换成整形timestamp
        for key, value in d.items():
            if isinstance(value, datetime):
                d[key] = int(value.timestamp())

        # 递归处理 relation_key
        for key in relation_keys:
            if key.startswith('?'):
                key = key[1:]
                optional = True
            else:
                optional = False
            parts = key.split(':')
            key = parts[0]
            view_name = parts[1] if len(parts) == 2 else None
            model = getattr(self, key)
            if isinstance(model, list):
                d[key] = [i.to_dict(view=view_name) for i in model]
            elif isinstance(model, Base):
                d[key] = model.to_dict(view=view_name)
            else:
                if not optional:
                    raise KeyError("can't find relation key %s" % key)
                else:
                    # TODO 可选relation key 为空时如何处理？
                    pass

        return d
