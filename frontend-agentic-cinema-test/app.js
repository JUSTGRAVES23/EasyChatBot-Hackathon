/*
 * =========================================================
 * EasyChatBot Main Dashboard Application
 * =========================================================
 *
 * The Home dashboard does NOT allow the learner to select
 * an AI companion.
 *
 * The learner already has a companion.
 *
 * The flow is:
 *
 *     Authenticated Learner
 *             +
 *       Existing Companion
 *             +
 *            World
 *             +
 *         Languages
 *             â†“
 *       Dashboard Context
 *             â†“
 *       Character Theme API
 *             â†“
 *       Resolved Dashboard Theme
 *
 *
 * Character identity is therefore NOT controlled by the
 * Home page.
 *
 * The current development learner context is supplied by:
 *
 *     window.EasyChatBotLearner
 *
 * from index.html.
 *
 * Later this object will be replaced by the authenticated
 * learner/session API.
 *
 *
 * Responsibilities of this file:
 *
 * - initialise the Home dashboard;
 * - read the learner's existing companion;
 * - load companion information;
 * - request the resolved character theme;
 * - populate companion presentation;
 * - handle dashboard actions;
 * - send chat messages;
 * - preserve separation between:
 *
 *       Character identity
 *       Theme resolution
 *       Dashboard presentation
 *       Chat execution
 *
 * Character themes are NOT defined here.
 *
 * Theme resolution remains a backend responsibility.
 *
 * =========================================================
 */


/*
 * =========================================================
 * Global Dashboard State
 * =========================================================
 */


/*
 * Technical character identifier.
 *
 * Example:
 *
 *     "luminate"
 *     "yeti"
 *     "clara"
 *     "layla"
 *
 * This is NOT selected by the Home UI.
 */

let characterId = null;


/*
 * Character display name.
 *
 * Example:
 *
 *     "Luminate"
 */

let character = null;


/*
 * Resolved character profile from characters.js.
 */

let activeCharacter = null;


/*
 * Current learner context.
 */

let learnerContext = null;


/*
 * Current resolved dashboard theme.
 */

let activeDashboardTheme = null;


/*
 * =========================================================
 * Development / Session Context
 * =========================================================
 *
 * index.html currently provides:
 *
 *     window.EasyChatBotLearner
 *
 * Example:
 *
 * {
 *     characterId: "luminate",
 *     worldId: "france",
 *     primaryLanguage: "fr",
 *     secondaryLanguage: "es"
 * }
 *
 *
 * This is deliberately a context object rather than a
 * character selector.
 *
 * =========================================================
 */


function getLearnerContext() {

    const context =
        window.EasyChatBotLearner;


    if (!context) {

        console.error(
            "EasyChatBot learner context was not found."
        );

        return null;

    }


    return {

        characterId:
            context.characterId || null,

        worldId:
            context.worldId || "france",

        primaryLanguage:
            context.primaryLanguage || "fr",

        secondaryLanguage:
            context.secondaryLanguage || null

    };

}


/*
 * =========================================================
 * Character Lookup
 * =========================================================
 *
 * characters.js remains the frontend character metadata
 * source for presentation copy.
 *
 * It is NOT used to select a character.
 *
 * The learner's character ID comes from the learner context.
 *
 * =========================================================
 */


function getCharacter(
    requestedCharacterId
) {

    if (
        typeof characters ===
        "undefined"
    ) {

        console.error(
            "characters.js was not loaded."
        );

        return null;

    }


    if (
        !Array.isArray(characters)
    ) {

        console.error(
            "The characters collection is invalid."
        );

        return null;

    }


    return characters.find(
        function (item) {

            return (
                item.id ===
                requestedCharacterId
            );

        }
    ) || null;

}


/*
 * =========================================================
 * Dashboard Initialisation
 * =========================================================
 */


