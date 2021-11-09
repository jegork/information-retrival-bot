import logging
import uuid
from typing import Any, Awaitable, Callable, Dict, Iterable, List, Optional, Text

import rasa.core.channels.channel
from rasa.core.channels.channel import (
    InputChannel,
    OutputChannel,
    UserMessage,
)
import rasa.shared.utils.io
from sanic import Blueprint, response, Sanic
from sanic.request import Request
from sanic.response import HTTPResponse
from socketio import AsyncServer

logger = logging.getLogger(__name__)


class SocketBlueprint(Blueprint):
    def __init__(
        self, sio: AsyncServer, socketio_path: Text, *args: Any, **kwargs: Any
    ) -> None:
        self.sio = sio
        self.socketio_path = socketio_path
        super().__init__(*args, **kwargs)

    def register(self, app: Sanic, options: Dict[Text, Any]) -> None:
        self.sio.attach(app, self.socketio_path)
        super().register(app, options)


class SocketIOOutput(OutputChannel):
    @classmethod
    def name(cls) -> Text:
        return "custom_socketio"

    def __init__(self, sio: AsyncServer, bot_message_evt: Text) -> None:
        self.sio = sio
        self.bot_message_evt = bot_message_evt

    async def _send_message(self, socket_id: Text, response: Any) -> None:
        """Sends a message to the recipient using the bot event."""

        await self.sio.emit(self.bot_message_evt, response, room=socket_id)

    async def send_text_message(
        self, recipient_id: Text, text: Text, **kwargs: Any
    ) -> None:
        """Send a message through this channel."""

        for message_part in text.strip().split("\n\n"):
            await self._send_message(recipient_id, {"text": message_part})

    async def send_image_url(
        self, recipient_id: Text, image: Text, **kwargs: Any
    ) -> None:
        """Sends an image to the output"""

        message = {"attachment": {"type": "image", "payload": {"src": image}}}
        await self._send_message(recipient_id, message)

    async def send_text_with_buttons(
        self,
        recipient_id: Text,
        text: Text,
        buttons: List[Dict[Text, Any]],
        **kwargs: Any,
    ) -> None:
        """Sends buttons to the output."""

        # split text and create a message for each text fragment
        # the `or` makes sure there is at least one message we can attach the quick
        # replies to
        message_parts = text.strip().split("\n\n") or [text]
        messages = [{"text": message, "quick_replies": []} for message in message_parts]

        # attach all buttons to the last text fragment
        for button in buttons:
            messages[-1]["quick_replies"].append(
                {
                    "content_type": "text",
                    "title": button["title"],
                    "payload": button["payload"],
                }
            )

        for message in messages:
            await self._send_message(recipient_id, message)

    async def send_elements(
        self, recipient_id: Text, elements: Iterable[Dict[Text, Any]], **kwargs: Any
    ) -> None:
        """Sends elements to the output."""

        for element in elements:
            message = {
                "attachment": {
                    "type": "template",
                    "payload": {"template_type": "generic", "elements": element},
                }
            }

            await self._send_message(recipient_id, message)

    async def send_custom_json(
        self, recipient_id: Text, json_message: Dict[Text, Any], **kwargs: Any
    ) -> None:
        """Sends custom json to the output"""

        # FIXES BUG
        await self.sio.emit(self.bot_message_evt, json_message, room=recipient_id)

    async def send_attachment(
        self, recipient_id: Text, attachment: Dict[Text, Any], **kwargs: Any
    ) -> None:
        """Sends an attachment to the user."""
        await self._send_message(recipient_id, {"attachment": attachment})


