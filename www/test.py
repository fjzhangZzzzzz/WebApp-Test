"""
code is far away from bugs with the god animal protecting
              ┏┓      ┏┓
            ┏┛┻━━━┛┻┓
            ┃      --      ┃
            ┃  ┳┛  ┗┳  ┃
            ┃      ┻      ┃
            ┗━┓      ┏━┛
                ┃      ┗━━━┓
                ┃  神兽保佑    ┣┓
                ┃　永无BUG！   ┏┛
                ┗┓┓┏━┳┓┏┛
                  ┃┫┫  ┃┫┫
                  ┗┻┛  ┗┻┛
"""
import asyncio, sys
import orm
from models import User, Blog, Comment

@asyncio.coroutine
def test(loop):
    yield from orm.create_pool(loop=loop, user='root', password='fjzhang', db='webapp_test')
    u = User(name='Test', email='fjzhang_@outlook.com', passwd='123456', img='about:blank')
    yield from u.save()
    yield from orm.destroy_pool()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test(loop))
    loop.close()
    if loop.is_closed():
        sys.exit(0)
