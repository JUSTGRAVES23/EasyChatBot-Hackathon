let character = "Yeti";


const recommendation = {

    productName: "iPhone 17",

    vendor: "eBay",

    dealUrl:
        "https://example.com/affiliate/iphone17",

    informationUrl:
        "https://example.com/iphone17"

};


window.onload = function () {

    console.log(
        "EasyChatBot frontend loaded"
    );


    const container =
        document.getElementById(
            "characters"
        );


    if (!container) {

        console.error(
            "Character container not found."
        );

        return;

    }


    if (
        typeof characters ===
        "undefined"
    ) {

        console.error(
            "characters.js was not loaded."
        );

        return;

    }


    characters.forEach(
        function (item) {

            const button =
                document.createElement(
                    "button"
                );


            button.innerText =
                item.name;


            button.onclick =
                function () {

                    selectCharacter(
                        item.id
                    );

                };


            container.appendChild(
                button
            );

        }
    );


    selectCharacter(
        "yeti"
    );

};


function getCharacter(
    characterId
) {

    return characters.find(
        function (item) {

            return (
                item.id ===
                characterId
            );

        }
    );

}


function selectCharacter(
    characterId
) {

    const selected =
        getCharacter(
            characterId
        );


    if (!selected) {

        console.error(
            "Character not found:",
            characterId
        );

        return;

    }


    character =
        selected.name;


    console.log(
        "Selected character:",
        character
    );


    const selectedCharacter =
        document.getElementById(
            "selected-character"
        );


    if (selectedCharacter) {

        selectedCharacter.textContent =
            "Selected companion: " +
            selected.name;

    }


    updateRecommendationCharacter(
        selected
    );

}


function updateRecommendationCharacter(
    selected
) {

    const recommendationData =
        selected.recommendation;


    const openingPhrase =
        recommendationData
            ? recommendationData.openingPhrase
            : "I found something for you.";


    const notificationTitle =
        document.getElementById(
            "notification-title"
        );


    const notificationMessage =
        document.getElementById(
            "notification-message"
        );


    const recommendationOpening =
        document.getElementById(
            "recommendation-opening"
        );


    const characterBadge =
        document.querySelector(
            ".character-badge"
        );


    if (notificationTitle) {

        notificationTitle.textContent =
            selected.name +
            " found something for you";

    }


    if (notificationMessage) {

        notificationMessage.textContent =
            openingPhrase;

    }


    if (recommendationOpening) {

        recommendationOpening.textContent =
            openingPhrase;

    }


    if (characterBadge) {

        characterBadge.textContent =
            selected.name;

    }

}


function openRecommendation() {

    const section =
        document.getElementById(
            "recommendation-section"
        );


    if (section) {

        section.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

    }

}


function getDeal() {

    window.open(
        recommendation.dealUrl,
        "_blank",
        "noopener,noreferrer"
    );

}


function moreInformation() {

    window.open(
        recommendation.informationUrl,
        "_blank",
        "noopener,noreferrer"
    );

}


async function sendMessage() {

    const message =
        document.getElementById(
            "message"
        ).value.trim();


    const research =
        document.getElementById(
            "research"
        ).checked;


    const responseElement =
        document.getElementById(
            "response"
        );


    if (!message) {

        responseElement.textContent =
            "Please enter a message.";

        return;

    }


    responseElement.textContent =
        "Your companion is thinking...";


    try {

        const response =
            await fetch(
                "http://127.0.0.1:8000/chat",
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        user_id:
                            "demo-user",

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


        responseElement.textContent =
            JSON.stringify(
                data,
                null,
                2
            );


    } catch (error) {

        console.error(
            "EasyChatBot request failed:",
            error
        );


        responseElement.textContent =
            "Unable to connect to EasyChatBot. " +
            "Please make sure the backend is running.\n\n" +
            error.message;

    }

}