async function initialiseDashboard() {

    console.log(
        "EasyChatBot Home dashboard initialising..."
    );


    /*
     * -----------------------------------------------------
     * Read learner context
     * -----------------------------------------------------
     */

    learnerContext =
        getLearnerContext();


    if (!learnerContext) {

        showDashboardError(
            "Learner context is unavailable."
        );

        return;

    }


    /*
     * -----------------------------------------------------
     * Validate existing companion
     * -----------------------------------------------------
     */

    characterId =
        learnerContext.characterId;


    if (!characterId) {

        showDashboardError(
            "No companion is assigned to this learner."
        );

        return;

    }


    /*
     * -----------------------------------------------------
     * Load character metadata
     * -----------------------------------------------------
     */

    activeCharacter =
        getCharacter(
            characterId
        );


    if (!activeCharacter) {

        console.error(
            "Character metadata not found:",
            characterId
        );


        showDashboardError(
            "Your companion could not be loaded."
        );

        return;

    }


    character =
        activeCharacter.name;


    console.log(
        "Existing learner companion:",
        character
    );


    console.log(
        "Character ID:",
        characterId
    );


    /*
     * -----------------------------------------------------
     * Populate dashboard companion presentation
     * -----------------------------------------------------
     */

    updateCompanionPresentation(
        activeCharacter
    );


    /*
     * -----------------------------------------------------
     * Load character/world theme
     * -----------------------------------------------------
     */

    await loadCharacterTheme();


    /*
     * -----------------------------------------------------
     * Initialise dashboard interactions
     * -----------------------------------------------------
     */

    initialiseNavigation();

    initialiseDashboardActions();


    console.log(
        "EasyChatBot Home dashboard ready."
    );

}


/*
 * =========================================================
 * Companion Presentation
 * =========================================================
 *
 * This function updates the Home dashboard with the
 * companion that already belongs to the learner.
 *
 * It does NOT create a character-selection UI.
 *
 * =========================================================
 */


function updateCompanionPresentation(
    selected
) {

    if (!selected) {

        return;

    }


    /*
     * -----------------------------------------------------
     * Companion name
     * -----------------------------------------------------
     */

    setText(
        "companion-name-pick",
        selected.name
    );


    /*
     * -----------------------------------------------------
     * Hero title
     * -----------------------------------------------------
     */

    const heroTitle =
        document.getElementById(
            "companion-title"
        );


    if (heroTitle) {

        heroTitle.textContent =
            selected.name +
            " is ready for you!";

    }


    /*
     * -----------------------------------------------------
     * Hero message
     * -----------------------------------------------------
     */

    const heroMessage =
        document.getElementById(
            "companion-message"
        );


    if (heroMessage) {

        heroMessage.textContent =
            getCompanionMessage(
                selected
            );

    }


    /*
     * -----------------------------------------------------
     * Companion quote
     * -----------------------------------------------------
     */

    const quote =
        document.getElementById(
            "companion-quote"
        );


    if (quote) {

        quote.textContent =
            getCompanionQuote(
                selected
            );

    }


    /*
     * -----------------------------------------------------
     * Quote author
     * -----------------------------------------------------
     */

    setText(
        "companion-quote-author",
        "â€” " + selected.name
    );


    /*
     * -----------------------------------------------------
     * Companion pick message
     * -----------------------------------------------------
     */

    const pickMessage =
        document.getElementById(
            "pick-message"
        );


    if (pickMessage) {

        pickMessage.textContent =
            getCompanionPickMessage(
                selected
            );

    }


    /*
     * -----------------------------------------------------
     * Character visual
     * -----------------------------------------------------
     */

    updateCompanionVisual(
        selected
    );


    /*
     * -----------------------------------------------------
     * HTML metadata
     * -----------------------------------------------------
     */

    document.documentElement.dataset.character =
        selected.id;


}


/*
 * =========================================================
 * Companion Messaging
 * =========================================================
 */


function getCompanionMessage(
    selected
) {

    if (
        selected.recommendation &&
        selected.recommendation.tone
    ) {

        return (
            "Your " +
            selected.name +
            " adventure continues. " +
            "Let's learn together."
        );

    }


    return (
        "Your learning adventure with " +
        selected.name +
        " continues."
    );

}


/*
 * =========================================================
 * Companion Quote
 * =========================================================
 */


function getCompanionQuote(
    selected
) {

    if (
        selected.recommendation &&
        selected.recommendation.openingPhrase
    ) {

        return selected
            .recommendation
            .openingPhrase;

    }


    return (
        "Every step you take opens the door "
        + "to something new."
    );

}


/*
 * =========================================================
 * Companion Pick Message
 * =========================================================
 */


function getCompanionPickMessage(
    selected
) {

    if (
        selected.recommendation &&
        selected.recommendation.openingPhrase
    ) {

        return selected
            .recommendation
            .openingPhrase;

    }


    return (
        "I found something that might "
        + "spark your curiosity."
    );

}


/*
 * =========================================================
 * Companion Visual
 * =========================================================
 *
 * The character theme system may eventually provide an
 * avatar/image URL.
 *
 * We therefore support:
 *
 *     theme.avatar
 *     theme.character_image
 *     theme.characterImage
 *     selected.avatar
 *     selected.image
 *
 * without requiring them today.
 *
 * If none exists, the dashboard keeps a visual placeholder.
 *
 * =========================================================
 */


