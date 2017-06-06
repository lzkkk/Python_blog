




import orm,asyncio
from models import User, Blog, Comment

def test():
	loop = asyncio.get_event_loop()
    yield from orm.create_pool(loop, user='www', password='www', database='python_blog')
    u = User(name='Test', email='test@example.com', passwd='1234567890', image='about:blank')

    yield from u.save()

for x in test():
    pass