class SocketIOInput(InputChannel):
    """A socket.io input channel."""

    @classmethod
    def name(cls) -> Text:
        return "custom_socketio"

    @classmethod
    def from_credentials(cls, credentials: Optional[Dict[Text, Any]]) -> InputChannel:
        credentials = credentials or {}
        return cls(
            credentials.get("user_message_evt", "user_uttered"),
            credentials.get("bot_message_evt", "bot_uttered"),
            credentials.get("namespace"),
            credentials.get("session_persistence", False),
            credentials.get("socketio_path", "/socket.io"),
            credentials.get("jwt_key"),
            credentials.get("jwt_method", "HS256"),
        )

    def __init__(
        self,
        user_message_evt: Text = "user_uttered",
        bot_message_evt: Text = "bot_uttered",
        namespace: Optional[Text] = None,
        session_persistence: bool = False,
        socketio_path: Optional[Text] = "/socket.io",
        jwt_key: Optional[Text] = None,
        jwt_method: Optional[Text] = "HS256",
    ):
        """Creates a ``SocketIOInput`` object."""
        self.bot_message_evt = bot_message_evt
        self.session_persistence = session_persistence
        self.user_message_evt = user_message_evt
        self.namespace = namespace
        self.socketio_path = socketio_path
        self.sio = None

        self.jwt_key = jwt_key
        self.jwt_algorithm = jwt_method

    def get_output_channel(self) -> Optional["OutputChannel"]:
        """Creates socket.io output channel object."""
        if self.sio is None:
            rasa.shared.utils.io.raise_warning(
                "SocketIO output channel cannot be recreated. "
                "This is expected behavior when using multiple Sanic "
                "workers or multiple Rasa Open Source instances. "
                "Please use a different channel for external events in these "
                "scenarios."
            )
            return
        return SocketIOOutput(self.sio, self.bot_message_evt)

    def blueprint(
        self, on_new_message: Callable[[UserMessage], Awaitable[Any]]
    ) -> Blueprint:
        # Workaround so that socketio works with requests from other origins.
        # https://github.com/miguelgrinberg/python-socketio/issues/205#issuecomment-493769183
        sio = AsyncServer(async_mode="sanic", cors_allowed_origins=[])
        socketio_webhook = SocketBlueprint(
            sio, self.socketio_path, "socketio_webhook", __name__
        )

        # make sio object static to use in get_output_channel
        self.sio = sio

        @socketio_webhook.route("/", methods=["GET"])
        async def health(_: Request) -> HTTPResponse:
            return response.json({"status": "ok"})

        @sio.on("connect", namespace=self.namespace)
        async def connect(
            sid: Text, environ: Dict, auth: Optional[Dict]
        ) -> Optional[bool]:
            if self.jwt_key:
                jwt_payload = None
                if auth and auth.get("token"):
                    jwt_payload = rasa.core.channels.channel.decode_bearer_token(
                        auth.get("token"), self.jwt_key, self.jwt_algorithm,
                    )

                if jwt_payload:
                    logger.debug(f"User {sid} connected to socketIO endpoint.")
                else:
                    return False
            else:
                logger.debug(f"User {sid} connected to socketIO endpoint.")

        @sio.on("disconnect", namespace=self.namespace)
        async def disconnect(sid: Text) -> None:
            logger.debug(f"User {sid} disconnected from socketIO endpoint.")

        @sio.on("session_request", namespace=self.namespace)
        async def session_request(sid: Text, data: Optional[Dict]) -> None:
            if data is None:
                data = {}
            if "session_id" not in data or data["session_id"] is None:
                data["session_id"] = uuid.uuid4().hex
            if self.session_persistence:
                sio.enter_room(sid, data["session_id"])
            await sio.emit("session_confirm", data["session_id"], room=sid)
            logger.debug(f"User {sid} connected to socketIO endpoint.")

        @sio.on(self.user_message_evt, namespace=self.namespace)
        async def handle_message(sid: Text, data: Dict) -> None:
            output_channel = SocketIOOutput(sio, self.bot_message_evt)

            if self.session_persistence:
                if not data.get("session_id"):
                    rasa.shared.utils.io.raise_warning(
                        "A message without a valid session_id "
                        "was received. This message will be "
                        "ignored. Make sure to set a proper "
                        "session id using the "
                        "`session_request` socketIO event."
                    )
                    return
                sender_id = data["session_id"]
            else:
                sender_id = sid

            message = UserMessage(
                data["message"], output_channel, sender_id, input_channel=self.name()
            )
            await on_new_message(message)

        return socketio_webhook