function updateCompanionVisual(
    selected
) {

    const visual =
        document.getElementById(
            "companion-visual"
        );

    const placeholder =
        document.getElementById(
            "companion-placeholder"
        );


    if (!visual) {

        return;

    }


    /*
     * =========================================================
     * CONFIGURABLE CHARACTER ARTWORK
     * =========================================================
     *
     * character-artwork.js owns the mapping between:
     *
     *     character ID
     *          ↓
     *     approved front card
     *
     * app.js does not contain character-specific artwork paths.
     *
     * This allows artwork to be replaced or new characters
     * to be added without changing the dashboard logic.
     */


    let artwork = null;


    if (
        typeof getCharacterArtwork ===
        "function"
    ) {

        artwork =
            getCharacterArtwork(
                selected.id
            );

    }


    /*
     * =========================================================
     * FRONT CARD RESOLUTION
     * =========================================================
     */

    const imageSource =
        artwork &&
        (
            artwork.frontCard ||
            artwork.front_card ||
            artwork.frontCardUrl ||
            artwork.front_card_url ||
            artwork.src ||
            artwork.image
        );


    /*
     * =========================================================
     * CONFIGURED FRONT CARD
     * =========================================================
     */

    if (imageSource) {

        visual.style.backgroundImage =
            "url('" +
            imageSource +
            "')";


        visual.classList.add(
            "has-character-image"
        );


        visual.classList.add(
            "has-character-front-card"
        );


        if (placeholder) {

            placeholder.style.display =
                "none";

        }


        visual.dataset.characterArtwork =
            selected.id;


        return;

    }


    /*
     * =========================================================
     * LEGACY ARTWORK FALLBACK
     * =========================================================
     *
     * Keep compatibility with existing characters.js
     * artwork fields while the new artwork registry is
     * introduced.
     */

    const legacyImageSource =
        selected.avatar ||
        selected.image ||
        selected.avatarUrl ||
        null;


    if (legacyImageSource) {

        visual.style.backgroundImage =
            "url('" +
            legacyImageSource +
            "')";


        visual.classList.add(
            "has-character-image"
        );


        visual.classList.remove(
            "has-character-front-card"
        );


        if (placeholder) {

            placeholder.style.display =
                "none";

        }


        visual.dataset.characterArtwork =
            selected.id;


        return;

    }


    /*
     * =========================================================
     * NO ARTWORK
     * =========================================================
     *
     * Never invent artwork.
     *
     * If a character does not have a configured front card,
     * retain the existing character placeholder.
     */

    visual.style.backgroundImage =
        "";


    visual.classList.remove(
        "has-character-image"
    );


    visual.classList.remove(
        "has-character-front-card"
    );


    delete visual.dataset.characterArtwork;


    if (placeholder) {

        placeholder.style.display =
            "";


        placeholder.textContent =
            getCharacterSymbol(
                selected.id
            );

    }

}

function getCharacterSymbol(
    requestedCharacterId
) {

    const symbols = {

        yeti: "â„ï¸",

        clara: "âœ¦",

        luminate: "ðŸ’¡",

        alix: "ðŸ—ºï¸",

        adri: "ðŸŒ",

        antoine: "ðŸ“–",

        grinch: "â˜ ï¸",

        julie: "ðŸŒ¿",

        lea: "âœ¨",

        mathis: "âš¡",

        naomi: "ðŸŽ¨",

        nora: "â™Ÿï¸",

        simon: "â—‡",

        zoe: "âš¡",

        jeng: "ðŸ»",

        layla: "ðŸŒ™"

    };


    return (
        symbols[
            requestedCharacterId
        ] || "âœ¨"
    );

}


/*
 * =========================================================
 * Character Theme Integration
 * =========================================================
 *
 * Backend endpoint:
 *
 *     GET /character-theme
 *
 * Inputs:
 *
 *     character_id
 *     world_id
 *     primary_language
 *     secondary_language
 *
 * The backend remains responsible for resolving the theme.
 *
 * =========================================================
 */


