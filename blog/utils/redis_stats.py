
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
    def increment_read_count(cls, article_id, ip, total_views, pv, uv_list=[]):
        ### 增加阅读计数
        article_key = cls.get_article_key(article_id)

        # 使用管道提高性能
        pipe = redis.pipeline()

        # 总阅读数+1
        read_stats = cls.get_read_stats(article_id)
        if read_stats['total_views'] is None:
            pipe.hincrby(article_key, 'total_views', total_views)
        else:
            pipe.hincrby(article_key, 'total_views', 1)

        # 用户阅读数
        user_read_stats = cls.get_user_read_stats(ip, article_id)
        user_article_key = cls.get_user_article_key(ip, article_id)
        if user_read_stats is None:
            pipe.hincrby(user_article_key, 'pv', pv)
        else:
            pipe.hincrby(user_article_key, 'pv', 1)
        # 用户人次
        uv_key = f'{article_key}:uv'
        if uv_list:
            for res in uv_list:
                pipe.sadd(uv_key, res['ip'])
        else:
            pipe.sadd(uv_key, ip)

        pipe.execute()

    @classmethod
    def get_read_stats(cls, article_id):
        ### 获取阅读统计
        article_key = cls.get_article_key(article_id)
        uv = f'{article_key}:uv'
        total_views = redis.hget(article_key, 'total_views')
        uv = redis.scard(uv)

        return {
                'total_views': total_views,
                'uv': uv
        }

    @classmethod
    def get_user_read_stats(cls, ip, article_id):
        ### 获取用户文章的阅读统计
        user_article_key = cls.get_user_article_key(ip, article_id)
        data = redis.hgetall(user_article_key)

        if not data:
            return None

        return {'pv': data.get(b'pv', 0)}
