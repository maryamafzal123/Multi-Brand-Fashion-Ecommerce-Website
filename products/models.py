from django.db import models
from django.utils.text import slugify
from cloudinary_storage.storage import MediaCloudinaryStorage
from cloudinary_storage.storage import RawMediaCloudinaryStorage

from django.core.exceptions import ValidationError

def validate_file_size(value):
    limit = 10 * 1024 * 1024  # 10MB
    if value.size > limit:
        raise ValidationError(f'File too large! Max size is 10MB. Your file is {round(value.size/1024/1024, 1)}MB')
    
class Category(models.Model):
    name       = models.CharField(max_length=100, unique=True)
    slug       = models.SlugField(unique=True, db_index=True)
    image      = models.ImageField(upload_to='categories/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    GENDER_CHOICES = [
        ('women', 'Women'),
        ('girls', 'Girls'),
        ('unisex', 'Unisex'),
    ]

    category    = models.ForeignKey(
        Category, on_delete=models.SET_NULL,
        null=True, related_name='products',
        db_index=True
    )
    name        = models.CharField(max_length=200)
    slug        = models.SlugField(unique=True, db_index=True)
    description = models.TextField()
    price       = models.DecimalField(max_digits=10, decimal_places=2, db_index=True)
    old_price   = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    stock       = models.PositiveIntegerField(default=0)
    age_range   = models.CharField(max_length=20, blank=True, null=True, db_index=True)
    gender      = models.CharField(max_length=10, choices=GENDER_CHOICES, default='women', db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    is_active   = models.BooleanField(default=True, db_index=True)
    created_at  = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active', 'is_featured']),
            models.Index(fields=['category', 'gender', 'age_range']),
            models.Index(fields=['price']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def discount_percent(self):
        if self.old_price and self.old_price > self.price:
            return round((1 - self.price / self.old_price) * 100)
        return 0

    @property
    def in_stock(self):
        return self.stock > 0


class ProductImage(models.Model):
    product    = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        related_name='images', db_index=True
    )
    image = models.FileField(
    upload_to='products/',
    storage=RawMediaCloudinaryStorage(),
    validators=[validate_file_size]
)
    is_primary = models.BooleanField(default=False)
    order      = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']
        indexes = [
            models.Index(fields=['product', 'is_primary']),
        ]

    def save(self, *args, **kwargs):
        if self.is_primary:
            ProductImage.objects.filter(
                product=self.product, is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class ProductVariant(models.Model):
    product     = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        related_name='variants', db_index=True
    )
    size        = models.CharField(max_length=20)
    color       = models.CharField(max_length=50, blank=True)
    stock       = models.PositiveIntegerField(default=0)
    extra_price = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    class Meta:
        indexes = [
            models.Index(fields=['product', 'size', 'color']),
        ]

    def __str__(self):
        return f"{self.product.name} — {self.size} / {self.color}"