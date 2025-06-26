from rest_framework import serializers
from .models import Job

class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = '__all__'

    def validate(self, attrs):
        if not attrs.get('jd_file') and not attrs.get('jd_link'):
            raise serializers.ValidationError(
                'Either jd_file or jd_link must be provided.'
            )
        return attrs
