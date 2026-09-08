from django.contrib import admin
from .models import Pet


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = (
        'nome',
        'especie',
        'porte',
        'idade',
        'distancia',
        'vacinado',
        'castrado',
        'disponivel',
    )

    list_filter = (
        'especie',
        'porte',
        'idade',
        'vacinado',
        'castrado',
        'disponivel',
    )

    search_fields = ('nome', 'descricao', 'temperamento')