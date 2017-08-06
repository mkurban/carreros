from django.shortcuts import render
from rest_framework import viewsets
from api.serializers import FiscalSerializer
from fiscales.models import Fiscal


class FiscalViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Fiscal.objects.all()
    serializer_class = FiscalSerializer


