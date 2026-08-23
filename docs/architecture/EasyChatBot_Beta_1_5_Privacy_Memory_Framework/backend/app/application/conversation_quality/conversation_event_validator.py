class ConversationEventValidator:
    REQUIRED_ROLES={'user','assistant','system'}
    def validate(self,event):
        return bool(event.conversation_id and event.telegram_user_hash and event.role in self.REQUIRED_ROLES)
