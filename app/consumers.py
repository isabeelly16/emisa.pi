from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Mensagem, Notificacao


class ChatConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        self.usuario = self.scope["user"]

        if not self.usuario.is_authenticated:
            await self.close()
            return

        outro_usuario_id = self.scope["url_route"]["kwargs"]["usuario_id"]

        self.outro_usuario = await self.buscar_usuario(outro_usuario_id)

        if not self.outro_usuario:
            await self.close()
            return

        ids = sorted([self.usuario.id, self.outro_usuario.id])

        self.room_group_name = f"chat_{ids[0]}_{ids[1]}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive_json(self, content):
        texto = content.get("mensagem", "").strip()

        if not texto:
            return

        mensagem = await self.salvar_mensagem(texto)

        await self.criar_notificacao(texto)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "mensagem": {
                    "id": mensagem.id,
                    "texto": mensagem.mensagem,
                    "remetente_id": mensagem.remetente.id,
                    "destinatario_id": mensagem.destinatario.id,
                    "data": timezone.localtime(
                        mensagem.data_envio
                    ).strftime("%d/%m/%Y %H:%M")
                }
            }
        )

    async def chat_message(self, event):
        await self.send_json(
            {
                "tipo": "mensagem",
                "mensagem": event["mensagem"]
            }
        )

    @database_sync_to_async
    def buscar_usuario(self, usuario_id):
        try:
            return User.objects.get(id=usuario_id)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def salvar_mensagem(self, texto):
        return Mensagem.objects.create(
            remetente=self.usuario,
            destinatario=self.outro_usuario,
            mensagem=texto
        )

    @database_sync_to_async
    def criar_notificacao(self, texto):
        Notificacao.objects.create(
            usuario=self.outro_usuario,
            titulo="Nova mensagem",
            mensagem=f"{self.usuario.username} enviou uma mensagem.",
            link=f"/mensagens/conversa/{self.usuario.id}/"
        )