from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Pet, SolicitacaoAdocao

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


def explorar(request):
    pets = Pet.objects.filter(disponivel=True)

    return render(request, 'explorar.html', {
        'pets': pets
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
def perfil_pet(request, pet_id):
    pet = Pet.objects.get(id=pet_id)

    return render(request, 'perfil_pet.html', {
        'pet': pet
    })
def solicitar_adocao(request, pet_id):

    pet = Pet.objects.get(id=pet_id)

    if request.method == 'POST':

        SolicitacaoAdocao.objects.create(
            pet=pet,
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
            f'Sua solicitação para adotar {pet.nome} foi enviada! 💗'
        )

        return redirect('perfil_pet', pet_id=pet.id)

    return render(request, 'adocao.html', {
        'pet': pet
    })