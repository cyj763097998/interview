
from django_redis import get_redis_connection

# redis 连接
redis = get_redis_connection()

class ArticleReadCounter:
    ### 文章阅读统计Redis操作

    @staticmethod
    def get_article_key(article_id):
        return f'article:read:{article_id}'

    @staticmethod
    def get_user_article_key(ip, article_id):
        return f'user:read:{ip}:article:{article_id}'

    @classmethod
    def increment_read_count(cls, article_id, ip, total_views=0, pv=0):
        ### 增加阅读计数
        article_key = cls.get_article_key(article_id)

        # 使用管道提高性能
        pipe = redis.pipeline()

        # 总阅读数+1
        pipe.hincrby(article_key, 'total_views', total_views)

        # 用户阅读数
        user_article_key = cls.get_user_article_key(ip, article_id)
        pipe.hincrby(user_article_key, 'pv', pv)

        # 用户人次
        uv = f'{article_key}:uv'
        pipe.sadd(uv, ip)

        pipe.execute()

    @classmethod
    def get_read_stats(cls, article_id):
        ### 获取阅读统计
        article_key = cls.get_article_key(article_id)
        uv = f'{article_key}:uv'
        total_views = redis.hget(article_key, 'total_views')
        uv = redis.scard(uv)

        return total_views, uv

    @classmethod
    def get_user_read_stats(cls, ip, article_id):
        ### 获取用户文章的阅读统计
        user_article_key = cls.get_user_article_key(ip, article_id)
        data = redis.hgetall(user_article_key)

        if not data:
            return None

        return data.get(b'pv', 0)
