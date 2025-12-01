import json
import re
from .bot import Bot


class Update(Bot):
    def __init__(self, update_dict: dict, token: str) -> None:
        super().__init__(token)
        self.update_dict: dict = update_dict
        self.full_string: str = json.dumps(update_dict, indent=5)
        self.update_id: str = update_dict["update_id"]
        self.callback_query = None
        self.callback_data = None
        self.__classify()

    def sendMessage(self, texto, **kwargs):
        return super().sendMessage(self.user_id, texto, **kwargs)

    def answerCallbackQuery(self):
        return super().answerCallbackQuery(self.callback_query_id)

    def sendInvoice(
        self, title, description, payload, provider_token, currency, label, price, **kwargs
    ):
        return super().sendInvoice(
            self.chat_id,
            title,
            description,
            payload,
            provider_token,
            currency,
            label,
            price,
            **kwargs
        )

    def editMessageText(self, text, message_id="callback", **kwargs):
        if message_id == "callback":
            return super().editMessageText(self.user_id, self.callback_message_id, text, **kwargs)
        else:
            return super().editMessageText(self.user_id, message_id, text, **kwargs)

    def __classify(self):
        self.callback_query = None
        self.pre_checkout_query = None
        self.message = None
        self.edited_message = None
        self.text: str = None
        self.command: str = None
        self.successful_payment = None

        if "message" in self.update_dict:
            self.message_classifier()
            print(f"Message classified: {self.update_dict.get('message')}")
        elif "callback_query" in self.update_dict:
            self.callback_query_classifier()
            print(f"Message classified: {self.update_dict.get('callback_query')}")
        elif "edited_message" in self.update_dict:
            self.edited_message_classifier()
            print(f"Message classified: {self.update_dict.get('edited_message')}")
        elif "pre_checkout_query" in self.update_dict:
            self.pre_checkout_query_classifier()
            print(f"Message classified: {self.update_dict.get('pre_checkout_query')}")
        else:
            print(f"None of the classifiers matched. Update dict: {self.update_dict}")
            raise ValueError("Invalid update object. Check classifiers")

    def message_classifier(self):
        self.message: dict = self.update_dict["message"]
        self.message_id = self.message["message_id"]
        self.chat_id = self.message["chat"]["id"]
        self.text = self.message.get("text", "")
        self.user_data = self.message.get("from", {})
        self.user_id = self.user_data.get("id") if self.user_data else None
        self.first_name = self.user_data.get("first_name") if self.user_data else None
        self.successful_payment = self.message.get("successful_payment", {})

        # Classify messages that are commands
        if self.text and self.text.startswith("/"):
            command, *args = self.text.split()
            self.is_command = True
            self.command = command[1:]
            self.command_args = args
        else:
            self.is_command = False
            self.command = None
            self.command_args = None

        # Classify messages that are successful payments
        if self.successful_payment:
            self.currency = self.successful_payment["currency"]
            self.total_amount = self.successful_payment["total_amount"]
            self.invoice_payload = self.successful_payment["invoice_payload"]
            self.telegram_payment_charge_id = self.successful_payment["telegram_payment_charge_id"]
            self.provider_payment_charge_id = self.successful_payment["provider_payment_charge_id"]

    def callback_query_classifier(self):
        self.callback_query = self.update_dict["callback_query"]
        self.callback_data = self.callback_query.get("data")
        self.user_id = self.callback_query["from"]["id"]
        self.message_id = self.callback_query["message"]["message_id"]
        self.callback_query_id = self.callback_query["id"]
        self.chat_id = self.callback_query["message"]["chat"]["id"]
        self.callback_message_id = self.callback_query["message"]["message_id"]
        self.callback_data: str = self.callback_query.get("data", "")

    def edited_message_classifier(self):
        self.edited_message = self.update_dict["edited_message"]
        self.user_id = self.edited_message["from"]["id"]
        self.first_name = self.edited_message["from"]["first_name"]
        self.text = self.update_dict["edited_message"]["text"]

    def pre_checkout_query_classifier(self):
        self.pre_checkout_query = self.update_dict["pre_checkout_query"]
        self.pre_checkout_query_id = self.pre_checkout_query["id"]
        self.from_data = self.pre_checkout_query["from"]
        self.user_id = self.from_data["id"]
        self.first_name = self.from_data["first_name"]
        self.username = self.from_data["username"]
        self.currency = self.pre_checkout_query["currency"]
        self.total_amount = self.pre_checkout_query["total_amount"]
        self.invoice_payload = self.pre_checkout_query["invoice_payload"]

    # ########################### H A N D L E R S ###############################################################

    def commandHandler(self, command: str, function, **kwargs):
        if self.command == command:
            function(self, **kwargs)
            return 1
        return 0

    def messageHandler(self, text: str = "default", function=None, regex=False, **kwargs):
        if self.text and self.command is None:
            if text == self.text or text == "default":
                function(self, **kwargs)
                return 1
            elif regex and re.findall(text, self.text):
                function(self, **kwargs)
                return 1
        return 0

    def successfulPaymentHandler(self, function=None, **kwargs):
        if self.successful_payment:
            function(self, **kwargs)
            return 1
        return 0

    def callbackQueryHandler(self, function, **kwargs):
        if self.callback_query:
            function(self, **kwargs)
            return 1
        return 0

    def preCheckoutHandler(self, function, **kwargs):
        if self.pre_checkout_query:
            function(self, **kwargs)
            return 1
        return 0
