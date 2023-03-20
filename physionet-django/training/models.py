from django.db import models

from project.modelcomponents.fields import SafeHTMLField


class OnPlatformTraining(models.Model):
    training_type = models.ForeignKey('user.TrainingType',
                                      on_delete=models.CASCADE, related_name='op_trainings')
    version = models.FloatField(default=1.0)

    class Meta:
        default_permissions = ('change',)
        unique_together = ('training_type', 'version')


class Quiz(models.Model):
    question = SafeHTMLField()
    training = models.ForeignKey('training.OnPlatformTraining',
                                 on_delete=models.CASCADE, related_name='quizzes')
    order = models.PositiveIntegerField()


class ContentBlock(models.Model):
    training = models.ForeignKey('training.OnPlatformTraining',
                                 on_delete=models.CASCADE, related_name='contents')
    body = SafeHTMLField()
    order = models.PositiveIntegerField()


class QuizChoice(models.Model):
    quiz = models.ForeignKey('training.Quiz',
                             on_delete=models.CASCADE, related_name='choices')
    body = models.TextField()
    is_correct = models.BooleanField('Correct Choice?', default=False)