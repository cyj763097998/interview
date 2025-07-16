
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
    def increment_read_count(cls, article_id, ip, tvs, pvs):
        ### 增加阅读计数
        article_key = cls.get_article_key(article_id)

        # 使用管道提高性能
        pipe = redis.pipeline()

        # 总阅读数+1
        total_views, uv = cls.get_read_stats(article_id)
        if total_views is None:
            pipe.hincrby(article_key, 'total_views', tvs)
        else:
            pipe.hincrby(article_key, 'total_views', 1)

        # 用户阅读数
        pv = cls.get_user_read_stats(ip, article_id)
        user_article_key = cls.get_user_article_key(ip, article_id)
        if pv is None:
            pipe.hincrby(user_article_key, 'pv', pvs)
        else:
            pipe.hincrby(user_article_key, 'pv', 1)
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
