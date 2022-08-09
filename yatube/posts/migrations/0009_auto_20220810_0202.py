# Generated by Django 2.2.16 on 2022-08-09 23:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0008_follow'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='pub_date',
            field=models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Дата публикации'),
        ),
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.UniqueConstraint(fields=('user', 'author'), name='unique_follow'),
        ),
    ]