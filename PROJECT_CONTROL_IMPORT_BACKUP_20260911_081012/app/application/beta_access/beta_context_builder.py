from app.application.beta_access.beta_user_context import (
    BetaUserContext,
)


class BetaContextBuilder:

    def build(
        self,
        user,
        telegram_user_id: int,
    ) -> BetaUserContext:


        return BetaUserContext(

            user_id=user.id,

            telegram_user_id=telegram_user_id,

            email=user.email,

            world_id=(
                user.active_world_id
                or "world-fr"
            ),

            character="Alix",

            level="B1",
        )
