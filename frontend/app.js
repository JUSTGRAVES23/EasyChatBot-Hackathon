let character = "Yeti";


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
                        item.name
                    );

                };


            container.appendChild(
                button
            );

        }
    );

};



function selectCharacter(name) {

    character = name;


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
            character;

    }

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