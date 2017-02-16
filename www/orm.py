# -*- coding:utf-8 -*-
__author__ = 'fjzhang'

"""Python下ORM for web设计

建立一个web访问的ORM，每一个web请求被连接之后都要接入数据库进行操作。
在web框架中，采用基于asyncio的aiohttp，这是基于协程的异步模型，
所以整个ORM的框架采用异步操作，采用aiomysql作为数据库的异步IO驱动。

思路分析：
Ⅰ. 首先需要建议一个全局的连接池，使得每一个HTTP请求都能从连接池中取得连接，
    然后接入数据库，这样就不会频繁的打开和关闭数据库

Ⅱ. 封装数据库操作函数（SELECT、INSERT、UPDATE、DELETE等）。
    每一个来自连接池的连接都可以通过生成游标的形式调用数据库操作函数，
    而这些操作函数是对数据库操作语句的封装。

Ⅲ. 封装数据库表中的每一列，定义Field类保存每一列的属性（包括数据类型，列名，是否为主键和默认值）

Ⅳ. 定义每一个数据库表映射类的元类ModelMetaclass，通过元类来控制数据库表映射的基类的生成。
    ModelMetaclass的工作：
    一、读取具体子类(user)的映射信息(也就是User表)。
    二、在当前类中查找所有的类属性(attrs)，如果找到Field属性，
        就将其保存到__mappings__的dict中，
        同时从类属性中删除Field(防止实例属性遮住类的同名属性)。
    三、将数据库表名保存到__table__中

Ⅴ. 定义ORM所有映射的基类：Model# Model类的任意子类可以映射一个数据库表。
    Model类可以看作是对所有数据库表操作的基本定义的映射，Model从dict继承，
    拥有字典的所有功能，同时实现特殊方法__getattr__和__setattr__，能够实现属性操作，
    实现数据库操作的所有方法，并定义为class方法，所有继承自Model都具有数据库操作方法。
"""

import asyncio, logging

import aiomysql

# 打印SQL语句
def log(sql, args=()):
    logging.info('SQL: %s' % sql)



# 创建全局的连接池，每个HTTP请求都能从池中获得数据库连接
@asyncio.coroutine
def create_pool(loop, **kw):
    logging.info('create database connection pool...')
    # 全局变量__pool用于存储整个连接池
    global __pool
    __pool = yield from aiomysql.create_pool(
        # **kw参数可以包含所有连接需要用到的关键字参数
        # 默认本机IP
        host=kw.get('host', 'localhost'),
        port=kw.get('port', 3306),
        user=kw['user'],
        password=kw['password'],
        db=kw['db'],
        charset=kw.get('charset', 'utf-8'),
        autocommit=kw.get('autocommit', True),
        maxsize=kw.get('maxsize', 10), # 默认最大连接数为10
        minsize=kw.get('minsize', 1),
        loop=loop # 接受一个event_loop实例
    )

async def destroy_pool():
    global __pool
    if __pool is not None:
        __pool.close()
        await __pool.wait_closed()

# 封装SQL SELECT语句
async def select(sql, args, size=None):
    log(sql, args)
    global __pool
    async with __pool.get() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            # 执行SQL语句
            # SQL语句的占位符是?，MySQL的占位符是%s
            await cur.execute(sql.replace('?', '%s'), args or ())
            # 根据指定返回的size，返回查询的结果
            if size:
                rs = await cur.fetchmany(size) # 返回size条查询结果
            else:
                rs = await cur.fetchall() # 返回所有查询结果
        logging.info('rows returned: %s' % len(rs))
        return rs

# 封装SQL INSERT，UPDATE，DELETE语句
# 语句操作参数一样，所以定义一个通用的执行函数
# 返回操作影响的行号
async def execute(sql, args, autocommit=True):
    log(sql, args)
    async with __pool.get() as conn:
        if not autocommit:
            await conn.begin()
        try:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                # SQL语句的占位符是?，MySQL的占位符是%s
                await cur.execute(sql.replace('?', '%s'), args)
                affected = cur.rowcount
            if not autocommit:
                await conn.commit()
        except BaseException as e:
            if not autocommit:
                await conn.rollback()
            raise
        return affected

# 根据输入的参数生成占位符列表
async def create_args_string(num):
    L = []
    for n in range(num):
        L.append('?')
    # 以','为分隔符，将列表合成字符串
    return ','.join(L)

