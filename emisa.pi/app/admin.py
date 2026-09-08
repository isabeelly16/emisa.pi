from django.contrib import admin
from .models import Pet, SolicitacaoAdocao


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

    search_fields = (
        'nome',
        'descricao',
        'temperamento',
    )


@admin.register(SolicitacaoAdocao)
class SolicitacaoAdocaoAdmin(admin.ModelAdmin):

    list_display = (
        'pet',
        'usuario',
        'nome_adotante',
        'email',
        'telefone',
        'status',
        'data_solicitacao',
    )

    list_filter = (
        'status',
        'data_solicitacao',
    )

    search_fields = (
        'nome_adotante',
        'email',
        'telefone',
        'pet__nome',
        'usuario__username',
    )

    readonly_fields = (
        'data_solicitacao',
    )