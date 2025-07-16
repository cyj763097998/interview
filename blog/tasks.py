import logging
from celery import shared_task
from django_redis import get_redis_connection
from .models import Article, UserReadRecord


@shared_task
def sync_redis_to_db(article_id, ip):
    redis = get_redis_connection()

    article_key = 'article:read:{article.id}'
    user_article_key = 'user:read:{ip}:article:{article.id}'
    user_article_uv_key = 'user:read:{ip}:article:{article.id}:uv'

    total_views = redis.hget(article_key, 'total_views') or 0
    uv = redis.scard(user_article_uv_key) or 0
    pv = redis.hgetall(user_article_key) or 0

    # 同步总阅读量
    # 更新或创建文章统计
    try:
        Article.objects.update_or_create(
            id=article_id,
            defaults={
                'total_views': total_views,
                'uv': uv
            }
        )
        # 删除缓存保证一致性
        redis.delete('total_views')
    except Exception as e:
        # 更新缓存
        redis.hset(article_key, 'total_views', total_views)
        logging.warning(f'异步更新失败: {str(e)}')

    # 同步用户阅读记录
    # 先更新数据库
    try:
        UserReadRecord.objects.get_or_create(
                ip=ip,
                article_id=article_id,
                defaults={'pv': pv}
            )
        # 删除缓存保证一致性
        redis.delete(pv)
    except Exception as e:
        redis.hincrby(user_article_key, 'pv', pv)
        logging.warning(f'异步更新失败: {str(e)}')