async function loadCharacterTheme() {

    if (!learnerContext) {

        console.error(
            "Cannot load theme without learner context."
        );

        return;

    }


    if (!characterId) {

        console.error(
            "Cannot load theme without character ID."
        );

        return;

    }


    const worldId =
        learnerContext.worldId;


    const primaryLanguage =
        learnerContext.primaryLanguage;


    const secondaryLanguage =
        learnerContext.secondaryLanguage;


    try {

        /*
         * -------------------------------------------------
         * Build query
         * -------------------------------------------------
         */

        const queryParameters = {

            character_id:
                characterId,

            world_id:
                worldId,

            primary_language:
                primaryLanguage

        };


        /*
         * Only send secondary language when
         * one actually exists.
         */

        if (secondaryLanguage) {

            queryParameters.secondary_language =
                secondaryLanguage;

        }


        const query =
            new URLSearchParams(
                queryParameters
            );


        /*
         * -------------------------------------------------
         * Request resolved theme
         * -------------------------------------------------
         */

        const response =
            await fetch(

                "http://127.0.0.1:8000/character-theme?" +
                query.toString()

            );


        if (!response.ok) {

            throw new Error(

                "Theme API request failed: " +
                response.status

            );

        }


        const themeResponse =
            await response.json();


        activeDashboardTheme =
            themeResponse;


        /*
         * -------------------------------------------------
         * Delegate presentation to theme.js
         * -------------------------------------------------
         */

        if (
            typeof applyCharacterTheme !==
            "function"
        ) {

            console.error(

                "applyCharacterTheme() was not found. " +
                "Make sure theme.js is loaded before app.js."

            );

            return;

        }


        applyCharacterTheme(
            themeResponse
        );


        /*
         * -------------------------------------------------
         * Apply optional theme-specific presentation
         * -------------------------------------------------
         */

        applyThemePresentation(
            themeResponse
        );


        console.log(
            "Character theme loaded:",
            characterId
        );


        console.log(
            "World:",
            worldId
        );


        console.log(
            "Primary language:",
            primaryLanguage
        );


        console.log(
            "Secondary language:",
            secondaryLanguage
        );


    } catch (error) {

        /*
         * Theme failure must NOT break the dashboard.
         */

        console.error(
            "Unable to load character theme:",
            error
        );


        /*
         * Keep the EasyChatBot core UI functional.
         */

    }

}


/*
 * =========================================================
 * Optional Theme Presentation
 * =========================================================
 *
 * theme.js owns CSS variable application.
 *
 * This function handles optional presentation metadata
 * without making the dashboard dependent on it.
 *
 * =========================================================
 */


function applyThemePresentation(
    themeResponse
) {

    if (!themeResponse) {

        return;

    }


    const theme =
        themeResponse.theme || {};


    const root =
        document.documentElement;


    /*
     * Character metadata
     */

    if (
        themeResponse.character_id
    ) {

        root.dataset.character =
            themeResponse.character_id;

    }


    /*
     * World metadata
     */

    if (
        themeResponse.world_id
    ) {

        root.dataset.world =
            themeResponse.world_id;

    }


    /*
     * Theme name
     */

    if (
        theme.name
    ) {

        root.dataset.theme =
            theme.name;

    }


    /*
     * Atmosphere
     */

    if (
        theme.atmosphere
    ) {

        if (
            typeof theme.atmosphere ===
            "string"
        ) {

            root.dataset.atmosphere =
                theme.atmosphere;

        }

        else if (
            typeof theme.atmosphere ===
            "object"
        ) {

            if (
                theme.atmosphere.id
            ) {

                root.dataset.atmosphere =
                    theme.atmosphere.id;

            }


            if (
                theme.atmosphere.type
            ) {

                root.dataset.atmosphereType =
                    theme.atmosphere.type;

            }

        }

    }

}


/*
 * =========================================================
 * Dashboard Navigation
 * =========================================================
 *
 * Home navigation is currently presentation-only.
 *
 * We do not introduce routing here yet.
 *
 * =========================================================
 */


function initialiseNavigation() {

    const navigationItems =
        document.querySelectorAll(
            ".dashboard-nav-item"
        );


    navigationItems.forEach(
        function (item) {

            item.addEventListener(
                "click",
                function (event) {

                    event.preventDefault();


                    navigationItems.forEach(
                        function (navItem) {

                            navItem.classList.remove(
                                "active"
                            );

                        }
                    );


                    item.classList.add(
                        "active"
                    );


                    const section =
                        item.dataset.section;


                    console.log(
                        "Dashboard navigation:",
                        section
                    );

                }
            );

        }
    );

}


/*
 * =========================================================
 * Dashboard Actions
 * =========================================================
 */


function initialiseDashboardActions() {

    /*
     * -----------------------------------------------------
     * Start Conversation
     * -----------------------------------------------------
     */

    const conversationButton =
        document.getElementById(
            "start-conversation-button"
        );


    if (conversationButton) {

        conversationButton.addEventListener(
            "click",
            function () {

                focusConversation();

            }
        );

    }


    /*
     * -----------------------------------------------------
     * Global dashboard buttons
     * -----------------------------------------------------
     */

    const primaryButtons =
        document.querySelectorAll(
            ".primary-dashboard-button"
        );


    primaryButtons.forEach(
        function (button) {

            if (
                button.id ===
                "start-conversation-button"
            ) {

                return;

            }


            button.addEventListener(
                "click",
                function () {

                    console.log(
                        "Dashboard action:",
                        button.textContent.trim()
                    );

                }
            );

        }
    );

}


