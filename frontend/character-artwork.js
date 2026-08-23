/*
 * =========================================================
 * EasyChatBot Character Artwork Registry
 * =========================================================
 *
 * This file contains ONLY the mapping between a character
 * and its approved front-card artwork.
 *
 * It does NOT:
 *
 * - define character personality;
 * - define character behaviour;
 * - select the learner's companion;
 * - resolve themes;
 * - store learner state.
 *
 * Character identity:
 *
 *     characters.js
 *
 * Artwork:
 *
 *     character-artwork.js
 *
 * Theme:
 *
 *     backend Character Theme API
 *
 * This separation makes it easy to:
 *
 * - replace a front card;
 * - add a new character;
 * - temporarily disable artwork;
 * - change an asset path;
 *
 * without changing the dashboard rendering logic.
 */


/*
 * =========================================================
 * Artwork Configuration
 * =========================================================
 */

const characterArtwork = {

    yeti: {
        frontCard:
            "assets/character-front-cards/yeti.png",

        artworkAvailable:
            true,

        artworkStatus:
            "approved",

        selectable:
            true
    },


    clara: {
        frontCard:
            "assets/character-front-cards/clara.png",

        artworkAvailable:
            true,

        artworkStatus:
            "approved",

        selectable:
            true
    },


    luminate: {
        frontCard:
            "assets/character-front-cards/luminate.png",

        artworkAvailable:
            true,

        artworkStatus:
            "approved",

        selectable:
            true
    },


    alix: {
        frontCard:
            "assets/character-front-cards/alix.png",

        artworkAvailable:
            true,

        artworkStatus:
            "approved",

        selectable:
            true
    },


    antoine: {
        frontCard:
            "assets/character-front-cards/antoine.png",

        artworkAvailable:
            true,

        artworkStatus:
            "approved",

        selectable:
            true
    },


    julie: {
        frontCard:
            "assets/character-front-cards/julie.png",

        artworkAvailable:
            true,

        artworkStatus:
            "approved",

        selectable:
            true
    },


    lea: {
        frontCard:
            "assets/character-front-cards/lea.png",

        artworkAvailable:
            true,

        artworkStatus:
            "approved",

        selectable:
            true
    },


    naomi: {
        frontCard:
            "assets/character-front-cards/naomi.png",

        artworkAvailable:
            true,

        artworkStatus:
            "approved",

        selectable:
            true
    },


    nora: {
        frontCard:
            "assets/character-front-cards/nora.png",

        artworkAvailable:
            true,

        artworkStatus:
            "approved",

        selectable:
            true
    },


    simon: {
        frontCard:
            "assets/character-front-cards/simon.png",

        artworkAvailable:
            true,

        artworkStatus:
            "approved",

        selectable:
            true
    },


    zoe: {
        frontCard:
            "assets/character-front-cards/zoe.png",

        artworkAvailable:
            true,

        artworkStatus:
            "approved",

        selectable:
            true
    },


    jeng: {
        frontCard:
            "assets/character-front-cards/jeng.png",

        artworkAvailable:
            true,

        artworkStatus:
            "approved",

        selectable:
            true
    },


    layla: {
        frontCard:
            "assets/character-front-cards/layla.png",

        artworkAvailable:
            true,

        artworkStatus:
            "approved",

        selectable:
            true
    }

};


/*
 * =========================================================
 * Character Artwork Lookup
 * =========================================================
 */

function getCharacterArtwork(
    characterId
) {

    if (
        !characterId
    ) {

        return null;

    }


    return (
        characterArtwork[
            characterId
        ] || null
    );

}


/*
 * =========================================================
 * Artwork Availability
 * =========================================================
 */

function hasCharacterArtwork(
    characterId
) {

    const artwork =
        getCharacterArtwork(
            characterId
        );


    if (!artwork) {

        return false;

    }


    return (
        artwork.artworkAvailable === true
    );

}


/*
 * =========================================================
 * Selection Availability
 * =========================================================
 *
 * A character may exist in the catalogue but remain
 * unavailable for learner selection until its EasyChatBot
 * artwork has been approved.
 */

function isCharacterSelectable(
    characterId
) {

    const artwork =
        getCharacterArtwork(
            characterId
        );


    if (!artwork) {

        return false;

    }


    return (
        artwork.artworkAvailable === true &&
        artwork.artworkStatus === "approved" &&
        artwork.selectable === true
    );

}


/*
 * =========================================================
 * Front Card URL
 * =========================================================
 */

function getCharacterFrontCard(
    characterId
) {

    const artwork =
        getCharacterArtwork(
            characterId
        );


    if (
        !artwork ||
        !artwork.frontCard
    ) {

        return null;

    }


    return artwork.frontCard;

}
