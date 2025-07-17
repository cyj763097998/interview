import logging
from celery import shared_task
from django_redis import get_redis_connection
from .models import Article, UserReadRecord
from .utils.redis_stats import ArticleReadCounter

redis = get_redis_connection()
@shared_task
def sync_redis_to_db(article_id, ip):
    read_stats = ArticleReadCounter.get_read_stats(article_id)
    total_views = int(read_stats['total_views'])
    uv = int(read_stats['uv'])
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
        # 再刷一次缓存保证一致性
        redis.hset(ArticleReadCounter.get_article_key(article_id), 'total_views', total_views)
    except Exception as e:
        # 数据库异常级别并降级处理,更新缓存
        redis.hset(ArticleReadCounter.get_article_key(article_id), 'total_views', total_views)
        logging.warning(f'Article异步更新失败: {str(e)}')

    user_stats = ArticleReadCounter.get_user_read_stats(ip, article_id)
    pv = int(user_stats['pv'])
    # 同步用户阅读记录
    # 先更新数据库
    try:
        UserReadRecord.objects.update_or_create(
            ip=ip,
            article_id=article_id,
            defaults={
                'pv': pv
            }
        )
        # 再刷一次缓存保证一致性
        redis.hset(ArticleReadCounter.get_user_article_key(ip, article_id), 'pv', pv)
    except Exception as e:
        # 数据库异常级别并降级处理,更新缓存
        redis.hset(ArticleReadCounter.get_user_article_key(ip, article_id), 'pv', pv)
        logging.warning(f'UserReadRecord异步更新失败: {str(e)}')

