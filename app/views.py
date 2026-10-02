from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from geopy.geocoders import Nominatim
from geopy.distance import geodesic

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


def obter_coordenadas(objeto):
    partes = []

    if getattr(objeto, 'zona_rural', False):
        partes.append('Zona Rural')

    rua = getattr(objeto, 'rua', '')
    numero = getattr(objeto, 'numero', '')

    if rua:
        if numero:
            partes.append(f'{rua}, {numero}')
        else:
            partes.append(rua)

    bairro = getattr(objeto, 'bairro', '')

    if bairro:
        partes.append(bairro)

    complemento = getattr(objeto, 'complemento', '')

    if complemento:
        partes.append(complemento)

    cidade = getattr(objeto, 'cidade', '')
    estado = getattr(objeto, 'estado', '')
    cep = getattr(objeto, 'cep', '')

    if cidade:
        partes.append(cidade)

    if estado:
        partes.append(estado)

    if cep:
        partes.append(cep)

    partes.append('Brasil')

    endereco_completo = ', '.join(partes)

    try:
        geolocator = Nominatim(
            user_agent='emisa_adocao'
        )

        localizacao = geolocator.geocode(
            endereco_completo,
            timeout=10
        )

        if not localizacao and cidade and estado:
            localizacao = geolocator.geocode(
                f'{cidade}, {estado}, Brasil',
                timeout=10
            )

        if localizacao:
            return (
                localizacao.latitude,
                localizacao.longitude
            )

    except Exception:
        pass

    return None


