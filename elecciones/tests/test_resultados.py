import pytest
from django.db.models import Sum
from django.urls import reverse
from elecciones.models import Eleccion, Mesa
from elecciones.views import ResultadosOficialesEleccion
from .factories import EleccionFactory, SeccionFactory, CircuitoFactory, MesaFactory, FiscalGeneralFactory




@pytest.fixture(scope='module')
def carta_marina(db):
    """
    2 secciones con 2 circuitos y 2 mesas por circuito
    """
    s1, s2 = SeccionFactory.create_batch(2)
    c1, c2 = CircuitoFactory.create_batch(2, seccion=s1)
    c3, c4 = CircuitoFactory.create_batch(2, seccion=s2)
    return (MesaFactory(numero=1, lugar_votacion__circuito=c1, electores=100),
            MesaFactory(numero=2, lugar_votacion__circuito=c1, electores=100),
            MesaFactory(numero=3, lugar_votacion__circuito=c2, electores=120),
            MesaFactory(numero=4, lugar_votacion__circuito=c2, electores=120),
            MesaFactory(numero=5, lugar_votacion__circuito=c3, electores=90),
            MesaFactory(numero=6, lugar_votacion__circuito=c3, electores=90),
            MesaFactory(numero=7, lugar_votacion__circuito=c4, electores=90),
            MesaFactory(numero=8, lugar_votacion__circuito=c4, electores=90))


@pytest.fixture(scope='module')
def fiscal_staff(admin_user):
    return FiscalGeneralFactory(user=admin_user)


@pytest.fixture(scope='module')
def url_resultados(db):
    eleccion = EleccionFactory().actual()
    return reverse('resultados-eleccion', args=[eleccion.id])


def test_total_electores_en_eleccion(carta_marina):
    # la sumatoria de todas las mesas de la eleccion
    # nota: el factory de mesa indirectamente crea la eleccion con id=3 que es actual()
    assert Eleccion.actual().electores == 880




def test_electores_sin_filtro(rf, carta_marina, url_resultados, fiscal_staff):
    request = rf.get(url_resultados)
    response = ResultadosOficialesEleccion.as_view()(request)
    assert '<td title="Electores">880 </td>'


def test_electores_filtro_mesa(rf, carta_marina, url_resultados, fiscal_staff):
    request = rf.get(url_resultados)
    response = ResultadosOficialesEleccion.as_view()(request)
    assert '<td title="Electores">880 </td>'