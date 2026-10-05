async function searchFiles(queryOverride) {

    const input = document.getElementById("searchInput");
    const status = document.getElementById("status");
    const results = document.getElementById("results");

    const query = (queryOverride || input.value).trim();

    console.log("Search button clicked");
    console.log("Query:", query);

    if (!query) {
        status.textContent = "Enter something to search.";
        return;
    }

    status.textContent = "Searching...";
    results.innerHTML = "";

    try {

        console.log("Sending request to Flask...");

        const response = await fetch("/search", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                query: query
            })
        });

        console.log("Flask response received");

        const data = await response.json();

        console.log("Response data:", data);

        if (!data.success) {

            status.textContent =
                data.message || "Search failed.";

            return;
        }

        status.textContent =
            "Results found: " + data.count;

        if (data.results.length === 0) {

            results.innerHTML = `
                <div class="result-card">
                    No matching files found.
                </div>
            `;

            if ("speechSynthesis" in window) {
                const utterance = new SpeechSynthesisUtterance(
                    "No results found for " + query
                );
                speechSynthesis.cancel();
                speechSynthesis.speak(utterance);
            }

            return;
        }

        data.results.forEach(function(result) {

            const card = document.createElement("div");

            card.className = "result-card";

            card.textContent =
                result.data.join(" | ");

            results.appendChild(card);

        });

        if ("speechSynthesis" in window) {
            const utterance = new SpeechSynthesisUtterance(
                "I found " + data.count + " results for " + query
            );
            speechSynthesis.cancel();
            speechSynthesis.speak(utterance);
        }

    } catch (error) {

        console.error("Search error:", error);

        status.textContent =
            "Could not connect to Findly.";

    }
}

function startVoiceSearch() {

    const SpeechRecognition =
        window.SpeechRecognition || window.webkitSpeechRecognition;

    const voiceButton = document.getElementById("voiceButton");
    const input = document.getElementById("searchInput");
    const status = document.getElementById("status");

    if (!SpeechRecognition) {
        status.textContent = "Voice input is not supported in this browser.";
        return;
    }

    const recognition = new SpeechRecognition();

    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = function() {
        voiceButton.disabled = true;
        status.textContent = "Listening...";
    };

    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        input.value = transcript;
        status.textContent = "Voice query captured: " + transcript;
        searchFiles(transcript);
    };

    recognition.onerror = function(event) {
        status.textContent = "Voice input failed. Please try again.";
        voiceButton.disabled = false;
    };

    recognition.onend = function() {
        voiceButton.disabled = false;
    };

    recognition.start();
}


document
    .getElementById("searchInput")
    .addEventListener("keydown", function(event) {

        if (event.key === "Enter") {
            searchFiles();
        }

    });