/*
 * =========================================================
 * Conversation Focus
 * =========================================================
 *
 * The new Home dashboard intentionally does not embed the
 * old recommendation/chat demo.
 *
 * The real Chat experience remains the next application
 * destination.
 *
 * For the current single-page development frontend, we
 * provide a graceful fallback if a message field exists.
 *
 * =========================================================
 */


function focusConversation() {

    const message =
        document.getElementById(
            "message"
        );


    if (message) {

        message.focus();

        return;

    }


    console.log(
        "Conversation requested for:",
        character
    );


    /*
     * Future routing:
     *
     * window.location.href =
     *     "/chat";
     *
     * is deliberately NOT activated yet.
     */

}


/*
 * =========================================================
 * Chat
 * =========================================================
 *
 * Kept for compatibility with the existing backend chat
 * endpoint and future Chat UI.
 *
 * The important difference is that the character is now
 * derived from the learner's existing companion.
 *
 * =========================================================
 */


async function sendMessage() {

    const messageElement =
        document.getElementById(
            "message"
        );


    const researchElement =
        document.getElementById(
            "research"
        );


    const responseElement =
        document.getElementById(
            "response"
        );


    if (!messageElement) {

        console.error(
            "Chat message field not found."
        );

        return;

    }


    const message =
        messageElement.value.trim();


    const research =
        researchElement
            ? researchElement.checked
            : false;


    if (!message) {

        if (responseElement) {

            responseElement.textContent =
                "Please enter a message.";

        }

        return;

    }


    if (!character) {

        if (responseElement) {

            responseElement.textContent =
                "Your companion is not available.";

        }

        return;

    }


    if (responseElement) {

        responseElement.textContent =
            "Your companion is thinking...";

    }


    try {

        const response =
            await fetch(

                "http://127.0.0.1:8000/chat",

                {

                    method:
                        "POST",


                    headers: {

                        "Content-Type":
                            "application/json"

                    },


                    body:
                        JSON.stringify({

                            user_id:
                                "demo-user",


                            /*
                             * Preserve the existing backend
                             * contract.
                             *
                             * The backend currently receives
                             * the character name.
                             */

                            character:
                                character,


                            message:
                                message,


                            research:
                                research

                        })

                }

            );


        if (!response.ok) {

            throw new Error(

                "API request failed: " +
                response.status

            );

        }


        const data =
            await response.json();


        if (responseElement) {

            responseElement.textContent =
                JSON.stringify(

                    data,

                    null,

                    2

                );

        }


    } catch (error) {

        console.error(

            "EasyChatBot request failed:",

            error

        );


        if (responseElement) {

            responseElement.textContent =
                "Unable to connect to EasyChatBot. " +
                "Please make sure the backend is running.\n\n" +
                error.message;

        }

    }

}


/*
 * =========================================================
 * Dashboard Error State
 * =========================================================
 */


function showDashboardError(
    message
) {

    console.error(
        "EasyChatBot dashboard error:",
        message
    );


    const title =
        document.getElementById(
            "companion-title"
        );


    const description =
        document.getElementById(
            "companion-message"
        );


    if (title) {

        title.textContent =
            "Your companion is unavailable";

    }


    if (description) {

        description.textContent =
            message;

    }

}


/*
 * =========================================================
 * DOM Utility
 * =========================================================
 */


function setText(
    elementId,
    value
) {

    const element =
        document.getElementById(
            elementId
        );


    if (!element) {

        return;

    }


    element.textContent =
        value;

}


/*
 * =========================================================
 * Public Theme Accessor
 * =========================================================
 */


function getActiveDashboardTheme() {

    return activeDashboardTheme;

}


/*
 * =========================================================
 * Public Character Accessors
 * =========================================================
 */


function getActiveCharacterId() {

    return characterId;

}


function getActiveCharacterName() {

    return character;

}


/*
 * =========================================================
 * Application Startup
 * =========================================================
 *
 * We deliberately do NOT:
 *
 *     selectCharacter("yeti")
 *
 * We deliberately do NOT:
 *
 *     render character buttons
 *
 * We deliberately do NOT:
 *
 *     ask the learner to choose a character.
 *
 * The learner's existing companion is loaded from the
 * learner context.
 *
 * =========================================================
 */


window.addEventListener(
    "DOMContentLoaded",
    function () {

        initialiseDashboard();

    }
);
