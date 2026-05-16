import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0009_userneed_target_profile_nullable'),
    ]

    operations = [
        migrations.CreateModel(
            name='ForumQuestion',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('body', models.TextField()),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='forum_questions', to='content.user')),
                ('offer_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='forum_questions', to='content.offertype')),
            ],
            options={
                'db_table': 'forum_question',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ForumAnswer',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('body', models.TextField()),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='forum_answers', to='content.user')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='content.forumquestion')),
            ],
            options={
                'db_table': 'forum_answer',
                'ordering': ['created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='forumquestion',
            index=models.Index(fields=['author', '-created_at'], name='idx_forum_question_author'),
        ),
        migrations.AddIndex(
            model_name='forumquestion',
            index=models.Index(fields=['offer_type', '-created_at'], name='idx_forum_question_type'),
        ),
        migrations.AddIndex(
            model_name='forumanswer',
            index=models.Index(fields=['question', 'created_at'], name='idx_forum_answer_question'),
        ),
    ]