def calcular_distancia_km(
    latitude1,
    longitude1,
    latitude2,
    longitude2
):
    if (
        latitude1 is None
        or longitude1 is None
        or latitude2 is None
        or longitude2 is None
    ):
        return None

    distancia = geodesic(
        (latitude1, longitude1),
        (latitude2, longitude2)
    ).km

    return round(
        distancia,
        1
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect(
            'explorar'
        )

    if request.method == 'POST':
        email = request.POST.get(
            'email',
            ''
        ).strip()

        senha = request.POST.get(
            'senha',
            ''
        )

        usuario = authenticate(
            request,
            username=email,
            password=senha
        )

        if usuario is not None:
            login(
                request,
                usuario
            )

            return redirect(
                'explorar'
            )

        messages.error(
            request,
            'E-mail ou senha incorretos.'
        )

    return render(
        request,
        'login.html'
    )


def logout_view(request):
    logout(request)

    return redirect(
        'login'
    )


def cadastro_view(request):
    if request.user.is_authenticated:
        return redirect(
            'explorar'
        )

    if request.method == 'POST':
        nome = request.POST.get(
            'nome',
            ''
        ).strip()

        email = request.POST.get(
            'email',
            ''
        ).strip()

        senha = request.POST.get(
            'senha',
            ''
        )

        confirmar_senha = request.POST.get(
            'confirmar_senha',
            ''
        )

        if senha != confirmar_senha:
            messages.error(
                request,
                'As senhas não são iguais.'
            )

            return render(
                request,
                'cadastro.html'
            )

        if not nome:
            messages.error(
                request,
                'Informe seu nome.'
            )

            return render(
                request,
                'cadastro.html'
            )

        if not email:
            messages.error(
                request,
                'Informe seu e-mail.'
            )

            return render(
                request,
                'cadastro.html'
            )

        if User.objects.filter(
            username=email
        ).exists():
            messages.error(
                request,
                'Este e-mail já está cadastrado.'
            )

            return render(
                request,
                'cadastro.html'
            )

        usuario = User.objects.create_user(
            username=email,
            email=email,
            password=senha,
            first_name=nome
        )

        login(
            request,
            usuario
        )

        return redirect(
            'explorar'
        )

    return render(
        request,
        'cadastro.html'
    )


@login_required
def explorar(request):
    pets = Pet.objects.filter(
        disponivel=True
    )

    favoritos_ids = Favorito.objects.filter(
        usuario=request.user
    ).values_list(
        'pet_id',
        flat=True
    )

    perfil_usuario = PerfilUsuario.objects.filter(
        usuario=request.user
    ).first()

    for pet in pets:
        if (
            perfil_usuario
            and perfil_usuario.latitude is not None
            and perfil_usuario.longitude is not None
            and pet.latitude is not None
            and pet.longitude is not None
        ):
            pet.distancia_calculada = calcular_distancia_km(
                perfil_usuario.latitude,
                perfil_usuario.longitude,
                pet.latitude,
                pet.longitude
            )
        else:
            pet.distancia_calculada = None

    mensagens_nao_lidas = Mensagem.objects.filter(
        destinatario=request.user,
        lida=False
    ).count()

    notificacoes_nao_lidas = Notificacao.objects.filter(
        usuario=request.user,
        lida=False
    ).count()

    quantidade_notificacoes = (
        mensagens_nao_lidas
        + notificacoes_nao_lidas
    )

    return render(
        request,
        'explorar.html',
        {
            'pets': pets,
            'favoritos_ids': favoritos_ids,
            'quantidade_notificacoes': quantidade_notificacoes
        }
    )


@login_required
def perfil_pet(request, pet_id):
    pet = get_object_or_404(
        Pet,
        id=pet_id
    )

    favorito = Favorito.objects.filter(
        usuario=request.user,
        pet=pet
    ).exists()

    return render(
        request,
        'perfil_pet.html',
        {
            'pet': pet,
            'favorito': favorito
        }
    )


@login_required
def solicitar_adocao(request, pet_id):
    pet = get_object_or_404(
        Pet,
        id=pet_id
    )

    if pet.usuario_id == request.user.id:
        messages.error(
            request,
            'Você não pode solicitar a adoção do seu próprio pet.'
        )

        return redirect(
            'perfil_pet',
            pet_id=pet.id
        )

    if not pet.disponivel:
        messages.error(
            request,
            'Este pet não está mais disponível para adoção.'
        )

        return redirect(
            'perfil_pet',
            pet_id=pet.id
        )

    if request.method == 'POST':
        solicitacao_existente = SolicitacaoAdocao.objects.filter(
            pet=pet,
            usuario=request.user,
            status__in=[
                'pendente',
                'aprovada',
                'aprovado'
            ]
        ).exists()

        if solicitacao_existente:
            messages.warning(
                request,
                'Você já possui uma solicitação ativa para este pet.'
            )

            return redirect(
                'minhas_solicitacoes'
            )

        nome_adotante = request.POST.get(
            'nome_adotante',
            ''
        ).strip()

        email = request.POST.get(
            'email',
            ''
        ).strip()

        telefone = request.POST.get(
            'telefone',
            ''
        ).strip()

        local_moradia = request.POST.get(
            'local_moradia',
            ''
        ).strip()

        motivo = request.POST.get(
            'motivo',
            ''
        ).strip()

        ja_teve_animais = (
            request.POST.get(
                'ja_teve_animais'
            ) == 'sim'
        )

        possui_espaco = (
            request.POST.get(
                'possui_espaco'
            ) == 'sim'
        )

        todos_concordam = (
            request.POST.get(
                'todos_concordam'
            ) == 'sim'
        )

        consegue_cuidar = (
            request.POST.get(
                'consegue_cuidar'
            ) == 'sim'
        )

        if not nome_adotante:
            messages.error(
                request,
                'Informe seu nome.'
            )

            return render(
                request,
                'adocao.html',
                {
                    'pet': pet
                }
            )

        if not email:
            messages.error(
                request,
                'Informe seu e-mail.'
            )

            return render(
                request,
                'adocao.html',
                {
                    'pet': pet
                }
            )

        if not telefone:
            messages.error(
                request,
                'Informe seu telefone.'
            )

            return render(
                request,
                'adocao.html',
                {
                    'pet': pet
                }
            )

        if not local_moradia:
            messages.error(
                request,
                'Informe sua moradia.'
            )

            return render(
                request,
                'adocao.html',
                {
                    'pet': pet
                }
            )

        if not motivo:
            messages.error(
                request,
                'Informe o motivo da adoção.'
            )

            return render(
                request,
                'adocao.html',
                {
                    'pet': pet
                }
            )

        solicitacao = SolicitacaoAdocao.objects.create(
            pet=pet,
            usuario=request.user,
            nome_adotante=nome_adotante,
            email=email,
            telefone=telefone,
            ja_teve_animais=ja_teve_animais,
            local_moradia=local_moradia,
            possui_espaco=possui_espaco,
            todos_concordam=todos_concordam,
            consegue_cuidar=consegue_cuidar,
            motivo=motivo,
            status='pendente'
        )

        if pet.usuario_id:
            Notificacao.objects.create(
                usuario=pet.usuario,
                titulo='Nova solicitação de adoção',
                mensagem=(
                    f'{nome_adotante} solicitou a adoção '
                    f'de {pet.nome}.'
                ),
                link='/solicitacoes-recebidas/'
            )

        messages.success(
            request,
            f'Sua solicitação para adotar {pet.nome} foi enviada!'
        )

        return redirect(
            'minhas_solicitacoes'
        )

    return render(
        request,
        'adocao.html',
        {
            'pet': pet
        }
    )


@login_required
def minhas_solicitacoes(request):
    solicitacoes = (
        SolicitacaoAdocao.objects
        .filter(
            usuario_id=request.user.id
        )
        .select_related(
            'pet'
        )
        .order_by(
            '-data_solicitacao'
        )
    )

    for solicitacao in solicitacoes:

        if solicitacao.status in (
            'aprovada',
            'aprovado'
        ):
            acompanhamento, criado = (
                AcompanhamentoAdocao.objects.get_or_create(
                    solicitacao=solicitacao,
                    defaults={
                        'ativo': True
                    }
                )
            )

            if not acompanhamento.ativo:
                acompanhamento.ativo = True

                acompanhamento.save(
                    update_fields=[
                        'ativo'
                    ]
                )

            solicitacao.acompanhamento_obj = acompanhamento
            solicitacao.acompanhamento = acompanhamento

        else:
            acompanhamento = (
                AcompanhamentoAdocao.objects
                .filter(
                    solicitacao=solicitacao
                )
                .first()
            )

            solicitacao.acompanhamento_obj = acompanhamento
            solicitacao.acompanhamento = acompanhamento

    origem = request.GET.get(
        'origem',
        'explorar'
    )

    if origem == 'perfil':
        voltar_url = 'perfil_usuario'
    else:
        voltar_url = 'explorar'

    return render(
        request,
        'minhas_solicitacoes.html',
        {
            'solicitacoes': solicitacoes,
            'voltar_url': voltar_url
        }
    )


@login_required
def solicitacoes_recebidas(request):
    solicitacoes = (
        SolicitacaoAdocao.objects
        .filter(
            pet__usuario_id=request.user.id
        )
        .select_related(
            'pet',
            'usuario'
        )
        .order_by(
            '-data_solicitacao'
        )
    )

    for solicitacao in solicitacoes:
        acompanhamento = (
            AcompanhamentoAdocao.objects
            .filter(
                solicitacao=solicitacao
            )
            .first()
        )

        solicitacao.acompanhamento_obj = acompanhamento

    quantidade_pendentes = solicitacoes.filter(
        status='pendente'
    ).count()

    return render(
        request,
        'solicitacoes_recebidas.html',
        {
            'solicitacoes': solicitacoes,
            'quantidade_pendentes': quantidade_pendentes
        }
    )

@login_required
def decidir_solicitacao(request, solicitacao_id):
    solicitacao = get_object_or_404(
        SolicitacaoAdocao.objects.select_related(
            'pet',
            'usuario'
        ),
        id=solicitacao_id,
        pet__usuario=request.user
    )

    if request.method != 'POST':
        return redirect(
            'solicitacoes_recebidas'
        )

    decisao = request.POST.get(
        'decisao',
        ''
    ).strip().lower()

    if decisao in (
        'aprovar',
        'aprovado',
        'aprovada'
    ):
        solicitacao.status = 'aprovada'
        solicitacao.save(
            update_fields=[
                'status'
            ]
        )

        pet = solicitacao.pet
        pet.disponivel = False
        pet.save(
            update_fields=[
                'disponivel'
            ]
        )

        acompanhamento, criado = (
            AcompanhamentoAdocao.objects.get_or_create(
                solicitacao=solicitacao,
                defaults={
                    'ativo': True
                }
            )
        )

        if not acompanhamento.ativo:
            acompanhamento.ativo = True
            acompanhamento.save(
                update_fields=[
                    'ativo'
                ]
            )

        Notificacao.objects.create(
            usuario=solicitacao.usuario,
            titulo='Adoção aprovada',
            mensagem=(
                f'Sua solicitação para adotar '
                f'{pet.nome} foi aprovada!'
            ),
            link=(
                f'/acompanhamento/'
                f'{acompanhamento.id}/'
            )
        )

        messages.success(
            request,
            f'A adoção de {pet.nome} foi aprovada!'
        )

        return redirect(
            'acompanhamento_adocao',
            acompanhamento_id=acompanhamento.id
        )

    if decisao in (
        'recusar',
        'recusada',
        'rejeitar',
        'rejeitado'
    ):
        solicitacao.status = 'recusada'
        solicitacao.save(
            update_fields=[
                'status'
            ]
        )

        Notificacao.objects.create(
            usuario=solicitacao.usuario,
            titulo='Solicitação recusada',
            mensagem=(
                f'Sua solicitação para adotar '
                f'{solicitacao.pet.nome} foi recusada.'
            ),
            link='/minhas-solicitacoes/'
        )

        messages.success(
            request,
            'Solicitação recusada.'
        )

        return redirect(
            'solicitacoes_recebidas'
        )

    messages.error(
        request,
        'Decisão inválida.'
    )

    return redirect(
        'solicitacoes_recebidas'
    )

@login_required
def marcar_entrega(request, solicitacao_id):

    solicitacao = get_object_or_404(
        SolicitacaoAdocao.objects.select_related(
            'pet',
            'usuario'
        ),
        id=solicitacao_id,
        pet__usuario=request.user,
        status__in=[
            'aprovada',
            'aprovado'
        ]
    )

    if request.method != 'POST':
        return redirect(
            'solicitacoes_recebidas'
        )

    acompanhamento, criado = (
        AcompanhamentoAdocao.objects.get_or_create(
            solicitacao=solicitacao,
            defaults={
                'ativo': True
            }
        )
    )

    acompanhamento.ativo = True

    if not acompanhamento.entregue_em:
        acompanhamento.entregue_em = timezone.now()

    acompanhamento.save()

    Notificacao.objects.create(
        usuario=solicitacao.usuario,
        titulo='Entrega registrada',
        mensagem=(
            f'A entrega de {solicitacao.pet.nome} foi registrada. '
            f'O acompanhamento pós-adoção está ativo.'
        ),
        link=(
            f'/acompanhamento/'
            f'{acompanhamento.id}/'
        )
    )

    messages.success(
        request,
        'Entrega registrada com sucesso!'
    )

    return redirect(
        'acompanhamento_adocao',
        acompanhamento_id=acompanhamento.id
    )


@login_required
def acompanhamento_adocao(request, acompanhamento_id):
    acompanhamento = get_object_or_404(
        AcompanhamentoAdocao.objects.select_related(
            'solicitacao__pet',
            'solicitacao__usuario',
            'solicitacao__pet__usuario'
        ),
        id=acompanhamento_id
    )

    solicitacao = acompanhamento.solicitacao

    eh_adotante = (
        solicitacao.usuario_id == request.user.id
    )

    eh_responsavel = (
        solicitacao.pet.usuario_id == request.user.id
    )

    if not eh_adotante and not eh_responsavel:
        messages.error(
            request,
            'Você não tem acesso a este acompanhamento.'
        )

        return redirect(
            'explorar'
        )

    atualizacoes = (
        acompanhamento.atualizacoes
        .all()
        .order_by(
            '-data_envio'
        )
    )

    if eh_adotante:
        voltar_url = 'minhas_solicitacoes'
    else:
        voltar_url = 'solicitacoes_recebidas'

    return render(
        request,
        'acompanhamento.html',
        {
            'acompanhamento': acompanhamento,
            'atualizacoes': atualizacoes,
            'eh_adotante': eh_adotante,
            'eh_responsavel': eh_responsavel,
            'pet': solicitacao.pet,
            'solicitacao': solicitacao,
            'voltar_url': voltar_url
        }
    )

@login_required
def enviar_atualizacao(request, acompanhamento_id):
    acompanhamento = get_object_or_404(
        AcompanhamentoAdocao.objects.select_related(
            'solicitacao__pet',
            'solicitacao__usuario',
            'solicitacao__pet__usuario'
        ),
        id=acompanhamento_id,
        ativo=True
    )

    solicitacao = acompanhamento.solicitacao

    if solicitacao.usuario_id != request.user.id:
        messages.error(
            request,
            'Somente a pessoa que adotou o pet pode enviar atualizações.'
        )

        return redirect(
            'acompanhamento_adocao',
            acompanhamento_id=acompanhamento.id
        )

    if request.method != 'POST':
        return redirect(
            'acompanhamento_adocao',
            acompanhamento_id=acompanhamento.id
        )

    texto = request.POST.get(
        'texto',
        ''
    ).strip()

    foto = request.FILES.get(
        'foto'
    )

    if not texto and not foto:
        messages.error(
            request,
            'Escreva uma mensagem ou envie uma foto.'
        )

        return redirect(
            'acompanhamento_adocao',
            acompanhamento_id=acompanhamento.id
        )

    AtualizacaoAdocao.objects.create(
        acompanhamento=acompanhamento,
        texto=texto,
        foto=foto
    )

    responsavel = solicitacao.pet.usuario

    if responsavel and responsavel.id != request.user.id:
        Notificacao.objects.create(
            usuario=responsavel,
            titulo='Nova atualização pós-adoção',
            mensagem=(
                f'{solicitacao.usuario.first_name or solicitacao.usuario.username} '
                f'enviou uma atualização sobre '
                f'{solicitacao.pet.nome}.'
            ),
            link=(
                f'/acompanhamento/'
                f'{acompanhamento.id}/'
            )
        )

    messages.success(
        request,
        'Atualização enviada com sucesso!'
    )

    return redirect(
        'acompanhamento_adocao',
        acompanhamento_id=acompanhamento.id
    )

@login_required
def perfil_usuario(request):

    perfil, criado = PerfilUsuario.objects.get_or_create(
        usuario=request.user
    )

    if request.method == 'POST':

        perfil.cep = request.POST.get(
            'cep',
            ''
        ).strip()

        perfil.estado = request.POST.get(
            'estado',
            ''
        ).strip()

        perfil.cidade = request.POST.get(
            'cidade',
            ''
        ).strip()

        perfil.bairro = request.POST.get(
            'bairro',
            ''
        ).strip()

        perfil.rua = request.POST.get(
            'rua',
            ''
        ).strip()

        perfil.numero = request.POST.get(
            'numero',
            ''
        ).strip()

        perfil.complemento = request.POST.get(
            'complemento',
            ''
        ).strip()

        perfil.zona_rural = (
            request.POST.get(
                'zona_rural'
            ) == 'on'
        )

        coordenadas = obter_coordenadas(
            perfil
        )

        if coordenadas:

            perfil.latitude = coordenadas[0]
            perfil.longitude = coordenadas[1]

        else:

            perfil.latitude = None
            perfil.longitude = None

        perfil.save()

        messages.success(
            request,
            'Endereço salvo com sucesso.'
        )

        return redirect(
            'perfil_usuario'
        )

    editar_endereco = (
        request.GET.get(
            'editar'
        ) == '1'
    )

    return render(
        request,
        'perfil_usuario.html',
        {
            'usuario': request.user,
            'perfil': perfil,
            'editar_endereco': editar_endereco
        }
    )


@login_required
def favoritar_pet(request, pet_id):

    pet = get_object_or_404(
        Pet,
        id=pet_id
    )

    favorito, criado = Favorito.objects.get_or_create(
        usuario=request.user,
        pet=pet
    )

    if not criado:
        favorito.delete()

    return redirect(
        request.META.get(
            'HTTP_REFERER',
            'explorar'
        )
    )


@login_required
def favoritos(request):

    favoritos = (
        Favorito.objects
        .filter(
            usuario=request.user
        )
        .select_related(
            'pet'
        )
        .order_by(
            '-data_adicionado'
        )
    )

    return render(
        request,
        'favoritos.html',
        {
            'favoritos': favoritos
        }
    )


@login_required
def mensagens(request):

    mensagens_usuario = (
        Mensagem.objects.filter(
            remetente=request.user
        )
        |
        Mensagem.objects.filter(
            destinatario=request.user
        )
    )

    usuarios_ids = set()

    for mensagem in mensagens_usuario:

        if mensagem.remetente_id == request.user.id:

            usuarios_ids.add(
                mensagem.destinatario_id
            )

        else:

            usuarios_ids.add(
                mensagem.remetente_id
            )

    usuarios = User.objects.filter(
        id__in=usuarios_ids
    )

    return render(
        request,
        'mensagens.html',
        {
            'usuarios': usuarios
        }
    )


@login_required
def enviar_mensagem(request):

    if request.method == 'POST':

        destinatario_id = request.POST.get(
            'destinatario'
        )

        texto = request.POST.get(
            'mensagem',
            ''
        ).strip()

        destinatario = get_object_or_404(
            User,
            id=destinatario_id
        )

        if texto:

            Mensagem.objects.create(
                remetente=request.user,
                destinatario=destinatario,
                mensagem=texto
            )

            Notificacao.objects.create(
                usuario=destinatario,
                titulo='Nova mensagem',
                mensagem=(
                    f'{request.user.first_name or request.user.username} '
                    f'enviou uma mensagem.'
                ),
                link=(
                    f'/mensagens/conversa/'
                    f'{request.user.id}/'
                )
            )

        return redirect(
            'conversa',
            usuario_id=destinatario.id
        )

    usuarios = User.objects.exclude(
        id=request.user.id
    )

    return render(
        request,
        'enviar_mensagem.html',
        {
            'usuarios': usuarios
        }
    )


@login_required
def conversa(request, usuario_id):

    outro_usuario = get_object_or_404(
        User,
        id=usuario_id
    )

    mensagens_conversa = Mensagem.objects.filter(
        remetente__in=[
            request.user,
            outro_usuario
        ],
        destinatario__in=[
            request.user,
            outro_usuario
        ]
    ).order_by(
        'data_envio'
    )

    Mensagem.objects.filter(
        remetente=outro_usuario,
        destinatario=request.user,
        lida=False
    ).update(
        lida=True
    )

    return render(
        request,
        'conversa.html',
        {
            'outro_usuario': outro_usuario,
            'mensagens': mensagens_conversa
        }
    )


@login_required
def notificacoes(request):

    notificacoes_lista = (
        Notificacao.objects
        .filter(
            usuario=request.user
        )
        .order_by(
            '-data_criacao'
        )
    )

    mensagens_nao_lidas = (
        Mensagem.objects
        .filter(
            destinatario=request.user,
            lida=False
        )
        .select_related(
            'remetente'
        )
        .order_by(
            '-data_envio'
        )
    )

    quantidade = (
        Notificacao.objects.filter(
            usuario=request.user,
            lida=False
        ).count()
        +
        mensagens_nao_lidas.count()
    )

    Notificacao.objects.filter(
        usuario=request.user,
        lida=False
    ).update(
        lida=True
    )

    return render(
        request,
        'notificacoes.html',
        {
            'notificacoes_lista': notificacoes_lista,
            'mensagens_nao_lidas': mensagens_nao_lidas,
            'quantidade': quantidade
        }
    )


@login_required
def notificacoes_contador(request):

    mensagens_nao_lidas = Mensagem.objects.filter(
        destinatario=request.user,
        lida=False
    ).count()

    notificacoes_nao_lidas = Notificacao.objects.filter(
        usuario=request.user,
        lida=False
    ).count()

    return JsonResponse(
        {
            'quantidade': (
                mensagens_nao_lidas
                +
                notificacoes_nao_lidas
            )
        }
    )


@login_required
def meus_pets(request):

    pets = (
        Pet.objects
        .filter(
            usuario=request.user
        )
        .order_by(
            'nome'
        )
    )

    return render(
        request,
        'meus_pets.html',
        {
            'pets': pets
        }
    )


@login_required
def cadastrar_pet(request):

    if request.method == 'POST':

        pet = Pet(
            usuario=request.user,

            nome=request.POST.get(
                'nome',
                ''
            ).strip(),

            especie=request.POST.get(
                'especie',
                ''
            ),

            porte=request.POST.get(
                'porte',
                ''
            ),

            idade=request.POST.get(
                'idade',
                ''
            ),

            cep=request.POST.get(
                'cep',
                ''
            ).strip(),

            estado=request.POST.get(
                'estado',
                ''
            ).strip(),

            cidade=request.POST.get(
                'cidade',
                ''
            ).strip(),

            bairro=request.POST.get(
                'bairro',
                ''
            ).strip(),

            rua=request.POST.get(
                'rua',
                ''
            ).strip(),

            numero=request.POST.get(
                'numero',
                ''
            ).strip(),

            complemento=request.POST.get(
                'complemento',
                ''
            ).strip(),

            zona_rural=(
                request.POST.get(
                    'zona_rural'
                ) == 'on'
            ),

            vacinado=(
                request.POST.get(
                    'vacinado'
                ) == 'on'
            ),

            castrado=(
                request.POST.get(
                    'castrado'
                ) == 'on'
            ),

            descricao=request.POST.get(
                'descricao',
                ''
            ).strip(),

            temperamento=request.POST.get(
                'temperamento',
                ''
            ).strip(),

            disponivel=(
                request.POST.get(
                    'disponivel'
                ) == 'on'
            ),

            foto=request.FILES.get(
                'foto'
            )
        )

        if not pet.cidade or not pet.estado:

            messages.error(
                request,
                'Informe a cidade e o estado onde o pet está.'
            )

            return render(
                request,
                'cadastrar_pet.html'
            )

        coordenadas = obter_coordenadas(
            pet
        )

        if not coordenadas:

            messages.error(
                request,
                'Não foi possível encontrar a localização do pet. Verifique o endereço informado.'
            )

            return render(
                request,
                'cadastrar_pet.html'
            )

        pet.latitude = coordenadas[0]
        pet.longitude = coordenadas[1]

        pet.save()

        messages.success(
            request,
            'Pet cadastrado para adoção com sucesso!'
        )

        return redirect(
            'meus_pets'
        )

    return render(
        request,
        'cadastrar_pet.html'
    )


@login_required
def editar_pet(request, pet_id):

    pet = get_object_or_404(
        Pet,
        id=pet_id,
        usuario=request.user
    )

    if request.method == 'POST':

        pet.nome = request.POST.get(
            'nome',
            ''
        ).strip()

        pet.especie = request.POST.get(
            'especie',
            ''
        )

        pet.porte = request.POST.get(
            'porte',
            ''
        )

        pet.idade = request.POST.get(
            'idade',
            ''
        )

        pet.cep = request.POST.get(
            'cep',
            ''
        ).strip()

        pet.estado = request.POST.get(
            'estado',
            ''
        ).strip()

        pet.cidade = request.POST.get(
            'cidade',
            ''
        ).strip()

        pet.bairro = request.POST.get(
            'bairro',
            ''
        ).strip()

        pet.rua = request.POST.get(
            'rua',
            ''
        ).strip()

        pet.numero = request.POST.get(
            'numero',
            ''
        ).strip()

        pet.complemento = request.POST.get(
            'complemento',
            ''
        ).strip()

        pet.zona_rural = (
            request.POST.get(
                'zona_rural'
            ) == 'on'
        )

        pet.vacinado = (
            request.POST.get(
                'vacinado'
            ) == 'on'
        )

        pet.castrado = (
            request.POST.get(
                'castrado'
            ) == 'on'
        )

        pet.descricao = request.POST.get(
            'descricao',
            ''
        ).strip()

        pet.temperamento = request.POST.get(
            'temperamento',
            ''
        ).strip()

        pet.disponivel = (
            request.POST.get(
                'disponivel'
            ) == 'on'
        )

        if request.FILES.get('foto'):
            pet.foto = request.FILES.get(
                'foto'
            )

        if not pet.cidade or not pet.estado:

            messages.error(
                request,
                'Informe a cidade e o estado onde o pet está.'
            )

            return render(
                request,
                'editar_pet.html',
                {
                    'pet': pet
                }
            )

        coordenadas = obter_coordenadas(
            pet
        )

        if not coordenadas:

            messages.error(
                request,
                'Não foi possível encontrar a localização informada. Verifique o endereço do pet.'
            )

            return render(
                request,
                'editar_pet.html',
                {
                    'pet': pet
                }
            )

        pet.latitude = coordenadas[0]
        pet.longitude = coordenadas[1]

        pet.save()

        messages.success(
            request,
            'Informações do pet atualizadas com sucesso!'
        )

        return redirect(
            'meus_pets'
        )

    return render(
        request,
        'editar_pet.html',
        {
            'pet': pet
        }
    )


@login_required
def excluir_pet(request, pet_id):

    pet = get_object_or_404(
        Pet,
        id=pet_id,
        usuario=request.user
    )

    if request.method == 'POST':

        pet.delete()

        messages.success(
            request,
            'Pet excluído com sucesso!'
        )

        return redirect(
            'meus_pets'
        )

    return render(
        request,
        'excluir_pet.html',
        {
            'pet': pet
        }
    )