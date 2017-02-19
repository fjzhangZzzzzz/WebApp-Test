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

__author__ = 'fjzhang'

if __name__ == '__main__':
    loop = asyncio.get_event_loop()


    async def test():
        await orm.create_pool(loop=loop, user='root', password='fjzhang', db='webapp_test')
        # u = User(name='Test', email='test@example.com', passwd='1234567890', image='about:blank')
        # await u.save()
        r = User.findAll()
        print(r)
        await orm.destroy_pool()


    # iomysql = AioMysql()
    #
    # async def test():
    #
    #     await iomysql.create_pool(
    #         loop=loop,
    #         user='root',
    #         password='fjzhang',
    #         db='webapp_test'
    #     )


    loop.run_until_complete(test())
