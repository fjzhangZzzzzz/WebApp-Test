"""
URL处理方法
"""
import re, time, json, logging, hashlib, base64, asyncio
from www.webcore import get, post
from www.models import User, Comment, Blog, next_id

__author__ = 'fjzhang'

@get('/')
async def index(request):
    users = await User.findAll()
    return{
        '__template__': 'test.html',
        'users': users
    }