from fiscales.models import Fiscal
from rest_framework import serializers


class FiscalSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Fiscal
        fields = ('apellido', 'nombres', 'dni',)
