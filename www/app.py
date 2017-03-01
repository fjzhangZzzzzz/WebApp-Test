_pycharm_edit_ = False

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from aiohttp import web
from jinja2 import Environment, FileSystemLoader

if _pycharm_edit_:
    from www import orm
    from www.webcore import add_routes, add_static
else:
    import orm
    from webcore import add_routes, add_static


logging.basicConfig(level=logging.INFO)


def init_jinja2(app, **kw):
    logging.info('init jinja2...')
    options = dict(
        autoescape=kw.get('autoescape', True),  # XML/HTML自动转义
        block_start_string=kw.get('block_start_string', '{%'),  # 块开始标记符
        block_end_string=kw.get('block_end_string', '%}'),  # 块结束标记符
        variable_start_string=kw.get('variable_start_string', '{{'),  # 变量开始标记符
        variable_end_string=kw.get('variable_end_string', '}}'),  # 变量结束标记符
        comment_start_string=kw.get('comment_start_string', '{#'),  # 注释开始标记符
        comment_end_string=kw.get('comment_end_string', '#}'),  # 注释结束标记符
        auto_reload=kw.get('auto_reload', True)  # 模板修改时自动重新加载
    )
    path = kw.get('path', None)
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    logging.info('set jinja2 templates path: %s' % path)
    env = Environment(loader=FileSystemLoader(path), **options)
    filters = kw.get('filters', None)
    if filters is not None:
        for name, f in filters.items():
            env.filters[name] = f

    app['__templating__'] = env


async def logger_factory(app, handler):
    async def logger(request):
        logging.info('Request: %s %s' % (request.method, request.path))
        return await handler(request)

    return logger


async def data_factory(app, handler):
    """

    :param app:
    :param handler:
    :return:
    """
    async def parse_data(request):
        if request.method == 'POST':
            if request.content_type.startswith('application/json'):
                request.__data__ = await request.json()
                logging.info('request json: %s' % str(request.__data__))
            elif request.content_type.startswith('application/x-www-form-urlencoded'):
                request.__data__ = await request.post()
                logging.info('request form: %s' % str(request.__data__))
        return await handler(request)

    return parse_data


# async def auth_factory(app, handler):
#     async def auth(request):
#         logging.info('check user: %s %s' % (request.method, request.path))
#         request.__user__ = None
#         cookie_str = request.cookie.get(COOKIE_NAME)
#         if cookie_str:
#             user = await cookie2user(cookie_str)
#             if user:
#                 logging.info('set current user: %s' % user.email)
#                 request.__user__ = user
#         if request.path.startswith('manage/') and (request.__user__ is None or not request.__user__.admin):
#             return web.HTTPFound('/signin')
#         return await handler(request)
#     return auth


async def response_factory(app, handler):
    async def reponse(request):
        logging.info('Response handler...')
        r = await handler(request)
        if isinstance(r, web.StreamResponse):
            return r
        if isinstance(r, bytes):
            resp = web.Response(body=r)
            resp.content_type = 'application/octet-stream'
            return resp
        if isinstance(r, str):
            if r.startswith('redirect:'):
                return web.HTTPFound(r[9:])
            resp = web.Response(body=r.encode('utf-8'))
            resp.content_type = 'text/html;charset=utf-8'
            return resp
        if isinstance(r, dict):
            """ 
            handler处理后返回dict对象                
            """
            template = r.get('__template__')
            if template is None:
                """ 
                1. 通过API获取数据，序列化response结果为JSON                
                """
                resp = web.Response(
                    body=json.dumps(r, ensure_ascii=False, default=lambda o: o.__dict__).encode('utf-8'))
                resp.content_type = 'application/json;charset=utf-8'
                return resp
            else:
                """ 
                1. 正常模板网页              
                """
                resp = web.Response(body=app['__templating__'].get_template(template).render(**r).encode('utf-8'))
                resp.content_type = 'text/html;charset=utf-8'
                return resp
        if isinstance(r, int) and 100 <= r <= 600:
            return web.Response(r)
        if isinstance(r, tuple) and len(r) == 2:
            t, m = r
            if isinstance(t, int) and 100 <= t <= 600:
                return web.Response(t, str(m))
        # default:
        resp = web.Response(body=str(r).encode('utf-8'))
        resp.content_type = 'text/plain;charset=utf-8'
        return resp

    return reponse


def datetime_filter(t):
    delta = int(time.time() - t)
    if delta < 60:
        return u'1分钟前'
    if delta < 60 * 60:
        return u'%s分钟前' % (delta // 60)
    if delta < 60 * 60 * 24:
        return u'%s小时前' % (delta // (60 * 60))
    if delta < 60 * 60 * 24 * 7:
        return u'%s天前' % (delta // (60 * 60 * 60))
    dt = datetime.fromtimestamp(t)
    return u'%s年%s月%s日' % (dt.year, dt.month, dt.day)

async def init(loop):
    await orm.create_pool(loop=loop, user='root', password='fjzhang', db='webapp_test')
    app = web.Application(loop=loop, middlewares=[
        logger_factory, response_factory
    ])
    init_jinja2(app, filters=dict(datetime=datetime_filter))
    add_routes(app, 'handlers')
    add_static(app)

    srv = await loop.create_server(app.make_handler(), '127.0.0.1', 9000)
    logging.info('server started at http://127.0.0.1:9000...')
    return srv


loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()
