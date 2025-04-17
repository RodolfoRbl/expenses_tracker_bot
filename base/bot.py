import json
import requests as rq


class Bot:

    def __init__(self, token):
        self.endpoint = f"https://api.telegram.org/bot{token}/"

    def get(self, method, **kwargs) -> dict:
        return rq.get(self.endpoint + method, params=kwargs).json()

    def post(self, method, **kwargs) -> dict:
        return rq.post(self.endpoint + method, params=kwargs).json()

    def sendMessage(self, chat_id, text, **kwargs):
        """
        Send a message to a desired chat. You can use different formatting options
        to style your message.
        """
        params = {"chat_id": chat_id, "text": text}
        params.update(kwargs)
        return self.post("sendMessage", **params)

    def sendPhoto(self, chat_id, photo, **kwargs):
        """
        Send a photo to a desired chat. It's necessary to have the photo_id or a file to put it as an
        argument to the function
        """
        params = {"chat_id": chat_id, "photo": photo}
        params.update(kwargs)
        return self.post("sendPhoto", **params)

    def sendPhotoFromLocal(self, chat_id, photo, **kwargs):
        datos = {"chat_id": chat_id}
        datos.update(kwargs)
        with open(photo, "rb") as imagen:
            response = rq.post(self.endpoint + "sendPhoto", data=datos, files={"photo": imagen}).json()
        return response

    def answerCallbackQuery(self, callback_query_id):
        return self.post("answerCallbackQuery", callback_query_id=str(callback_query_id))

    def answerPreCheckoutQuery(self, pre_checkout_query_id, ok=True):
        return self.post("answerPreCheckoutQuery", pre_checkout_query_id=str(pre_checkout_query_id), ok=True)

    def editMessageText(self, user_id, callback_message_id, text, **kwargs):
        params = {"chat_id": user_id, "message_id": callback_message_id, "text": text}
        params.update(kwargs)
        return self.post("editMessageText", **params)

    def getMyCommands(self):
        return self.post("getMyCommands")

    def setMyCommands(self, append=False, **kwargs):
        """
        Sets or appends commands for the bot.
        """
        new = [{"command": k, "description": v} for k, v in kwargs.items()]
        if append:
            actual_commands: list = self.getMyCommands()["result"]
            actual_commands.extend(new)
            return self.post("setMyCommands", commands=json.dumps(actual_commands))
        return self.post("setMyCommands", commands=json.dumps(new))

    def deleteCommands(self, *commands: str):
        actual_commands: list = self.getMyCommands()["result"]
        new = [i for i in actual_commands if i["command"] not in commands]
        self.post("setMyCommands", commands=json.dumps(new))

    def sendInvoice(self, chat_id, title, description, payload, provider_token, currency, label, price, **kwargs):

        params = {
            "chat_id": chat_id,
            "title": title,
            "description": description,
            "payload": payload,
            "provider_token": provider_token,
            "currency": currency,
            "prices": json.dumps([{"label": label, "amount": price}]),
        }

        return rq.post(self.endpoint + "sendInvoice", data=params).json()
