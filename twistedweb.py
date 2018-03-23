from twisted.web import server, resource
from twisted.internet import reactor


class MyResource(resource.Resource):
    def render(self, request):
        name = request.args['name'][0]
        return "Hello cheese wagon! %s!\n" % name

reactor.listenTCP(8080, server.Site(MyResource()))
reactor.run()



# from twisted.internet.task import deferLater
# from twisted.web.resource import Resource
# from twisted.web.server import NOT_DONE_YET
# from twisted.internet import reactor

# class DelayedResource(Resource):
#     def _delayedRender(self, request):
#         request.write("<html><body>Sorry to keep you waiting.</body></html>")
#         request.finish()

#     def render_GET(self, request):
#         d = deferLater(reactor, 5, lambda: request)
#         d.addCallback(self._delayedRender)
#         return NOT_DONE_YET

# resource = DelayedResource()



# OR


# def ensure_deferred(f):
#     @functools.wraps(f)
#     def wrapper(*args, **kwargs):
#         result = f(*args, **kwargs)
#         return defer.ensureDeferred(result)
#     return wrapper


# @ensure_deferred
# async def run(connection):
#     channel = await connection.channel()
#     exchange = await channel.exchange_declare(exchange='topic_link', type='topic')
#     queue = await channel.queue_declare(queue='hello', auto_delete=False, exclusive=False)
#     await channel.queue_bind(exchange='topic_link', queue='hello', routing_key='hello.world')
#     await channel.basic_qos(prefetch_count=1)
#     queue_object, consumer_tag = await channel.basic_consume(queue='hello', no_ack=False)
#     l = task.LoopingCall(read, queue_object)
#     l.start(0.01)


# @ensure_deferred
# async def read(queue_object):
#     ch, method, properties, body = await queue_object.get()
#     if body:
#         print(body)
#     await ch.basic_ack(delivery_tag=method.delivery_tag)


# parameters = pika.ConnectionParameters()
# cc = protocol.ClientCreator(reactor, twisted_connection.TwistedProtocolConnection, parameters)
# d = cc.connectTCP('rabbitmq', 5672)
# d.addCallback(lambda protocol: protocol.ready)
# d.addCallback(run)
# reactor.run()