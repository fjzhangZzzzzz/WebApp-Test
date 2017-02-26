"""
URL处理方法
"""
import re, time, json, logging, hashlib, base64, asyncio
from www.webcore import get, post
from www.models import User, Comment, Blog, next_id

__author__ = 'fjzhang'


# @get('/')
# async def index(request):
#     users = await User.findAll()
#     return {
#         '__template__': 'test.html',
#         'users': users
#     }
@get('/')
async def index(request):
    summary = 'fjzhang.'
    blogs = [
        Blog(id='1', name='Test Blog', summary=summary, created_at=time.time()-120),
        Blog(id='2', name='Something New', summary=summary, created_at=time.time()-3600),
        Blog(id='3', name='Learn Swift', summary=summary, created_at=time.time()-7200)
    ]
    return {
        '__template__': 'blogs.html',
        'blogs': blogs
    }