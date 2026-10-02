from django.contrib import admin

from .models import (
    Pet,
    SolicitacaoAdocao,
    Favorito,
    Mensagem,
    PerfilUsuario,
    AcompanhamentoAdocao,
    AtualizacaoAdocao,
    Notificacao
)


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):

    list_display = (
        'nome',
        'especie',
        'porte',
        'idade',
        'cidade',
        'estado',
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
        'cidade',
        'estado',
        'bairro',
        'cep',
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


@admin.register(AcompanhamentoAdocao)
class AcompanhamentoAdocaoAdmin(admin.ModelAdmin):

    list_display = (
        'solicitacao',
        'ativo',
        'entregue_em',
        'criado_em',
    )

    list_filter = (
        'ativo',
        'entregue_em',
    )


@admin.register(AtualizacaoAdocao)
class AtualizacaoAdocaoAdmin(admin.ModelAdmin):

    list_display = (
        'acompanhamento',
        'data_envio',
    )

    readonly_fields = (
        'data_envio',
    )


@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):

    list_display = (
        'usuario',
        'titulo',
        'lida',
        'data_criacao',
    )

    list_filter = (
        'lida',
        'data_criacao',
    )

    search_fields = (
        'usuario__username',
        'titulo',
        'mensagem',
    )


admin.site.register(Favorito)
admin.site.register(Mensagem)
admin.site.register(PerfilUsuario)