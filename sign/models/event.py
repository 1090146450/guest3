from django.db import models
from django.forms import forms


class Event(models.Model):
    """
    发布会表
    """
    name = models.CharField(max_length=100)            # 发布会标题
    limit = models.IntegerField()                      # 限制人数
    status = models.BooleanField()                     # 状态
    address = models.CharField(max_length=200)         # 地址
    start_time = models.DateTimeField('events time')   # 发布会时间
    create_time = models.DateTimeField(auto_now=True)  # 创建时间（自动获取当前时间）

    def __str__(self):
        return self.name

