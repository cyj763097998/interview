from django.db import models

class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.CharField()
    total_views = models.IntegerField(default=0)  # 总阅读数
    uv = models.IntegerField(default=0)   # 用户人次

    class Meta:
        verbose_name = '文章阅读统计'
        verbose_name_plural = verbose_name


class UserReadRecord(models.Model):
    ip = models.CharField(max_length=30)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    pv = models.IntegerField(default=0)    # 用户阅读数

    class Meta:
        verbose_name = '用户阅读记录'
        verbose_name_plural = verbose_name