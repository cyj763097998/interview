import time
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.http import JsonResponse
from django_redis import get_redis_connection
from blog.utils.redis_stats import ArticleReadCounter

from blog.models import Article, UserReadRecord

class BlogView(View):
    def get(self, request, pk):
        article = Article.objects.filter(pk=pk).first()
        if not article:
            return JsonResponse({})

        # 用户ip
        ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))

        ### 数据展示，先从redis缓存查数据，没有在往数据库查
        # 获取阅读统计
        read_stats = ArticleReadCounter.get_read_stats(article.id)
        if read_stats is None:
            total_views = 0
            res = Article.objects.filter(pk=pk).first()
            if res:
                read_stats[total_views] = res.total_views

        # 获取用户文章的阅读统计
        user_stats = ArticleReadCounter.get_user_read_stats(ip, article.id)
        if user_stats is None:
            pv = 0
            res = UserReadRecord.objects.filter(ip=ip).first()
            if res:
                user_stats[pv] = res.pv

        ### 做累加操作，存入redis缓存
        ArticleReadCounter.increment_read_count(article.id, ip)

        # 触发异步任务
        from blog.tasks import sync_redis_to_db
        sync_redis_to_db.delay(article.id, ip)

        ### 数据构造 {article_id:1, 'ip':1,'pv':100 , 'uv':4,'total_view':1000}
        data = {
            'article_id': article.id,
            'ip': ip,
            'pv': user_stats.pv,
            'uv': read_stats.uv,
            'total_views': read_stats.total_views
        }
        return JsonResponse(data)