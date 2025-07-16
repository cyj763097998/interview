import time
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.http import JsonResponse
from django_redis import get_redis_connection

from .models import Article, UserReadRecord

class BlogView(View):
    def get(self, request, pk):
        article = get_object_or_404(Article, pk=pk)
        if not article:
            return JsonResponse('文章不存在')

        # redis 连接
        redis = get_redis_connection()
        # 用户ip
        ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))
        ### 数据展示，先从redis缓存查数据，没有在往数据库查
        article_key = f'article:read:{article.id}'
        user_article_key = f'user:read:{ip}:article:{article.id}'
        user_article_uv_key = f'user:read:{ip}:article:{article.id}:uv'

        # 总阅读数
        total_views = int(redis.hget(article_key, 'total_views'))
        if total_views is None:
            total_views = Article.objects.get(pk=pk).total_views
        # 用户人次
        uv = int(redis.scard(user_article_uv_key))
        if uv is None:
            uv = Article.objects.get(pk=pk).uv
        # 用户阅读数
        pv = int(redis.hgetall(user_article_key).get(b'pv'))
        if pv is None:
            pv = UserReadRecord.objects.get(pk=pk).pv

        ### 做累加操作，存入redis缓存
        pipe = redis.pipeline()
        # 总阅读数+1
        pipe.hincrby(article_key, 'total_views', 1)
        # 用户阅读记录
        pipe.hincrby(user_article_key, 'pv', 1)
        # 用户人次
        pipe.sadd(user_article_uv_key, ip)
        pipe.execute()

        # 触发异步任务
        # from .tasks import sync_redis_to_db
        # sync_redis_to_db.delay(article.id, ip)

        ### 数据构造 {article_id:1, 'ip':1,'pv':100 , 'uv':4,'total_view':1000}
        data = {
            'article_id': article.id,
            'ip': ip,
            'pv': pv,
            'uv': uv,
            'total_views': total_views
        }
        return JsonResponse(data)