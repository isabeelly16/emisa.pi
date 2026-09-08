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

    nome = models.CharField(max_length=100)

    foto = models.ImageField(
        upload_to='pets/',
        blank=True,
        null=True
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

    distancia = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=0
    )

    vacinado = models.BooleanField(default=False)

    castrado = models.BooleanField(default=False)

    descricao = models.TextField(blank=True)

    temperamento = models.CharField(
        max_length=200,
        blank=True
    )

    disponivel = models.BooleanField(default=True)

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
        related_name='solicitacoes_adocao'
    )

    nome_adotante = models.CharField(max_length=100)
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