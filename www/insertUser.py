#! /usr/bin/env python



import orm,asyncio
from models import User, Blog, Comment

async def test(loop):
    await orm.create_pool(loop=loop,user='www', password='www', db='python_blog')
    u = User(name='lip', email='wlip@example.com', passwd='0987654321', image='about:blank')
    await u.save()
    await d

loop = asyncio.get_event_loop()
loop.run_until_complete(test(loop))
loop.close()