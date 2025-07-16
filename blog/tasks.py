import logging
from celery import shared_task
from django_redis import get_redis_connection
from .models import Article, UserReadRecord
from .utils.redis_stats import ArticleReadCounter

redis = get_redis_connection()
@shared_task
def sync_redis_to_db(article_id):
    read_stats = ArticleReadCounter.get_read_stats(article_id)
    # 同步总阅读量
    # 更新或创建文章统计
    try:
        Article.objects.update_or_create(
            id=article_id,
            defaults={
                'total_views': read_stats['total_views'],
                'uv': read_stats['uv']
            }
        )
        # 删除缓存保证一致性
        redis.delete('total_views')
    except Exception as e:
        # 数据库异常级别并降级处理,更新缓存
        redis.hset(ArticleReadCounter.get_article_key, 'total_views', read_stats['total_views'])
        logging.warning(f'异步更新失败: {str(e)}')

@shared_task
def sync_redis_to_db_ip(article_id, ip):
    user_stats = ArticleReadCounter.get_user_read_stats(ip, article_id)
    # 同步用户阅读记录
    # 先更新数据库
    try:
        UserReadRecord.objects.update_or_create(
                ip=ip,
                article_id=article_id,
                defaults={
                    'pv': user_stats['pv']
                }
        )
        # 删除缓存保证一致性
        redis.delete(user_stats['pv'])
    except Exception as e:
        # 数据库异常级别并降级处理,更新缓存
        redis.hincrby(ArticleReadCounter.get_user_article_key, 'pv', user_stats['pv'])
        logging.warning(f'异步更新失败: {str(e)}')
