from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist


def validate_image_size(value):
    max_size = 2 * 1024 * 1024
    if value.size > max_size:
        raise ValidationError('File size must be less than 2 MB.')


class TimeStampedModel(models.Model):

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_active', '-id']
        abstract = True


class SlugModel(models.Model):
    slug = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ['-id']
        abstract = True

    def save(self, *args, **kwargs):
        if hasattr(self, 'name'):
            self.slug = slugify(self.name)
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.name}'


class SingletonModel(models.Model):

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super(SingletonModel, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        try:
            obj = cls.objects.get(id=1)
        except ObjectDoesNotExist:
            obj = cls.objects.create(id=1)
        return obj
