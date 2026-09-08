from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import Pet, SolicitacaoAdocao, Favorito, Mensagem


def login_view(request):
    if request.user.is_authenticated:
        return redirect('explorar')

    if request.method == 'POST':
        email = request.POST.get('email')
        senha = request.POST.get('senha')

        usuario = authenticate(
            request,
            username=email,
            password=senha
        )

        if usuario is not None:
            login(request, usuario)
            return redirect('explorar')

        messages.error(request, 'E-mail ou senha incorretos.')

    return render(request, 'login.html')


@login_required
def explorar(request):
    pets = Pet.objects.filter(disponivel=True)

    favoritos_ids = Favorito.objects.filter(
        usuario=request.user
    ).values_list('pet_id', flat=True)

    return render(request, 'explorar.html', {
        'pets': pets,
        'favoritos_ids': favoritos_ids
    })


def logout_view(request):
    logout(request)
    return redirect('login')


def cadastro_view(request):
    if request.user.is_authenticated:
        return redirect('explorar')

    if request.method == 'POST':
        nome = request.POST.get('nome')
        email = request.POST.get('email')
        telefone = request.POST.get('telefone')
        senha = request.POST.get('senha')
        confirmar_senha = request.POST.get('confirmar_senha')

        if senha != confirmar_senha:
            messages.error(request, 'As senhas não são iguais.')
            return render(request, 'cadastro.html')

        if User.objects.filter(username=email).exists():
            messages.error(request, 'Este e-mail já está cadastrado.')
            return render(request, 'cadastro.html')

        usuario = User.objects.create_user(
            username=email,
            email=email,
            password=senha,
            first_name=nome
        )

        login(request, usuario)

        return redirect('explorar')

    return render(request, 'cadastro.html')


@login_required
def perfil_pet(request, pet_id):
    pet = Pet.objects.get(id=pet_id)

    favorito = Favorito.objects.filter(
        usuario=request.user,
        pet=pet
    ).exists()

    return render(request, 'perfil_pet.html', {
        'pet': pet,
        'favorito': favorito
    })


@login_required
def solicitar_adocao(request, pet_id):
    pet = Pet.objects.get(id=pet_id)

    if request.method == 'POST':
        SolicitacaoAdocao.objects.create(
            pet=pet,
            usuario=request.user,
            nome_adotante=request.POST.get('nome_adotante'),
            email=request.POST.get('email'),
            telefone=request.POST.get('telefone'),
            ja_teve_animais=request.POST.get('ja_teve_animais') == 'sim',
            local_moradia=request.POST.get('local_moradia'),
            possui_espaco=request.POST.get('possui_espaco') == 'sim',
            todos_concordam=request.POST.get('todos_concordam') == 'sim',
            consegue_cuidar=request.POST.get('consegue_cuidar') == 'sim',
            motivo=request.POST.get('motivo'),
        )

        messages.success(
            request,
            f'Sua solicitação para adotar {pet.nome} foi enviada!'
        )

        return redirect('perfil_pet', pet_id=pet.id)

    return render(request, 'adocao.html', {
        'pet': pet
    })


@login_required
def minhas_solicitacoes(request):
    solicitacoes = SolicitacaoAdocao.objects.filter(
        usuario=request.user
    ).select_related('pet').order_by('-data_solicitacao')

    return render(request, 'minhas_solicitacoes.html', {
        'solicitacoes': solicitacoes
    })


@login_required
def perfil_usuario(request):
    return render(request, 'perfil_usuario.html', {
        'usuario': request.user
    })


@login_required
def favoritar_pet(request, pet_id):
    pet = Pet.objects.get(id=pet_id)

    favorito, criado = Favorito.objects.get_or_create(
        usuario=request.user,
        pet=pet
    )

    if not criado:
        favorito.delete()

    return redirect(
        request.META.get('HTTP_REFERER', 'explorar')
    )


@login_required
def favoritos(request):
    favoritos = Favorito.objects.filter(
        usuario=request.user
    ).select_related('pet').order_by('-data_adicionado')

    return render(request, 'favoritos.html', {
        'favoritos': favoritos
    })


@login_required
def mensagens(request):
    mensagens_recebidas = Mensagem.objects.filter(
        destinatario=request.user
    ).select_related('remetente').order_by('-data_envio')

    mensagens_enviadas = Mensagem.objects.filter(
        remetente=request.user
    ).select_related('destinatario').order_by('-data_envio')

    return render(request, 'mensagens.html', {
        'mensagens_recebidas': mensagens_recebidas,
        'mensagens_enviadas': mensagens_enviadas
    })


@login_required
def enviar_mensagem(request):
    if request.method == 'POST':
        destinatario_id = request.POST.get('destinatario')
        texto = request.POST.get('mensagem')

        destinatario = User.objects.get(id=destinatario_id)

        if texto:
            Mensagem.objects.create(
                remetente=request.user,
                destinatario=destinatario,
                mensagem=texto
            )

        return redirect('mensagens')

    usuarios = User.objects.exclude(
        id=request.user.id
    )

    return render(request, 'enviar_mensagem.html', {
        'usuarios': usuarios
    })
@login_required
def conversa(request, usuario_id):

    outro_usuario = User.objects.get(id=usuario_id)

    mensagens_conversa = Mensagem.objects.filter(
        remetente__in=[request.user, outro_usuario],
        destinatario__in=[request.user, outro_usuario]
    ).order_by('data_envio')

    Mensagem.objects.filter(
        remetente=outro_usuario,
        destinatario=request.user,
        lida=False
    ).update(lida=True)

    return render(request, 'conversa.html', {
        'outro_usuario': outro_usuario,
        'mensagens': mensagens_conversa
    })