from rest_framework import serializers
from goods.models import SKUImage, SKU


class SKUImageSerializer(serializers.ModelSerializer):
    sku_id = serializers.IntegerField(label="SKU商品ID")
    sku = serializers.StringRelatedField(label="SKU商品")

    class Meta:
        model = SKUImage
        exclude = ("create_time", "update_time")


class SKUSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SKU
        fields = ("id", "name")
