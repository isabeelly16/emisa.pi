from django.db import models
from django.contrib.auth.models import User


class Pet(models.Model):

    ESPECIES = [
        ('cao', 'Cão'),
        ('gato', 'Gato'),
    ]

    PORTES = [
        ('pequeno', 'Pequeno'),
        ('medio', 'Médio'),
        ('grande', 'Grande'),
    ]

    IDADES = [
        ('filhote', 'Filhote'),
        ('adulto', 'Adulto'),
    ]

    nome = models.CharField(
        max_length=100
    )

    foto = models.ImageField(
        upload_to='pets/',
        blank=True,
        null=True
    )

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='pets',
        null=True,
        blank=True
    )

    cep = models.CharField(
        max_length=9,
        blank=True
    )

    estado = models.CharField(
        max_length=100,
        blank=True
    )

    cidade = models.CharField(
        max_length=100,
        blank=True
    )

    bairro = models.CharField(
        max_length=100,
        blank=True
    )

    rua = models.CharField(
        max_length=200,
        blank=True
    )

    numero = models.CharField(
        max_length=20,
        blank=True
    )

    complemento = models.CharField(
        max_length=100,
        blank=True
    )

    zona_rural = models.BooleanField(
        default=False
    )

    latitude = models.FloatField(
        null=True,
        blank=True
    )

    longitude = models.FloatField(
        null=True,
        blank=True
    )

    especie = models.CharField(
        max_length=10,
        choices=ESPECIES
    )

    porte = models.CharField(
        max_length=10,
        choices=PORTES
    )

    idade = models.CharField(
        max_length=10,
        choices=IDADES
    )

    vacinado = models.BooleanField(
        default=False
    )

    castrado = models.BooleanField(
        default=False
    )

    descricao = models.TextField(
        blank=True
    )

    temperamento = models.CharField(
        max_length=200,
        blank=True
    )

    disponivel = models.BooleanField(
        default=True
    )

    def __str__(self):
        return self.nome


class SolicitacaoAdocao(models.Model):

    STATUS = [
        ('pendente', 'Pendente'),
        ('aprovada', 'Aprovada'),
        ('recusada', 'Recusada'),
    ]

    pet = models.ForeignKey(
        Pet,
        on_delete=models.CASCADE,
        related_name='solicitacoes'
    )

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='solicitacoes_adocao',
        null=True,
        blank=True
    )

    nome_adotante = models.CharField(
        max_length=100
    )

    email = models.EmailField()

    telefone = models.CharField(
        max_length=20
    )

    ja_teve_animais = models.BooleanField(
        default=False
    )

    local_moradia = models.CharField(
        max_length=200
    )

    possui_espaco = models.BooleanField(
        default=False
    )

    todos_concordam = models.BooleanField(
        default=False
    )

    consegue_cuidar = models.BooleanField(
        default=False
    )

    motivo = models.TextField()

    status = models.CharField(
        max_length=10,
        choices=STATUS,
        default='pendente'
    )

    data_solicitacao = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f'{self.nome_adotante} - {self.pet.nome}'


class Favorito(models.Model):

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favoritos'
    )

    pet = models.ForeignKey(
        Pet,
        on_delete=models.CASCADE,
        related_name='favoritado_por'
    )

    data_adicionado = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = ('usuario', 'pet')

    def __str__(self):
        return f'{self.usuario.username} - {self.pet.nome}'


class Mensagem(models.Model):

    remetente = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='mensagens_enviadas'
    )

    destinatario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='mensagens_recebidas'
    )

    mensagem = models.TextField()

    data_envio = models.DateTimeField(
        auto_now_add=True
    )

    lida = models.BooleanField(
        default=False
    )

    def __str__(self):
        return f'{self.remetente.username} → {self.destinatario.username}'


class PerfilUsuario(models.Model):

    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='perfil'
    )

    cep = models.CharField(
        max_length=9,
        blank=True
    )

    estado = models.CharField(
        max_length=100,
        blank=True
    )

    cidade = models.CharField(
        max_length=100,
        blank=True
    )

    bairro = models.CharField(
        max_length=100,
        blank=True
    )

    rua = models.CharField(
        max_length=200,
        blank=True
    )

    numero = models.CharField(
        max_length=20,
        blank=True
    )

    complemento = models.CharField(
        max_length=100,
        blank=True
    )

    zona_rural = models.BooleanField(
        default=False
    )

    latitude = models.FloatField(
        null=True,
        blank=True
    )

    longitude = models.FloatField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f'Perfil de {self.usuario.username}'

class AcompanhamentoAdocao(models.Model):

    solicitacao = models.OneToOneField(
        SolicitacaoAdocao,
        on_delete=models.CASCADE,
        related_name='acompanhamento'
    )

    ativo = models.BooleanField(
        default=True
    )

    entregue_em = models.DateTimeField(
        null=True,
        blank=True
    )

    criado_em = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f'Acompanhamento - {self.solicitacao.pet.nome}'


class AtualizacaoAdocao(models.Model):

    acompanhamento = models.ForeignKey(
        AcompanhamentoAdocao,
        on_delete=models.CASCADE,
        related_name='atualizacoes'
    )

    texto = models.TextField()

    foto = models.ImageField(
        upload_to='pos_adocao/',
        blank=True,
        null=True
    )

    data_envio = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f'Atualização - {self.acompanhamento.solicitacao.pet.nome}'


class Notificacao(models.Model):

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notificacoes'
    )

    titulo = models.CharField(
        max_length=150
    )

    mensagem = models.TextField()

    link = models.CharField(
        max_length=300,
        blank=True
    )

    lida = models.BooleanField(
        default=False
    )

    data_criacao = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f'{self.usuario.username} - {self.titulo}'