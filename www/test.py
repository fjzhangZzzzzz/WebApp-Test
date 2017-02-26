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

import asyncio

from www.models import User
from www.orm import create_pool, destroy_pool

__author__ = 'fjzhang'

if __name__ == '__main__':
    loop = asyncio.get_event_loop()


    async def test():
        await create_pool(loop=loop, user='root', password='fjzhang', db='webapp_test')
        # u = User(name='Test', email='test@example.com', passwd='1234567890', image='about:blank')
        # await u.save()
        r = User.findAll()
        print(r)
        await destroy_pool()


    loop.run_until_complete(test())