# 定义Field类，负责保存（数据库）表的字段名和字段类型
class Field(object):
    # 表的字段包含名字、类型、是否为表的主键和默认值
    def __init__(self, name, column_type, primary_key, default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default
    # 当打印（数据库）表时， 输出（数据库）表的信息：类名，字段类型和名字
    def __str__(self):
        return '<%s, %s, %s>' % (self.__class__.__name__, self.column_type, self.name)

# 定义不同类型的衍生Field
# 表的不同列的字段的类型不同
class StringField(Field):
    def __init__(self, name=None, primary_key=False, default=None, ddl='varchar(100'):
        super().__init__(name, ddl, primary_key, default)


class BooleanField(Field):
    def __init__(self, name=None, default=False):
        super().__init__(name, 'boolean', False, default)


class IntegerField(Field):
    def __init__(self, name=None, primary_key=False, default=0):
        super().__init__(name, 'bigint', primary_key, default)


class FloatField(Field):
    def __init__(self, name=None, primary_key=False, default=0):
        super().__init__(name, 'real', primary_key, default)


class TextField(Field):
    def __init__(self, name=None, default=None):
        super().__init__(name, 'text', False, default)

"""定义Model的元类

所有的元类都继承自type
ModelMetaclass元类定义了所有Model基类的子类实现的操作
ModelMetaclass工作主要是为一个数据库表映射成一个封装的类做准备：
- 读取具体子类（user）的映射信息；
- 创造类的时候，排除对Model类的修改；
- 在当前类中查找所有的类属性（attrs），如果找到Field属性，
  就将其保存到__mappings__的dict中，同时从类属性中删除Field（防止实例属性遮住类的同名属性）；
- 将数据库表名保存到__table__中；
"""
class ModelMetaclass(type):
    # __new__控制__init__的执行，所以在其执行之前
    # cls：代表要__init__的类，此参数在实例化时由Python解释器自动提供
    # bases：代表继承父类的集合
    # attrs：类的方法集合
    def __new__(cls, name, bases, attrs):
        # 排除对Model的修改
        if name=='Model':
            return type.__new__(cls, name, bases, attrs)

        # 获取table名称
        tableName = attrs.get('__table__', None) or name
        logging.info('found model: %s (table: %s)' % (name, tableName))

        # 获取Field和主键名
        mappings = dict()
        fields = []
        primaryKey = None
        for k, v in attrs.items():
            # Field属性
            if isinstance(v, Field):
                # k是类的一个属性，v是这个属性在数据库中对应的Field列表属性
                logging.info('found mapping: %s ==> %s' % (k, v))
                mappings[k] = v

                #找到主键
                if v.primary_key:
                    # 如果此时类实例已存在主键，说明主键重复了
                    if primaryKey:
                        raise StandardError('Duplicate primary for field: %s' % k)
                    # 否则将此列设为列表的主键
                    primaryKey = k
                else:
                    fields.append(k)
        # end for

        if not primaryKey:
            raise StandardError('Primary Key not found.')

        # 从类属性中删除Field属性
        for k in mappings.keys():
            attrs.pop(k)
        # 保存除主键外的属性名为``（运算出字符串）列表形式
        escaped_fields = list(map(lambda f: '`%s`' % f, fields))

        attrs['__mappings__'] = mappings        # 保存属性和列的映射关系
        attrs['__table__'] = tableName          # 保存表名
        attrs['__primary_key__'] = primaryKey   # 主键属性名
        attrs['__fields__'] = fields            # 除主键外的属性名

        # 构造默认的SELECT、INSERT、UPDATE、DELETE语句
        # ``反引号功能同repr()
        attrs['__select__'] = 'select `%s`, %s from `%s`' % (primaryKey, ', '.join(escaped_fields), tableName)
        attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % (tableName, ', '.join(escaped_fields), primaryKey, create_args_string(len(escaped_fields) + 1))
        attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (tableName, ', '.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)), primaryKey)
        attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (tableName, primaryKey)
        return type.__new__(cls, name, bases, attrs)

"""定义ORM所有的映射的基类：Model

Model类的任意子类可以映射一个数据库表
Model类可以看做是对所有数据库表操作的基本定义的映射

基于字典查询形式
Model从dict继承，拥有字典的所有功能，同时实现特殊__getattr__和__setattr__，能够实现属性操作
实现数据库操作的所有方法，定义为class方法，所有继承自Model都具有数据库操作方法
"""
class Model(dict, metaclass=ModelMetaclass):
    """ 数据模型 """
    def __init__(self, **kw):
        super(Model, self).__init__(**kw)
    
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value

    def getValue(self, key):
        return getattr(self, key, None)

    def getValueOrDefault(self, key):
        value = getattr(self, key, None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                logging.debug('using default value for %s: %s' % (key, str(value)))
                setattr(self, key, value)
        return value

    # 类方法有类变量cls传入，从而可以用cls做一些相关的处理。
    # 并且有子类继承时，调用该类方法时，传入的类变量cls是子类，而非父类。
    @classmethod
    async def findAll(cls, where=None, args=None, **kw):
        sql = [cls.__select__]
        if where:
            sql.append('where')
            sql.append(where)
        if args is None:
            args=[]
        orderBy = kw.get('orderBy', None)
        if orderBy:
            sql.append('order by')
            sql.append(orderBy)
        limit = kw.get('limit', None)
        if limit is not None:
            sql.append('limit')
            if isinstance(limit, int):
                sql.append('?')
                args.append(limit)
            elif isinstance(limit, tuple) and len(limit) == 2:
                sql.append('?, ?')
                args.extend(limit)
            else:
                raise ValueError('Invalid limit value: %s' % str(limit))
        rs = await select(' '.join(sql), args)
        return [cls(**r) for r in rs]


    @classmethod
    async def findNumber(cls, selectField, where=None, args=None):
        'find number by select and where'        
        sql =  ['select %s _num_ from `%s`' % (selectField, cls.__table__)]
        if where:
            sql.append('where')
            sql.append(where)
        rs = await select(' '.join(sql), args, 1)
        if len(rs) == 0:
            return None
        return rs[0]['_num_']

    @classmethod
    async def find(cls, pk):
        'find object by primary key.'
        rs = await select('%s where `%s`=?' % (cls.__select__, cls.__primary_key__), [pk], 1)
        if len(rs) == 0:
            return None
        return cls(**rs[0])

    async def save(self):
        args = list(map(self.getValueOrDefault, self.__fields__))
        args.append(self.getValueOrDefault(self.__primary_key__))
        rows = await execute(self.__insert__, args)
        if rows != 1:
            logging.warn('failed to insert record: affected rows: %s' % rows)

    async def update(self):
        args = list(map(self.getValue, self.__fields__))
        args.append(self.getValue(self.__primary_key__))
        rwos = await execute(self.__update__, args)
        if rows != 1:
            logging.warn('failed to update by primary key: affected rows: %s' % rows)

    async def remove(self):
        args = [self.getValue(self.__primary_key__)]
        rows = await execute(self.__delete__, args)
        if rows != 1:
            logging.warn('failed to remove by primary key: affected rows: %s' % rows)