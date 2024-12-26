from rest_framework import serializers
from .models import Session, Payment, Therapist, AuthModel

class AuthModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthModel
        fields = [
            "id","full_name", "email", "phone_number", "password",
             "role", "date_joined"
        ]
        extra_kwargs = {
            'password': {'write_only': False}
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance

class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

class TherapistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Therapist
        fields = ['id', 'user', 'specialty']


class TherapistInFullSerializer(serializers.ModelSerializer):
    user = AuthModelSerializer()
    class Meta:
        model = Therapist
        fields = ['id', 'user', 'specialty']
        
class SessionInFullSerializer(serializers.ModelSerializer):
    user = AuthModelSerializer()
    therapist = TherapistInFullSerializer()
    class Meta:
        model = Session
        fields = '__all__'

class PaymentInFullSerializer(serializers.ModelSerializer):
    user = AuthModelSerializer()
    session = SessionInFullSerializer()
    class Meta:
        model = Payment
        fields = '__all__'